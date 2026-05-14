"""
Команда парсинга цен с сайтов поставщиков.

Использование:
  python manage.py parse_supplier_prices
  python manage.py parse_supplier_prices --active-only
  python manage.py parse_supplier_prices --source-id 3
  python manage.py parse_supplier_prices --limit 5
  python manage.py parse_supplier_prices --dry-run
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    ParsingSource, ParsedProduct, ParsingRun, Material, PriceQuote,
)
from core.services.parser_engine import parse_source
from core.services.ai_matching import (
    normalize_text, detect_category, match_material, build_ai_comment,
)

MIN_MATCH_SCORE = 35.0
AUTO_QUOTE_MIN_SCORE = 35.0


class Command(BaseCommand):
    help = 'Парсинг цен с сайтов поставщиков и создание/обновление PriceQuote'

    def add_arguments(self, parser):
        parser.add_argument('--source-id', type=int, default=None,
                            help='ID конкретного ParsingSource')
        parser.add_argument('--limit', type=int, default=None,
                            help='Максимальное количество источников')
        parser.add_argument('--dry-run', action='store_true',
                            help='Не сохранять в БД, только показать результат')
        parser.add_argument('--active-only', action='store_true', default=True,
                            help='Только активные источники (по умолчанию)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        source_id = options['source_id']
        limit = options['limit']

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN: изменения не сохраняются ---'))

        # Создать запись о запуске
        run = None
        if not dry_run:
            run = ParsingRun.objects.create(status='running')

        # Получить источники
        qs = ParsingSource.objects.select_related('supplier').filter(is_active=True)
        if source_id:
            qs = qs.filter(id=source_id)
        if limit:
            qs = qs[:limit]

        sources = list(qs)
        if not sources:
            self.stdout.write(self.style.WARNING('Активных источников парсинга не найдено.'))
            if run:
                run.status = 'failed'
                run.finished_at = timezone.now()
                run.error_log = 'Нет активных источников'
                run.save()
            return

        # Загружаем активные материалы каталога один раз, чтобы сопоставлять найденные товары без лишних запросов.
        materials = list(Material.objects.filter(is_active=True).select_related('category'))
        self.stdout.write(f"Материалов в каталоге: {len(materials)}")

        total_products = 0
        total_quotes_created = 0
        total_quotes_updated = 0
        sources_success = 0
        sources_failed = 0
        error_lines = []

        for source in sources:
            self.stdout.write(f"\n[{source.supplier.name}] {source.name} — {source.url}")

            products_raw, error = parse_source(source)

            if error:
                self.stdout.write(self.style.ERROR(f"  ОШИБКА: {error}"))
                sources_failed += 1
                error_lines.append(f"[{source.supplier.name}] {error}")
                if not dry_run:
                    source.last_parsed_at = timezone.now()
                    source.last_error = error
                    source.save(update_fields=['last_parsed_at', 'last_error'])
                continue

            sources_success += 1
            source_products_count = 0
            source_quotes_created = 0
            source_quotes_updated = 0

            for item in products_raw:
                product_name = item.get('name', '').strip()
                if not product_name:
                    continue

                category = detect_category(product_name, source.category_hint)
                norm_name = normalize_text(product_name)
                match_result = match_material(product_name, materials)

                matched_material = match_result['material']
                score = match_result['score']
                price_raw = item.get('price')

                ai_comment = build_ai_comment(
                    product_name, matched_material, score, category, price_raw
                )

                self.stdout.write(
                    f"  [{score:.0f}%] {product_name[:60]} "
                    f"-> {matched_material.code if matched_material else 'net'} "
                    f"| tsena: {price_raw or '-'}"
                )

                if dry_run:
                    continue

                # Сохраняем сырой результат парсинга для последующей проверки и сопоставления.
                parsed = ParsedProduct.objects.create(
                    source=source,
                    supplier=source.supplier,
                    material=matched_material if score >= MIN_MATCH_SCORE else None,
                    external_name=product_name,
                    normalized_name=norm_name,
                    external_code=item.get('article', ''),
                    category_detected=category,
                    price=price_raw,
                    currency='RUB',
                    availability=item.get('availability', ''),
                    delivery_days=item.get('delivery_days'),
                    product_url=item.get('url', ''),
                    characteristics=item.get('characteristics', {}),
                    match_score=score,
                    ai_comment=ai_comment,
                    raw_data={
                        'status_code': item.get('status_code'),
                        'url': item.get('url', ''),
                    },
                )
                source_products_count += 1

                # Для уверенно сопоставленных товаров сразу создаём или обновляем ценовое предложение.
                if (
                    matched_material
                    and score >= AUTO_QUOTE_MIN_SCORE
                    and price_raw is not None
                ):
                    delivery_days = item.get('delivery_days') or 14
                    availability_text = item.get('availability', '')
                    product_url = item.get('url', source.url)

                    notes_text = f"Автоматически получено с сайта: {product_url}"
                    logistics_notes = availability_text
                    payment_terms = "Автоматический сбор данных"

                    existing = PriceQuote.objects.filter(
                        supplier=source.supplier,
                        material=matched_material,
                    ).first()

                    if existing:
                        existing.price = Decimal(str(price_raw))
                        existing.delivery_days = delivery_days
                        existing.quote_date = timezone.now().date()
                        existing.notes = notes_text
                        existing.logistics_notes = logistics_notes
                        existing.payment_terms = payment_terms
                        existing.save()
                        source_quotes_updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    → PriceQuote обновлён: {matched_material.code} "
                                f"= {price_raw} руб."
                            )
                        )
                    else:
                        PriceQuote.objects.create(
                            supplier=source.supplier,
                            material=matched_material,
                            price=Decimal(str(price_raw)),
                            delivery_days=delivery_days,
                            quote_date=timezone.now().date(),
                            notes=notes_text,
                            logistics_notes=logistics_notes,
                            payment_terms=payment_terms,
                        )
                        source_quotes_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    → PriceQuote создан: {matched_material.code} "
                                f"= {price_raw} руб."
                            )
                        )

            total_products += source_products_count
            total_quotes_created += source_quotes_created
            total_quotes_updated += source_quotes_updated

            if not dry_run:
                source.last_parsed_at = timezone.now()
                source.last_success_at = timezone.now()
                source.last_error = ''
                source.save(update_fields=['last_parsed_at', 'last_success_at', 'last_error'])

            self.stdout.write(
                f"  Итого: товаров={source_products_count}, "
                f"создано={source_quotes_created}, обновлено={source_quotes_updated}"
            )

        # Финальная статистика
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(
            f"Источников: {len(sources)} (успешно={sources_success}, ошибок={sources_failed})"
        )
        self.stdout.write(f"Товаров найдено: {total_products}")
        self.stdout.write(f"PriceQuote создано: {total_quotes_created}")
        self.stdout.write(f"PriceQuote обновлено: {total_quotes_updated}")

        if not dry_run and run:
            if sources_failed == 0:
                final_status = 'success'
            elif sources_success > 0:
                final_status = 'partial'
            else:
                final_status = 'failed'

            run.finished_at = timezone.now()
            run.status = final_status
            run.sources_total = len(sources)
            run.sources_success = sources_success
            run.sources_failed = sources_failed
            run.products_found = total_products
            run.quotes_created = total_quotes_created
            run.quotes_updated = total_quotes_updated
            run.error_log = '\n'.join(error_lines)
            run.save()

            self.stdout.write(self.style.SUCCESS(f"Запуск #{run.id} завершён: {final_status}"))
