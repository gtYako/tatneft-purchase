"""
Модуль безопасного поиска новых поставщиков.

Не сканирует интернет бесконтрольно.
Для автоматического поиска требует официальный API (SEARCH_API_KEY / SERPAPI_API_KEY).
Без API — принимает данные через CSV-импорт.
Все найденные сайты сохраняются как SupplierCandidate (статус new).
Финальное включение в парсинг делает администратор вручную.
"""
import os
import re
import time
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

CATEGORY_KEYWORDS = {
    'КИПиА': ['датчик', 'манометр', 'расходомер', 'термометр', 'уровнемер', 'преобразователь', 'кип'],
    'Запорная арматура': ['задвижка', 'клапан', 'кран шаровой', 'вентиль', 'затвор', 'арматура'],
    'Насосное оборудование': ['насос', 'насосный агрегат', 'помпа', 'эцн', 'уэцн'],
    'Кабельная продукция': ['кабель', 'провод', 'шнур', 'кабельный', 'ввгнг', 'кпвэ'],
    'Трубы': ['труба', 'нкт', 'обсадная', 'трубопровод', 'гост 8732'],
    'Химические реагенты': ['реагент', 'деэмульгатор', 'ингибитор', 'химия нефтяная'],
    'Электродвигатели': ['электродвигатель', 'двигатель асинхронный', 'взрывозащищённый', 'аир'],
    'Подшипники': ['подшипник', 'skf', 'fag', 'nsk'],
}

SUPPLIER_KEYWORDS = [
    'каталог', 'продукция', 'товары', 'shop', 'catalog', 'products',
    'кипиа', 'насос', 'кабель', 'арматура', 'реагент', 'труба',
    'нефтегаз', 'промышленное оборудование', 'оборудование для нефти',
    'поставка', 'поставщик',
]

CONTACT_KEYWORDS = ['контакты', 'contact', 'телефон', 'email', '@', 'адрес']
REQUISITE_KEYWORDS = ['инн', 'кпп', 'огрн', 'реквизиты', 'огрнип']
DELIVERY_KEYWORDS = ['доставка', 'delivery', 'по всей России', 'по рф', 'самовывоз']
PRICE_KEYWORDS = ['цена', 'price', 'стоимость', 'руб', '₽', 'прайс']


def search_supplier_candidates(query: str) -> list[dict]:
    """
    Поиск кандидатов поставщиков через официальный API.

    Если API-ключ не настроен — возвращает пустой список и пишет в лог.
    НЕ парсит Google/Yandex напрямую.
    """
    serpapi_key = os.environ.get('SERPAPI_API_KEY') or os.environ.get('SEARCH_API_KEY')

    if not serpapi_key:
        logger.info(
            "Поиск поставщиков: SERPAPI_API_KEY не задан. "
            "Используйте CSV-импорт (import_supplier_candidates) "
            "или добавьте ключ SerpAPI/аналогичного сервиса."
        )
        return []

    try:
        params = {
            'q': query,
            'api_key': serpapi_key,
            'engine': 'google',
            'gl': 'ru',
            'hl': 'ru',
            'num': 10,
        }
        resp = requests.get('https://serpapi.com/search', params=params, timeout=15)
        if resp.status_code != 200:
            logger.warning("SerpAPI вернул статус %s", resp.status_code)
            return []

        data = resp.json()
        results = []
        for item in data.get('organic_results', []):
            url = item.get('link', '')
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            if url and title:
                results.append({
                    'name': title,
                    'website': _normalize_website_url(url),
                    'reason': snippet,
                })
        return results
    except Exception as exc:
        logger.warning("search_supplier_candidates error: %s", exc)
        return []


def _normalize_website_url(url: str) -> str:
    """Привести URL к виду https://domain.com/"""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        return url


