from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Catalog – categories
    path('catalog/categories/', views.category_list, name='category_list'),
    path('catalog/categories/new/', views.category_create, name='category_create'),
    path('catalog/categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('catalog/categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Catalog – materials
    path('catalog/', views.material_list, name='material_list'),
    path('catalog/new/', views.material_create, name='material_create'),
    path('catalog/<int:pk>/', views.material_detail, name='material_detail'),
    path('catalog/<int:pk>/edit/', views.material_update, name='material_update'),
    path('catalog/<int:pk>/delete/', views.material_delete, name='material_delete'),

    # Warehouse
    path('warehouse/', views.warehouse_list, name='warehouse_list'),
    path('warehouse/new/', views.warehouse_create, name='warehouse_create'),
    path('warehouse/<int:pk>/edit/', views.warehouse_update, name='warehouse_update'),
    path('warehouse/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),

    # Purchase requests
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/edit/', views.request_edit, name='request_edit'),
    path('requests/<int:pk>/add-item/', views.request_add_item, name='request_add_item'),
    path('requests/<int:pk>/delete-item/<int:item_pk>/', views.request_delete_item, name='request_delete_item'),
    path('requests/<int:pk>/submit/', views.request_submit, name='request_submit'),
    path('requests/<int:pk>/approve/', views.request_approve, name='request_approve'),
    path('requests/<int:pk>/reject/', views.request_reject, name='request_reject'),
    path('requests/<int:pk>/return-to-draft/', views.request_return_to_draft, name='request_return_to_draft'),

    # Market analysis / quote selection
    path('requests/item/<int:item_pk>/analyse/', views.market_analysis, name='market_analysis'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/new/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Price quotes
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/new/', views.quote_create, name='quote_create'),
    path('quotes/<int:pk>/edit/', views.quote_update, name='quote_update'),
    path('quotes/<int:pk>/delete/', views.quote_delete, name='quote_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/<int:request_pk>/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/status/', views.order_status_update, name='order_status_update'),

    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/price-dynamics/', views.price_dynamics, name='price_dynamics'),
    path('analytics/shortage/', views.shortage_report, name='shortage_report'),
    path('analytics/reports/', views.reports, name='reports'),

    # Admin panel
    path('admin-panel/users/', views.user_list, name='user_list'),
    path('admin-panel/users/new/', views.user_create, name='user_create'),
    path('admin-panel/users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('admin-panel/audit/', views.audit_log_view, name='audit_log'),
]
