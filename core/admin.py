from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog,
    ParsingSource, ParsedProduct, ParsingRun,
    SupplierCandidate, SupplierDiscoveryQuery, SupplierDiscoveryRun,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'department', 'position')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'unit', 'criticality', 'is_active')
    list_filter = ('category', 'criticality', 'is_active')
    search_fields = ('code', 'name')


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ('material', 'location', 'qty_on_hand', 'qty_reserved', 'last_update')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'rating', 'delivery_reliability', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'inn')


@admin.register(PriceQuote)
class PriceQuoteAdmin(admin.ModelAdmin):
    list_display = ('material', 'supplier', 'price', 'delivery_days', 'quote_date')
    list_filter = ('supplier',)


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'requester', 'department', 'criticality', 'status', 'need_date', 'created_at')
    list_filter = ('status', 'criticality')


@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ('request', 'material', 'qty_requested', 'qty_to_purchase', 'target_price')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'request', 'supplier', 'status', 'total_amount', 'order_date')
    list_filter = ('status',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id')
    list_filter = ('model_name',)
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'object_repr', 'details', 'ip_address')


# ─────────────────── МОНИТОРИНГ ПОСТАВЩИКОВ ───────────────────

@admin.register(ParsingSource)
class ParsingSourceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'supplier', 'source_type', 'category_hint',
        'is_active', 'last_parsed_at', 'last_success_at', 'has_error',
    )
    list_filter = ('is_active', 'source_type', 'supplier')
    search_fields = ('name', 'url', 'supplier__name')
    readonly_fields = ('last_parsed_at', 'last_success_at', 'created_at', 'updated_at')
    list_editable = ('is_active',)

    @admin.display(boolean=True, description='Ошибка')
    def has_error(self, obj):
        return bool(obj.last_error)


@admin.register(ParsedProduct)
class ParsedProductAdmin(admin.ModelAdmin):
    list_display = (
        'external_name', 'supplier', 'category_detected',
        'price', 'match_score_display', 'material', 'parsed_at',
    )
    list_filter = ('supplier', 'category_detected', 'source')
    search_fields = ('external_name', 'external_code', 'supplier__name')
    readonly_fields = ('parsed_at', 'ai_comment', 'raw_data')
    list_select_related = ('supplier', 'material', 'source')

    @admin.display(description='Совпадение, %')
    def match_score_display(self, obj):
        return f"{obj.match_score:.0f}%"


@admin.register(ParsingRun)
class ParsingRunAdmin(admin.ModelAdmin):
    list_display = (
        'started_at', 'status', 'sources_total', 'sources_success',
        'sources_failed', 'products_found', 'quotes_created', 'quotes_updated',
    )
    list_filter = ('status',)
    readonly_fields = (
        'started_at', 'finished_at', 'sources_total', 'sources_success',
        'sources_failed', 'products_found', 'quotes_created', 'quotes_updated', 'error_log',
    )


def _approve_candidates(modeladmin, request, queryset):
    """Одобрить кандидатов и создать Supplier + неактивный ParsingSource."""
    for candidate in queryset.filter(status='new'):
        # Создать Supplier если не существует
        supplier, _ = Supplier.objects.get_or_create(
            name=candidate.name,
            defaults={
                'inn': f"99{candidate.id:08d}",  # временный ИНН для модерации
                'notes': f"Создан из SupplierCandidate #{candidate.id}. Сайт: {candidate.website}",
                'is_active': True,
                'rating': 5.0,
            },
        )
        # Создать неактивные ParsingSource для найденных каталогов
        for catalog_url in (candidate.detected_catalog_urls or [candidate.website])[:3]:
            if not ParsingSource.objects.filter(supplier=supplier, url=catalog_url).exists():
                ParsingSource.objects.create(
                    supplier=supplier,
                    name=f"Каталог {candidate.name}",
                    url=catalog_url,
                    source_type='listing',
                    category_hint=candidate.category_hint,
                    is_active=False,  # администратор включает вручную
                )
        candidate.status = 'approved'
        candidate.reviewed_at = timezone.now()
        candidate.save(update_fields=['status', 'reviewed_at'])

    modeladmin.message_user(
        request,
        f"Одобрено {queryset.filter(status='approved').count()} кандидатов. "
        "Поставщики созданы. Источники парсинга добавлены в неактивном состоянии.",
    )


_approve_candidates.short_description = 'Одобрить и создать поставщиков (is_active=False для источников)'


def _reject_candidates(modeladmin, request, queryset):
    updated = queryset.filter(status='new').update(
        status='rejected',
        reviewed_at=timezone.now(),
    )
    modeladmin.message_user(request, f"Отклонено: {updated}")


_reject_candidates.short_description = 'Отклонить выбранных кандидатов'


@admin.register(SupplierCandidate)
class SupplierCandidateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'website', 'status', 'supplier_score',
        'has_prices', 'has_contacts', 'has_product_cards',
        'site_status_code', 'created_at',
    )
    list_filter = ('status', 'has_prices', 'has_contacts', 'has_product_cards')
    search_fields = ('name', 'website', 'category_hint')
    readonly_fields = (
        'created_at', 'reviewed_at', 'supplier_score', 'risk_flags',
        'detected_contacts', 'detected_categories',
        'detected_catalog_urls', 'detected_product_urls',
        'site_status_code', 'site_response_time_ms',
    )
    actions = [_approve_candidates, _reject_candidates]


@admin.register(SupplierDiscoveryQuery)
class SupplierDiscoveryQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'is_active', 'created_at')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


@admin.register(SupplierDiscoveryRun)
class SupplierDiscoveryRunAdmin(admin.ModelAdmin):
    list_display = (
        'started_at', 'status', 'queries_total',
        'candidates_found', 'candidates_created', 'candidates_updated',
    )
    list_filter = ('status',)
    readonly_fields = (
        'started_at', 'finished_at', 'queries_total',
        'candidates_found', 'candidates_created', 'candidates_updated', 'error_log',
    )