def analyze_supplier_site(url: str) -> dict:
    """
    Анализ сайта поставщика по открытым признакам.

    Загружает только главную страницу, никакого глубокого краулинга.
    """
    result = {
        'site_status_code': None,
        'site_response_time_ms': None,
        'has_prices': False,
        'has_contacts': False,
        'has_requisites': False,
        'has_delivery_rf': False,
        'has_product_cards': False,
        'detected_categories': [],
        'detected_catalog_urls': [],
        'detected_product_urls': [],
        'detected_contacts': {},
        'supplier_score': 0.0,
        'reason': '',
        'risk_flags': [],
        'https': False,
    }

    start_ms = int(time.monotonic() * 1000)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        elapsed_ms = int(time.monotonic() * 1000) - start_ms
        result['site_status_code'] = resp.status_code
        result['site_response_time_ms'] = elapsed_ms
        result['https'] = resp.url.startswith('https://')

        if resp.status_code != 200:
            result['risk_flags'].append(f"HTTP {resp.status_code}")
            result['reason'] = f"Сайт вернул статус {resp.status_code}"
            result['supplier_score'] = calculate_supplier_score(result)
            return result

        resp.encoding = resp.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        page_text = soup.get_text(' ', strip=True).lower()
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        # Цены
        result['has_prices'] = any(kw in page_text for kw in PRICE_KEYWORDS)

        # Контакты
        result['has_contacts'] = any(kw in page_text for kw in CONTACT_KEYWORDS)
        phones = re.findall(r'[\+7|8][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', page_text)
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', resp.text)
        if phones:
            result['detected_contacts']['phones'] = list(set(phones[:3]))
        if emails:
            result['detected_contacts']['emails'] = list(set(emails[:3]))

        # Реквизиты
        result['has_requisites'] = any(kw in page_text for kw in REQUISITE_KEYWORDS)

        # Доставка по РФ
        result['has_delivery_rf'] = any(kw in page_text for kw in DELIVERY_KEYWORDS)

        # Карточки товаров
        product_card_selectors = [
            '.product-card', '.product-item', '[class*="product-card"]',
            '[class*="catalog-item"]', '.item-card',
        ]
        for sel in product_card_selectors:
            if len(soup.select(sel)) >= 2:
                result['has_product_cards'] = True
                break

        # Категории
        categories = detect_supplier_categories(page_text)
        result['detected_categories'] = categories

        # Ссылки на каталог
        catalog_links = []
        product_links = []
        catalog_patterns = ['/catalog', '/katalog', '/products', '/shop', '/товары', '/продукция']
        for a in soup.find_all('a', href=True)[:100]:
            href = a.get('href', '')
            text = a.get_text(strip=True).lower()
            full_url = href if href.startswith('http') else (base_url + href if href.startswith('/') else '')
            if not full_url:
                continue
            is_catalog = any(p in href for p in catalog_patterns) or any(
                t in text for t in ['каталог', 'продукция', 'товары', 'catalog', 'products']
            )
            if is_catalog and full_url not in catalog_links:
                catalog_links.append(full_url)
            elif len(href.split('/')) >= 4 and full_url not in product_links:
                product_links.append(full_url)

        result['detected_catalog_urls'] = catalog_links[:5]
        result['detected_product_urls'] = product_links[:5]

        # Риски
        if not result['has_contacts']:
            result['risk_flags'].append('Нет контактной информации')
        if not result['has_prices'] and not result['has_product_cards']:
            result['risk_flags'].append('Нет признаков товарного каталога')
        if not result['has_requisites']:
            result['risk_flags'].append('Реквизиты не найдены')

        # Причина / резюме
        signs = []
        if result['has_product_cards']:
            signs.append('есть карточки товаров')
        if result['has_prices']:
            signs.append('есть цены')
        if result['has_contacts']:
            signs.append('есть контакты')
        if categories:
            signs.append(f"категории: {', '.join(categories)}")
        result['reason'] = 'Признаки: ' + '; '.join(signs) if signs else 'Признаки поставщика не обнаружены'

    except requests.exceptions.ConnectionError:
        result['risk_flags'].append('Сайт недоступен')
        result['reason'] = 'Сайт не отвечает на запрос'
    except requests.exceptions.Timeout:
        result['risk_flags'].append('Таймаут')
        result['reason'] = 'Превышен таймаут соединения'
    except Exception as exc:
        result['risk_flags'].append(f"Ошибка: {type(exc).__name__}")
        result['reason'] = str(exc)[:200]

    result['supplier_score'] = calculate_supplier_score(result)
    return result


def calculate_supplier_score(analysis: dict) -> float:
    score = 0.0

    if analysis.get('detected_catalog_urls'):
        score += 20
    if analysis.get('has_product_cards'):
        score += 20
    if analysis.get('has_prices'):
        score += 15
    if analysis.get('has_contacts'):
        score += 10
    if analysis.get('has_requisites'):
        score += 10
    if analysis.get('has_delivery_rf'):
        score += 10
    if analysis.get('detected_categories'):
        score += 10
    if analysis.get('https'):
        score += 5

    risk_flags = analysis.get('risk_flags', [])
    if any('недоступен' in f or 'Таймаут' in f or 'HTTP' in f for f in risk_flags):
        score -= 20
    if 'Нет контактной информации' in risk_flags:
        score -= 15
    if 'Нет признаков товарного каталога' in risk_flags:
        score -= 15
    if not analysis.get('detected_catalog_urls'):
        score -= 10

    return max(0.0, min(100.0, score))


def detect_supplier_categories(text: str) -> list[str]:
    """Определить категории поставщика по тексту страницы."""
    found = []
    text = text.lower().replace('ё', 'е')
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(category)
    return found
