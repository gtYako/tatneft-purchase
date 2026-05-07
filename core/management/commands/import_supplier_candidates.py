"""
Импорт кандидатов поставщиков из CSV-файла.

Формат CSV (с заголовком):
  name,website,category_hint,confidence_score,reason

Пример:
  python manage.py import_supplier_candidates --csv candidates.csv
  python manage.py import_supplier_candidates --csv candidates.csv --analyze
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import SupplierCandidate
from core.services.supplier_discovery import analyze_supplier_site


class Command(BaseCommand):
    help = 'Импорт кандидатов поставщиков из CSV'

    def add_arguments(self, parser):
        parser.add_argument('--csv', required=True, help='Путь к CSV-файлу')
        parser.add_argument(
            '--analyze', action='store_true',
            help='Анализировать сайт каждого кандидата через analyze_supplier_site'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Показать что будет импортировано, без сохранения в БД'
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        do_analyze = options['analyze']
        dry_run = options['dry_run']

        if not os.path.exists(csv_path):
            raise CommandError(f"Файл не найден: {csv_path}")

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN ---'))

        created = 0
        updated = 0
        skipped = 0

        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"Строк в файле: {len(rows)}")

        for row in rows:
            name = row.get('name', '').strip()
            website = row.get('website', '').strip()
            category_hint = row.get('category_hint', '').strip()
            reason = row.get('reason', '').strip()

            try:
                confidence_score = float(row.get('confidence_score', 0) or 0)
            except (ValueError, TypeError):
                confidence_score = 0.0

            if not name or not website:
                self.stdout.write(self.style.WARNING(f"  Пропущена строка (нет name/website): {row}"))
                skipped += 1
                continue

            self.stdout.write(f"  {name} — {website}")

            analysis = {}
            if do_analyze and not dry_run:
                self.stdout.write(f"    Анализ сайта...")
                analysis = analyze_supplier_site(website)
                self.stdout.write(
                    f"    score={analysis.get('supplier_score', 0):.0f}, "
                    f"reason={analysis.get('reason', '')[:80]}"
                )

            if dry_run:
                continue

            existing = SupplierCandidate.objects.filter(website=website).first()

            if existing:
                if analysis:
                    existing.supplier_score = analysis.get('supplier_score', existing.supplier_score)
                    existing.reason = analysis.get('reason', existing.reason)
                    existing.detected_contacts = analysis.get('detected_contacts', {})
                    existing.detected_categories = analysis.get('detected_categories', [])
                    existing.detected_catalog_urls = analysis.get('detected_catalog_urls', [])
                    existing.detected_product_urls = analysis.get('detected_product_urls', [])
                    existing.has_prices = analysis.get('has_prices', False)
                    existing.has_contacts = analysis.get('has_contacts', False)
                    existing.has_requisites = analysis.get('has_requisites', False)
                    existing.has_delivery_rf = analysis.get('has_delivery_rf', False)
                    existing.has_product_cards = analysis.get('has_product_cards', False)
                    existing.site_status_code = analysis.get('site_status_code')
                    existing.site_response_time_ms = analysis.get('site_response_time_ms')
                    existing.risk_flags = analysis.get('risk_flags', [])
                    existing.save()
                updated += 1
            else:
                defaults = {
                    'name': name,
                    'category_hint': category_hint,
                    'confidence_score': confidence_score,
                    'reason': reason,
                    'status': 'new',
                }
                if analysis:
                    defaults.update({
                        'supplier_score': analysis.get('supplier_score', confidence_score),
                        'reason': analysis.get('reason', reason),
                        'detected_contacts': analysis.get('detected_contacts', {}),
                        'detected_categories': analysis.get('detected_categories', []),
                        'detected_catalog_urls': analysis.get('detected_catalog_urls', []),
                        'detected_product_urls': analysis.get('detected_product_urls', []),
                        'has_prices': analysis.get('has_prices', False),
                        'has_contacts': analysis.get('has_contacts', False),
                        'has_requisites': analysis.get('has_requisites', False),
                        'has_delivery_rf': analysis.get('has_delivery_rf', False),
                        'has_product_cards': analysis.get('has_product_cards', False),
                        'site_status_code': analysis.get('site_status_code'),
                        'site_response_time_ms': analysis.get('site_response_time_ms'),
                        'risk_flags': analysis.get('risk_flags', []),
                    })

                SupplierCandidate.objects.create(website=website, **defaults)
                created += 1

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(f"Создано кандидатов: {created}")
        self.stdout.write(f"Обновлено кандидатов: {updated}")
        self.stdout.write(f"Пропущено строк: {skipped}")
        self.stdout.write(
            self.style.SUCCESS(
                'Перейдите в Django Admin → Кандидаты поставщиков для проверки и одобрения.'
            )
        )
