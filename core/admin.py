from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog
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
