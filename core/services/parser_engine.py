"""
Универсальный парсер сайтов поставщиков.

Использует requests + BeautifulSoup(html.parser).
Без lxml, без Selenium, без Playwright.
Ошибки одного источника не останавливают весь процесс.
"""
import re
import time
import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

_PRICE_RE = re.compile(
    r'(\d[\d\s ]*(?:[.,]\d{1,2})?)\s*(?:руб|₽|rub)',
    re.IGNORECASE,
)
_PRICE_PLAIN_RE = re.compile(r'(\d[\d\s ]{2,}(?:[.,]\d{1,2})?)')
_DELIVERY_RE = re.compile(r'(\d+)\s*(?:дн|день|дней|д\.)', re.IGNORECASE)
_ARTICLE_RE = re.compile(r'(?:арт(?:икул)?\.?\s*|код\s*|article\s*)[:\s]?([A-Za-zА-Яа-я0-9\-/]+)', re.IGNORECASE)


def fetch_page(url: str, delay_seconds: int = 3) -> tuple[str | None, int | None]:
    """Загрузить страницу. Возвращает (html, status_code) или (None, None) при ошибке."""
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text, resp.status_code
    except requests.exceptions.RequestException as exc:
        logger.warning("fetch_page failed for %s: %s", url, exc)
        return None, None


def normalize_price(text: str) -> Decimal | None:
    """Нормализовать строку цены в Decimal. None если не найдено."""
    if not text:
        return None
    text = str(text).strip()

    match = _PRICE_RE.search(text)
    if not match:
        match = _PRICE_PLAIN_RE.search(text)
    if not match:
        return None

    raw = match.group(1)
    raw = re.sub(r'[\s ]', '', raw)
    raw = raw.replace(',', '.')
    try:
        value = Decimal(raw)
        if value <= 0 or value > 100_000_000:
            return None
        return value
    except InvalidOperation:
        return None


def normalize_availability(text: str) -> str:
    """Определить наличие товара из текста."""
    if not text:
        return ''
    t = text.lower()
    if any(w in t for w in ('в наличии', 'на складе', 'есть', 'в наличие')):
        return 'В наличии'
    if any(w in t for w in ('под заказ', 'на заказ', 'под-заказ')):
        return 'Под заказ'
    if any(w in t for w in ('нет в наличии', 'нет на складе', 'отсутствует', 'нет')):
        return 'Нет в наличии'
    return text[:50]


def estimate_delivery_days(text: str) -> int | None:
    """Оценить срок поставки в днях из текста."""
    if not text:
        return None
    match = _DELIVERY_RE.search(text)
    if match:
        try:
            days = int(match.group(1))
            if 1 <= days <= 365:
                return days
        except ValueError:
            pass
    t = text.lower()
    if 'под заказ' in t or 'на заказ' in t:
        return 14
    if 'в наличии' in t or 'на складе' in t:
        return 3
    return None


def extract_article(text: str) -> str:
    """Извлечь артикул/код из текста."""
    match = _ARTICLE_RE.search(text)
    return match.group(1).strip() if match else ''


def extract_characteristics(soup: BeautifulSoup) -> dict:
    """Извлечь характеристики из таблиц и dl-списков страницы."""
    chars = {}

    # Таблицы характеристик
    for table in soup.find_all('table')[:3]:
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                if key and val and len(key) < 100:
                    chars[key] = val

    # Характеристики могут быть оформлены списками dl/dt/dd вместо таблицы.
    for dl in soup.find_all('dl')[:3]:
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        for dt, dd in zip(dts, dds):
            key = dt.get_text(strip=True)
            val = dd.get_text(strip=True)
            if key and val:
                chars[key] = val

    return dict(list(chars.items())[:30])


def _find_price(soup: BeautifulSoup, page_text: str) -> Decimal | None:
    """Найти цену на странице через несколько стратегий."""
    # Сначала проверяем микроразметку товара.
    el = soup.find(attrs={'itemprop': 'price'})
    if el:
        val = el.get('content') or el.get_text(strip=True)
        price = normalize_price(val)
        if price:
            return price

    # Затем ищем цену по распространённым CSS-классам интернет-магазинов.
    for selector in ('.price', '.product-price', '.product__price',
                     '.price__value', '.cost', '[class*="price"]'):
        for el in soup.select(selector)[:5]:
            price = normalize_price(el.get_text(strip=True))
            if price:
                return price

    # Последний вариант — поиск цены регулярным выражением по началу текста страницы.
    return normalize_price(page_text[:5000])


def _find_name(soup: BeautifulSoup) -> str:
    """Найти название товара на странице."""
    # Приоритет отдаём микроразметке товара.
    el = soup.find(attrs={'itemprop': 'name'})
    if el:
        return el.get_text(strip=True)[:400]

    # Затем используем основной заголовок страницы.
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)[:400]

    # Если заголовка нет, проверяем типовые CSS-классы карточки товара.
    for selector in ('.product-title', '.product__title', '.product-name',
                     '[class*="product-title"]', '[class*="product_title"]'):
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)[:400]

    # В крайнем случае берём содержимое тега title.
    title = soup.find('title')
    if title:
        return title.get_text(strip=True)[:200]

    return ''


