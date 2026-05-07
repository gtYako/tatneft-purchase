"""
Заполняет базу поисковыми запросами для discovery-модуля.

Использование:
  python manage.py seed_supplier_discovery_queries
"""
from django.core.management.base import BaseCommand

from core.models import SupplierDiscoveryQuery

QUERIES = [
    'купить датчик давления промышленный цена поставщик РФ',
    'купить преобразователь давления КИПиА поставщик Россия',
    'купить задвижка 30с41нж Ду100 Ру16 цена',
    'купить кран шаровой фланцевый Ду50 Ру16',
    'купить насос ЭЦН нефтяной поставщик',
    'купить насос для нефтепродуктов промышленный Россия',
    'купить кабель ВВГнг LS поставщик РФ',
    'купить деэмульгатор нефтяной реагент поставщик',
    'купить НКТ трубы поставщик Россия',
    'купить электродвигатель взрывозащищенный поставщик',
]


class Command(BaseCommand):
    help = 'Добавляет поисковые запросы для модуля поиска поставщиков'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for query_text in QUERIES:
            _, is_new = SupplierDiscoveryQuery.objects.get_or_create(query=query_text)
            if is_new:
                created += 1
                self.stdout.write(f"  + {query_text}")
            else:
                skipped += 1

        self.stdout.write(f"\nЗапросов создано: {created}, уже существовало: {skipped}")
        self.stdout.write(
            self.style.SUCCESS(
                'Используйте команду discover_supplier_sites '
                'после настройки SERPAPI_API_KEY или с флагом --csv.'
            )
        )
