"""
ИИ-сопоставление найденных товаров с каталогом МТР.

Используется классификация по категориям, нечёткое сопоставление
через RapidFuzz и формирование объяснения решения.
"""
import re
from rapidfuzz import fuzz


STOP_WORDS = {
    'и', 'или', 'для', 'на', 'от', 'по', 'из', 'с', 'в', 'к', 'за',
    'под', 'над', 'при', 'без', 'до', 'не', 'ни', 'то', 'это', 'также',
    'тип', 'арт', 'артикул', 'код', 'модель', 'серия', 'шт', 'компл',
    'упак', 'м', 'мм', 'см', 'кг', 'г', 'л', 'мл', 'шт.',
}

TECH_NORMALIZATION = [
    (r'\bду\b', 'dn'),
    (r'\bdn\b', 'dn'),
    (r'\bру\b', 'pn'),
    (r'\bpn\b', 'pn'),
    (r'\bмпа\b', 'mpa'),
    (r'\bквт\b', 'kw'),
    (r'\bкв\b', 'kv'),
    (r'\bнкт\b', 'nkt'),
    (r'\bэцн\b', 'ecn'),
    (r'\bнкт\b', 'nkt'),
]

CATEGORY_KEYWORDS = {
    'КИПиА': [
        'датчик', 'давление', 'температура', 'расход', 'уровень',
        'манометр', 'термометр', 'расходомер', 'уровнемер',
        'преобразователь', 'реле', 'сигнализатор', 'кип', 'контрольно',
        'измерительный', 'автоматизация', 'регулятор', 'клапан',
        'pozyx', 'овен', 'метран', 'emerson', 'yokogawa',
    ],
    'Запорная арматура': [
        'задвижка', 'клапан', 'кран', 'вентиль', 'затвор',
        'шаровой', 'шаровая', 'обратный', 'игольчатый',
        '30с41нж', '30с64нж', 'фланцевый', 'муфтовый', 'арматура',
        'нж', 'чугун', 'латунь',
    ],
    'Насосное оборудование': [
        'насос', 'насосный', 'агрегат', 'помпа', 'нагнетатель',
        'центробежный', 'погружной', 'скважинный', 'пластовый',
        'эцн', 'уэцн', 'ecn',
    ],
    'Кабельная продукция': [
        'кабель', 'провод', 'шнур', 'кабельный', 'вввгнг',
        'ввгнг', 'пвс', 'кг', 'кпвэ', 'кнр', 'мкэш',
        'бронированный', 'силовой', 'контрольный', 'сечение',
    ],
    'Химические реагенты': [
        'реагент', 'деэмульгатор', 'ингибитор', 'диспергатор',
        'химия', 'присадка', 'растворитель', 'кислота', 'щёлочь',
        'метанол', 'гликоль', 'пав',
    ],
    'Электродвигатели': [
        'электродвигатель', 'двигатель', 'асинхронный', 'взрывозащищённый',
        'аир', '1500 об', '3000 об', 'квт', 'электромотор', '4аm',
        'вэ', 'exd', 'exn',
    ],
    'Подшипники': [
        'подшипник', 'шарикоподшипник', 'роликоподшипник',
        'радиально', 'упорный', 'skf', 'fag', 'nsk', 'gost',
    ],
    'Трубы': [
        'труба', 'трубопровод', 'нкт', 'обсадная', 'насосно',
        'компрессорный', 'стальная', 'полиэтиленовая', 'пэ',
        'диаметр', 'толщина стенки', 'гост 8732', 'гост 632',
    ],
}


def normalize_text(text: str) -> str:
    if not text:
        return ''
    text = text.lower()
    text = text.replace('ё', 'е')
    text = re.sub(r'[^\w\s\-/]', ' ', text)
    for pattern, replacement in TECH_NORMALIZATION:
        text = re.sub(pattern, replacement, text)
    tokens = [t for t in text.split() if t not in STOP_WORDS and len(t) > 1]
    return ' '.join(tokens)


def detect_category(name: str, hint: str = None) -> str:
    text = (name + ' ' + (hint or '')).lower().replace('ё', 'е')
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score
    if not scores:
        return 'Прочее'
    return max(scores, key=scores.get)


def _extract_tech_tokens(text: str) -> list:
    """Извлечь технические параметры: числа, размеры, обозначения."""
    tokens = []
    # Числа с единицами: Ду100, DN50, Ру16, PN16
    tokens += re.findall(r'(?:dn|ду|pn|ру)\s*\d+', text, re.IGNORECASE)
    # Просто числа (диаметры, мощности)
    tokens += re.findall(r'\d+(?:[.,]\d+)?', text)
    # Марки материала (буква+цифра): 12Х18Н10Т, 30С41НЖ
    tokens += re.findall(r'[а-яa-z]{1,4}\d+[а-яa-z]+\d*', text, re.IGNORECASE)
    return [t.lower().replace('ё', 'е') for t in tokens]


def match_material(product_name: str, materials):
    """
    Сопоставить название товара с материалами каталога.

    Возвращает dict: {material, score, explanation}
    """
    if not materials:
        return {'material': None, 'score': 0.0, 'explanation': 'Каталог МТР пуст'}

    norm_product = normalize_text(product_name)
    tech_tokens_product = _extract_tech_tokens(norm_product)

    best_material = None
    best_score = 0.0
    best_explanation = ''

    for mat in materials:
        norm_mat = normalize_text(mat.name)
        tech_tokens_mat = _extract_tech_tokens(norm_mat)

        # Три варианта нечёткого сравнения
        score_sort = fuzz.token_sort_ratio(norm_product, norm_mat)
        score_set = fuzz.token_set_ratio(norm_product, norm_mat)
        score_partial = fuzz.partial_ratio(norm_product, norm_mat)

        base_score = max(score_sort, score_set, score_partial)

        # Бонус за совпадение технических токенов
        tech_bonus = 0
        if tech_tokens_product and tech_tokens_mat:
            common = set(tech_tokens_product) & set(tech_tokens_mat)
            tech_bonus = min(15, len(common) * 5)

        total_score = min(100.0, base_score + tech_bonus)

        if total_score > best_score:
            best_score = total_score
            best_material = mat
            best_explanation = (
                f"token_sort={score_sort}, token_set={score_set}, "
                f"partial={score_partial}, tech_bonus={tech_bonus}"
            )

    return {
        'material': best_material,
        'score': round(best_score, 1),
        'explanation': best_explanation,
    }


def build_ai_comment(
    product_name: str,
    material,
    score: float,
    category: str,
    price=None,
) -> str:
    lines = [f"Категория: {category}"]

    if material:
        lines.append(f"Сопоставлен МТР: {material.code} — {material.name}")
        lines.append(f"Уверенность сопоставления: {score:.1f}%")

        if score >= 70:
            verdict = "Высокая уверенность — PriceQuote создан автоматически."
        elif score >= 35:
            if price:
                verdict = "Средняя уверенность — PriceQuote создан (рекомендуется ручная проверка)."
            else:
                verdict = "Средняя уверенность — цена не найдена, PriceQuote не создан."
        else:
            verdict = "Низкая уверенность — PriceQuote не создан, требуется ручное сопоставление."

        lines.append(verdict)
    else:
        lines.append("Совпадение с МТР не найдено.")
        lines.append("PriceQuote не создан.")

    if not price:
        lines.append("Цена на сайте не обнаружена.")

    return ' | '.join(lines)