def parse_product_page(url: str, category_hint: str = None, delay_seconds: int = 3) -> dict | None:
    """
    Спарсить карточку товара.
    Возвращает dict с данными или None при ошибке.
    Если цена не найдена — всё равно возвращает данные.
    """
    html, status_code = fetch_page(url, delay_seconds)
    if not html:
        return None

    try:
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(' ', strip=True)

        name = _find_name(soup)
        price = _find_price(soup, page_text)
        article = extract_article(page_text[:2000])
        characteristics = extract_characteristics(soup)

        # Наличие товара часто хранится в отдельных блоках склада или доставки.
        avail_raw = ''
        for selector in ('.availability', '.stock', '[class*="avail"]', '[class*="stock"]'):
            el = soup.select_one(selector)
            if el:
                avail_raw = el.get_text(strip=True)
                break
        availability = normalize_availability(avail_raw or page_text[:1000])

        # Срок поставки извлекается отдельно, а при отсутствии блока оценивается по статусу наличия.
        delivery_days = None
        for selector in ('.delivery', '.delivery-time', '[class*="delivery"]'):
            el = soup.select_one(selector)
            if el:
                delivery_days = estimate_delivery_days(el.get_text(strip=True))
                break
        if delivery_days is None:
            delivery_days = estimate_delivery_days(availability)

        return {
            'name': name,
            'price': price,
            'article': article,
            'availability': availability,
            'delivery_days': delivery_days,
            'characteristics': characteristics,
            'url': url,
            'status_code': status_code,
        }
    except Exception as exc:
        logger.warning("parse_product_page error for %s: %s", url, exc)
        return None


def parse_listing_page(url: str, category_hint: str = None, max_items: int = 10, delay_seconds: int = 3) -> list[dict]:
    """
    Спарсить листинг товаров.
    Возвращает список dict с базовыми данными о товарах.
    """
    html, status_code = fetch_page(url, delay_seconds)
    if not html:
        return []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        results = []

        # Ищем карточки товаров по распространённым CSS-паттернам каталогов.
        product_selectors = [
            '.product-card', '.product-item', '.product',
            '[class*="product-card"]', '[class*="product_card"]',
            '[class*="catalog-item"]', '[class*="catalog_item"]',
            '.item', 'article',
        ]

        cards = []
        for selector in product_selectors:
            found = soup.select(selector)
            if len(found) >= 2:
                cards = found[:max_items]
                break

        for card in cards:
            # Название товара берём из микроразметки, заголовка или типовых классов.
            name_el = (
                card.find(attrs={'itemprop': 'name'}) or
                card.find('h2') or card.find('h3') or card.find('h4') or
                card.select_one('.name, .title, [class*="name"], [class*="title"]')
            )
            name = name_el.get_text(strip=True)[:400] if name_el else ''

            # Цену извлекаем той же логикой, что и на отдельной карточке товара.
            price = _find_price(card, card.get_text(' ', strip=True))

            # Относительные ссылки приводим к полному URL текущего сайта.
            link_el = card.find('a', href=True)
            product_url = ''
            if link_el:
                href = link_el['href']
                if href.startswith('http'):
                    product_url = href
                elif href.startswith('/'):
                    product_url = base_url + href

            if name:
                results.append({
                    'name': name,
                    'price': price,
                    'article': '',
                    'availability': '',
                    'delivery_days': None,
                    'characteristics': {},
                    'url': product_url or url,
                    'status_code': status_code,
                })

        # Если карточки не найдены, сохраняем хотя бы данные самой страницы.
        if not results:
            page_text = soup.get_text(' ', strip=True)
            price = _find_price(soup, page_text)
            name = _find_name(soup)
            if name:
                results.append({
                    'name': name,
                    'price': price,
                    'article': extract_article(page_text[:2000]),
                    'availability': normalize_availability(page_text[:1000]),
                    'delivery_days': estimate_delivery_days(page_text[:2000]),
                    'characteristics': extract_characteristics(soup),
                    'url': url,
                    'status_code': status_code,
                })

        return results[:max_items]

    except Exception as exc:
        logger.warning("parse_listing_page error for %s: %s", url, exc)
        return []


def parse_source(source) -> tuple[list[dict], str | None]:
    """
    Спарсить один ParsingSource.
    Возвращает (список_продуктов, ошибка_или_None).
    """
    try:
        if source.source_type == 'product':
            result = parse_product_page(
                source.url,
                category_hint=source.category_hint,
                delay_seconds=source.request_delay_seconds,
            )
            if result is None:
                return [], f"Не удалось получить страницу: {source.url}"
            return [result], None
        else:
            results = parse_listing_page(
                source.url,
                category_hint=source.category_hint,
                max_items=source.max_items_per_run,
                delay_seconds=source.request_delay_seconds,
            )
            return results, None
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("parse_source error for source %s: %s", source.id, error_msg)
        return [], error_msg
