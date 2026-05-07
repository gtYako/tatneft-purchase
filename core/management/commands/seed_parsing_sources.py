"""
Заполняет базу источниками парсинга российских поставщиков.

Активные источники — те, у которых структура страниц достаточно стандартна
для универсального парсера. Остальные добавляются с is_active=False
для ручной проверки и настройки.

Использование:
  python manage.py seed_parsing_sources
"""
from django.core.management.base import BaseCommand

from core.models import Supplier, ParsingSource, SupplierCandidate

SUPPLIERS_DATA = [
    # (name, inn_fake, active_sources, inactive_sources)
    # inn_fake — временный уникальный ИНН для демо-данных
    {
        'name': 'ТД Автоматика',
        'inn': '7710001001',
        'website': 'https://tdatm.ru/',
        'notes': 'Поставщик КИПиА и средств автоматизации',
        'rating': 7.5,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог КИПиА',
                'url': 'https://tdatm.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'РусАвтоматизация',
        'inn': '7710001002',
        'website': 'https://rusautomation.ru/',
        'notes': 'КИПиА, датчики, регуляторы',
        'rating': 7.0,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог продукции',
                'url': 'https://rusautomation.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'ТехАрматура',
        'inn': '7710001003',
        'website': 'https://teharmatura.ru/',
        'notes': 'Запорная арматура, краны, клапаны',
        'rating': 7.0,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог арматуры',
                'url': 'https://teharmatura.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Запорная арматура',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'TDM Electric',
        'inn': '7710001004',
        'website': 'https://tdme.ru/',
        'notes': 'Электрооборудование, кабель, коммутация',
        'rating': 7.5,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог TDM Electric',
                'url': 'https://tdme.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Кабельная продукция',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'Cable.ru',
        'inn': '7710001005',
        'website': 'https://cable.ru/',
        'notes': 'Кабельная продукция и провода',
        'rating': 7.5,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог кабельной продукции',
                'url': 'https://cable.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Кабельная продукция',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'ОВЕН',
        'inn': '7710001006',
        'website': 'https://owen.ru/',
        'notes': 'Приборы КИПиА, ПЛК, SCADA',
        'rating': 8.0,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог ОВЕН',
                'url': 'https://owen.ru/product/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': True,
            },
        ],
    },
    {
        'name': '4АСУТП',
        'inn': '7710001007',
        'website': 'https://4asutp.ru/',
        'notes': 'Автоматизация и КИПиА',
        'rating': 6.5,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог 4АСУТП',
                'url': 'https://4asutp.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': True,
            },
        ],
    },
    {
        'name': 'Завод Насосов',
        'inn': '7710001008',
        'website': 'https://zavodnasos.com/',
        'notes': 'Насосное оборудование',
        'rating': 7.0,
        'is_active': True,
        'sources': [
            {
                'name': 'Каталог насосов',
                'url': 'https://zavodnasos.com/catalog/',
                'source_type': 'listing',
                'category_hint': 'Насосное оборудование',
                'is_active': True,
            },
        ],
    },
    # ── Неактивные (требуют ручной проверки) ──
    {
        'name': 'ЭТМ',
        'inn': '7810001001',
        'website': 'https://www.etm.ru/',
        'notes': 'Электротехнические материалы — крупный дистрибьютор',
        'rating': 8.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог ЭТМ',
                'url': 'https://www.etm.ru/cat/',
                'source_type': 'listing',
                'category_hint': 'Кабельная продукция',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'Эвелен',
        'inn': '7810001002',
        'website': 'https://evelen.ru/',
        'notes': 'Промышленная автоматизация',
        'rating': 6.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог Эвелен',
                'url': 'https://evelen.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'КИП-Сервис',
        'inn': '7810001003',
        'website': 'https://kipservis.ru/',
        'notes': 'КИПиА, сервис и ремонт',
        'rating': 6.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог КИП-Сервис',
                'url': 'https://kipservis.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'КИПиА.ру',
        'inn': '7810001004',
        'website': 'https://kipia.ru/',
        'notes': 'Датчики и приборы КИПиА',
        'rating': 6.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Продукция КИПиА.ру',
                'url': 'https://kipia.ru/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'ЧипДип',
        'inn': '7810001005',
        'website': 'https://www.chipdip.ru/',
        'notes': 'Радиоэлектронные компоненты и КИПиА',
        'rating': 7.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог ЧипДип',
                'url': 'https://www.chipdip.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'КИПиА',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'АрмПроф',
        'inn': '7810001006',
        'website': 'https://www.armprof.ru/',
        'notes': 'Промышленная арматура',
        'rating': 6.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог арматуры АрмПроф',
                'url': 'https://www.armprof.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Запорная арматура',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'OilPump',
        'inn': '7810001007',
        'website': 'https://oilpump.ru/',
        'notes': 'Насосы для нефтепродуктов',
        'rating': 6.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог насосов OilPump',
                'url': 'https://oilpump.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Насосное оборудование',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'Ливгидромаш',
        'inn': '7810001008',
        'website': 'https://www.hms-livgidromash.ru/',
        'notes': 'Насосное оборудование HMS Livgidromash',
        'rating': 7.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Продукция Ливгидромаш',
                'url': 'https://www.hms-livgidromash.ru/products/',
                'source_type': 'listing',
                'category_hint': 'Насосное оборудование',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'NTE Company',
        'inn': '7810001009',
        'website': 'https://nte-company.ru/',
        'notes': 'Электротехническое оборудование',
        'rating': 6.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог NTE',
                'url': 'https://nte-company.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Электродвигатели',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'ПроЭнергоСолюшн',
        'inn': '7810001010',
        'website': 'https://proensol.ru/',
        'notes': 'Электроэнергетическое оборудование',
        'rating': 6.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог ПроЭнергоСолюшн',
                'url': 'https://proensol.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Электродвигатели',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'ТД Техмаш',
        'inn': '7810001011',
        'website': 'https://tdtechmash.ru/',
        'notes': 'Промышленное оборудование',
        'rating': 6.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог ТД Техмаш',
                'url': 'https://tdtechmash.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Насосное оборудование',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'РусЭлКаб',
        'inn': '7810001012',
        'website': 'https://www.ruselcab.ru/',
        'notes': 'Кабельно-проводниковая продукция',
        'rating': 6.5,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог РусЭлКаб',
                'url': 'https://www.ruselcab.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Кабельная продукция',
                'is_active': False,
            },
        ],
    },
    {
        'name': 'Лайта',
        'inn': '7810001013',
        'website': 'https://www.layta.ru/',
        'notes': 'Светотехника и электрооборудование',
        'rating': 6.0,
        'is_active': False,
        'sources': [
            {
                'name': 'Каталог Лайта',
                'url': 'https://www.layta.ru/catalog/',
                'source_type': 'listing',
                'category_hint': 'Кабельная продукция',
                'is_active': False,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Добавляет базу российских поставщиков и источников парсинга'

    def handle(self, *args, **options):
        suppliers_created = 0
        suppliers_updated = 0
        sources_created = 0
        sources_skipped = 0
        candidates_created = 0

        for data in SUPPLIERS_DATA:
            supplier, created = Supplier.objects.get_or_create(
                inn=data['inn'],
                defaults={
                    'name': data['name'],
                    'notes': data.get('notes', ''),
                    'rating': data.get('rating', 7.0),
                    'is_active': data.get('is_active', True),
                },
            )
            if created:
                suppliers_created += 1
                self.stdout.write(self.style.SUCCESS(f"  Поставщик создан: {supplier.name}"))
            else:
                suppliers_updated += 1
                self.stdout.write(f"  Поставщик уже есть: {supplier.name}")

            for src_data in data.get('sources', []):
                existing = ParsingSource.objects.filter(
                    supplier=supplier,
                    url=src_data['url'],
                ).first()
                if existing:
                    sources_skipped += 1
                else:
                    ParsingSource.objects.create(
                        supplier=supplier,
                        name=src_data['name'],
                        url=src_data['url'],
                        source_type=src_data.get('source_type', 'listing'),
                        category_hint=src_data.get('category_hint', ''),
                        is_active=src_data.get('is_active', True),
                        max_items_per_run=10,
                        request_delay_seconds=3,
                    )
                    sources_created += 1
                    status_label = 'АКТИВЕН' if src_data.get('is_active') else 'неактивен'
                    self.stdout.write(
                        f"    Источник [{status_label}]: {src_data['name']}"
                    )

            # Неактивные поставщики — ещё и как SupplierCandidate для модерации
            if not data.get('is_active', True):
                website = data.get('website', '')
                if not SupplierCandidate.objects.filter(website=website).exists():
                    SupplierCandidate.objects.create(
                        name=data['name'],
                        website=website,
                        category_hint=data.get('notes', ''),
                        status='new',
                        confidence_score=60.0,
                        reason='Добавлен из seed_parsing_sources как неактивный поставщик',
                    )
                    candidates_created += 1

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(f"Поставщиков создано: {suppliers_created}")
        self.stdout.write(f"Поставщиков уже существовало: {suppliers_updated}")
        self.stdout.write(f"Источников парсинга создано: {sources_created}")
        self.stdout.write(f"Источников пропущено (уже есть): {sources_skipped}")
        self.stdout.write(f"Кандидатов для модерации создано: {candidates_created}")
        self.stdout.write(self.style.SUCCESS('\nGотово. Активные источники готовы к парсингу.'))
        self.stdout.write(
            'Неактивные источники можно включить в Django Admin > Источники парсинга.'
        )
