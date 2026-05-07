"""
Безопасный поиск новых поставщиков.

Требует SERPAPI_API_KEY для автоматического поиска, либо принимает CSV.
Все найденные сайты сохраняются как SupplierCandidate (статус new).
Финальное включение в парсинг делает администратор вручную.

Использование:
  python manage.py discover_supplier_sites --limit 5
  python manage.py discover_supplier_sites --csv new_suppliers.csv
  python manage.py discover_supplier_sites --query-id 3
  python manage.py discover_supplier_sites --dry-run
"""
import csv
import os
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import SupplierDiscoveryQuery, SupplierDiscoveryRun, SupplierCandidate
from core.services.supplier_discovery import (
    search_supplier_candidates,
    analyze_supplier_site,
    calculate_supplier_score,
)


class Command(BaseCommand):
    help = 'Поиск новых поставщиков через API или CSV с анализом сайтов'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None,
                            help='Максимальное количество запросов для обработки')
        parser.add_argument('--query-id', type=int, default=None,
                            help='ID конкретного SupplierDiscoveryQuery')
        parser.add_argument('--dry-run', action='store_true',
                            help='Показать результат без сохранения в БД')
        parser.add_argument('--csv', type=str, default=None,
                            help='Путь к CSV-файлу с кандидатами (name,website,category_hint)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        query_id = options['query_id']
        csv_path = options['csv']

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN ---'))

        run = None
        if not dry_run:
            run = SupplierDiscoveryRun.objects.create(status='running')

        candidates_found = 0
        candidates_created = 0
        candidates_updated = 0
        error_lines = []

        # ── Режим CSV ──
        if csv_path:
            if not os.path.exists(csv_path):
                self.stdout.write(self.style.ERROR(f"CSV-файл не найден: {csv_path}"))
                if run:
                    run.status = 'failed'
                    run.error_log = f"CSV-файл не найден: {csv_path}"
                    run.finished_at = timezone.now()
                    run.save()
                return

            with open(csv_path, encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))

            self.stdout.write(f"CSV: строк={len(rows)}")
            raw_candidates = []
            for row in rows:
                name = row.get('name', '').strip()
                website = row.get('website', '').strip()
                category_hint = row.get('category_hint', '').strip()
                query_text = row.get('discovery_query', '').strip()
                if name and website:
                    raw_candidates.append({
                        'name': name,
                        'website': website,
                        'category_hint': category_hint,
                        'reason': query_text or 'Импортирован из CSV',
                    })

            self._process_candidates(
                raw_candidates, dry_run,
                candidates_found, candidates_created, candidates_updated, error_lines, run
            )
            return

        # ── Режим поиска через API ──
        has_api_key = bool(os.environ.get('SERPAPI_API_KEY') or os.environ.get('SEARCH_API_KEY'))
        if not has_api_key:
            self.stdout.write(self.style.WARNING(
                'SERPAPI_API_KEY не задан. Автоматический поиск недоступен.\n'
                'Варианты:\n'
                '  1. Добавьте SERPAPI_API_KEY в переменные окружения.\n'
                '  2. Используйте --csv для импорта кандидатов из файла.\n'
                '  3. Добавьте кандидатов вручную через Django Admin.\n'
            ))
            if run:
                run.status = 'failed'
                run.error_log = 'SERPAPI_API_KEY не задан, поиск невозможен'
                run.finished_at = timezone.now()
                run.save()
            return

        # Получить запросы
        qs = SupplierDiscoveryQuery.objects.filter(is_active=True)
        if query_id:
            qs = qs.filter(id=query_id)
        if limit:
            qs = qs[:limit]

        queries = list(qs)
        if not queries:
            self.stdout.write(self.style.WARNING(
                'Нет активных запросов. Запустите seed_supplier_discovery_queries.'
            ))
            if run:
                run.status = 'failed'
                run.finished_at = timezone.now()
                run.save()
            return

        if run:
            run.queries_total = len(queries)
            run.save(update_fields=['queries_total'])

        for query in queries:
            self.stdout.write(f"\nЗапрос: {query.query}")
            try:
                raw = search_supplier_candidates(query.query)
                candidates_found += len(raw)
                self.stdout.write(f"  Найдено: {len(raw)} кандидатов")
                for candidate in raw:
                    self._process_one(
                        candidate, dry_run,
                        candidates_created_ref=[candidates_created],
                        candidates_updated_ref=[candidates_updated],
                    )
                    candidates_created = candidates_created  # обновляется внутри _process_one через list
            except Exception as exc:
                msg = f"Ошибка при запросе '{query.query}': {exc}"
                self.stdout.write(self.style.ERROR(f"  {msg}"))
                error_lines.append(msg)

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(f"Кандидатов найдено: {candidates_found}")
        self.stdout.write(f"Кандидатов создано: {candidates_created}")
        self.stdout.write(f"Кандидатов обновлено: {candidates_updated}")

        if run:
            run.finished_at = timezone.now()
            run.status = 'success' if not error_lines else 'partial'
            run.candidates_found = candidates_found
            run.candidates_created = candidates_created
            run.candidates_updated = candidates_updated
            run.error_log = '\n'.join(error_lines)
            run.save()

    def _process_candidates(
        self, raw_list, dry_run,
        found, created, updated, errors, run,
    ):
        found = len(raw_list)
        created_local = 0
        updated_local = 0

        for item in raw_list:
            website = item.get('website', '').strip()
            name = item.get('name', '').strip()
            if not website or not name:
                continue

            self.stdout.write(f"  Анализ: {name} — {website}")
            try:
                analysis = analyze_supplier_site(website) if not dry_run else {}
            except Exception as exc:
                errors.append(f"{website}: {exc}")
                analysis = {}

            if dry_run:
                self.stdout.write(f"    [dry-run] пропущен")
                continue

            existing = SupplierCandidate.objects.filter(website=website).first()
            score = analysis.get('supplier_score', 0.0)

            if existing:
                existing.supplier_score = score
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
                updated_local += 1
            else:
                SupplierCandidate.objects.create(
                    name=name,
                    website=website,
                    category_hint=item.get('category_hint', ''),
                    status='new',
                    confidence_score=score,
                    reason=analysis.get('reason', item.get('reason', '')),
                    supplier_score=score,
                    detected_contacts=analysis.get('detected_contacts', {}),
                    detected_categories=analysis.get('detected_categories', []),
                    detected_catalog_urls=analysis.get('detected_catalog_urls', []),
                    detected_product_urls=analysis.get('detected_product_urls', []),
                    has_prices=analysis.get('has_prices', False),
                    has_contacts=analysis.get('has_contacts', False),
                    has_requisites=analysis.get('has_requisites', False),
                    has_delivery_rf=analysis.get('has_delivery_rf', False),
                    has_product_cards=analysis.get('has_product_cards', False),
                    site_status_code=analysis.get('site_status_code'),
                    site_response_time_ms=analysis.get('site_response_time_ms'),
                    risk_flags=analysis.get('risk_flags', []),
                )
                created_local += 1

        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(f"Обработано: {found}, создано: {created_local}, обновлено: {updated_local}")

        if run:
            run.finished_at = timezone.now()
            run.status = 'success' if not errors else 'partial'
            run.candidates_found = found
            run.candidates_created = created_local
            run.candidates_updated = updated_local
            run.error_log = '\n'.join(errors)
            run.save()

    def _process_one(self, item, dry_run, candidates_created_ref, candidates_updated_ref):
        """Обработать одного кандидата (из API-поиска)."""
        website = item.get('website', '').strip()
        name = item.get('name', '').strip()
        if not website or not name:
            return

        try:
            analysis = analyze_supplier_site(website) if not dry_run else {}
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"    Анализ {website}: {exc}"))
            analysis = {}

        score = analysis.get('supplier_score', 0.0)
        self.stdout.write(
            f"  {name} | score={score:.0f} | "
            f"{'цены' if analysis.get('has_prices') else ''} "
            f"{'каталог' if analysis.get('detected_catalog_urls') else ''}"
        )

        if dry_run:
            return

        existing = SupplierCandidate.objects.filter(website=website).first()
        if existing:
            existing.supplier_score = score
            existing.save(update_fields=['supplier_score'])
            candidates_updated_ref[0] += 1
        else:
            SupplierCandidate.objects.create(
                name=name,
                website=website,
                status='new',
                confidence_score=score,
                supplier_score=score,
                reason=analysis.get('reason', item.get('reason', '')),
                detected_contacts=analysis.get('detected_contacts', {}),
                detected_categories=analysis.get('detected_categories', []),
                detected_catalog_urls=analysis.get('detected_catalog_urls', []),
                has_prices=analysis.get('has_prices', False),
                has_contacts=analysis.get('has_contacts', False),
                site_status_code=analysis.get('site_status_code'),
                risk_flags=analysis.get('risk_flags', []),
            )
            candidates_created_ref[0] += 1
