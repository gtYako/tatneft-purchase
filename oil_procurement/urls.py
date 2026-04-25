from django.contrib import admin
from django.urls import path, include
from core import api

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # ─── Auth API ───
    path('api/auth/csrf/', api.csrf_view),
    path('api/auth/login/', api.login_view),
    path('api/auth/logout/', api.logout_view),
    path('api/auth/me/', api.me_view),

    # ─── Catalog ───
    path('api/categories/', api.CategoryListCreate.as_view()),
    path('api/categories/all/', api.categories_all),
    path('api/categories/<int:pk>/', api.CategoryDetail.as_view()),

    # ─── Materials ───
    path('api/materials/all/', api.materials_all),
    path('api/materials/', api.MaterialListCreate.as_view()),
    path('api/materials/<int:pk>/', api.MaterialDetail.as_view()),

    # ─── Warehouse ───
    path('api/warehouse/', api.WarehouseListCreate.as_view()),
    path('api/warehouse/<int:pk>/', api.WarehouseDetail.as_view()),

    # ─── Suppliers ───
    path('api/suppliers/all/', api.suppliers_all),
    path('api/suppliers/', api.SupplierListCreate.as_view()),
    path('api/suppliers/<int:pk>/', api.SupplierDetail.as_view()),

    # ─── Price Quotes ───
    path('api/quotes/', api.QuoteListCreate.as_view()),
    path('api/quotes/<int:pk>/', api.QuoteDetail.as_view()),

    # ─── Purchase Requests ───
    path('api/requests/', api.RequestListCreate.as_view()),
    path('api/requests/<int:pk>/submit/', api.request_submit),
    path('api/requests/<int:pk>/approve/', api.request_approve),
    path('api/requests/<int:pk>/reject/', api.request_reject),
    path('api/requests/<int:pk>/return-to-draft/', api.request_return_to_draft),
    path('api/requests/<int:pk>/add-item/', api.request_add_item),
    path('api/requests/<int:pk>/items/<int:item_pk>/delete/', api.request_delete_item),
    path('api/requests/<int:pk>/', api.RequestDetailView.as_view()),

    # ─── Items analysis ───
    path('api/items/<int:item_pk>/analyse/', api.item_analyse),
    path('api/items/<int:item_pk>/select-quote/', api.item_select_quote),

    # ─── Orders ───
    path('api/orders/prefill/<int:request_pk>/', api.order_prefill),
    path('api/orders/<int:pk>/status/', api.order_status_update),
    path('api/orders/', api.OrderListCreate.as_view()),
    path('api/orders/<int:pk>/', api.OrderDetail.as_view()),

    # ─── Analytics ───
    path('api/analytics/dashboard/', api.analytics_dashboard),
    path('api/analytics/price-dynamics/', api.analytics_price_dynamics),
    path('api/analytics/shortage/', api.analytics_shortage),
    path('api/analytics/reports/', api.analytics_reports),

    # ─── Admin panel ───
    path('api/admin/users/', api.user_list_create),
    path('api/admin/users/<int:pk>/', api.user_detail),
    path('api/admin/audit/', api.audit_log_list),
]
