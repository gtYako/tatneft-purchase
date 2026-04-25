from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, Avg, Count
from django.urls import reverse
from django.utils import timezone
import json


def paginate(request, queryset, per_page=20):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)

from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog
)
from .forms import (
    CategoryForm, MaterialForm, WarehouseStockForm,
    SupplierForm, PriceQuoteForm, PurchaseRequestForm,
    RequestItemForm, RejectRequestForm, SelectQuoteForm,
    PurchaseOrderForm, CustomUserCreateForm, CustomUserEditForm
)


# ─────────────────── helpers ───────────────────

def log_action(request, action, obj=None, details=''):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=obj.pk if obj else None,
        object_repr=str(obj) if obj else '',
        details=details,
        ip_address=get_client_ip(request),
    )


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def role_required(*roles):
    """Decorator factory: only allow users with specific roles."""
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                return HttpResponseForbidden(
                    render(request, '403.html', status=403)
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ─────────────────── dashboard ───────────────────

@login_required
def dashboard(request):
    user = request.user
    ctx = {}

    if user.role == 'initiator':
        ctx['my_requests'] = PurchaseRequest.objects.filter(
            requester=user
        ).order_by('-created_at')[:10]
        ctx['draft_count'] = PurchaseRequest.objects.filter(requester=user, status='draft').count()
        ctx['submitted_count'] = PurchaseRequest.objects.filter(requester=user, status='submitted').count()
        ctx['approved_count'] = PurchaseRequest.objects.filter(requester=user, status='approved').count()

    elif user.role == 'purchaser':
        ctx['pending_requests'] = PurchaseRequest.objects.filter(
            status='submitted'
        ).order_by('-created_at')[:10]
        ctx['approved_requests'] = PurchaseRequest.objects.filter(
            status='approved'
        ).order_by('-created_at')[:5]
        ctx['submitted_count'] = PurchaseRequest.objects.filter(status='submitted').count()
        ctx['approved_count'] = PurchaseRequest.objects.filter(status='approved').count()
        ctx['suppliers_count'] = Supplier.objects.filter(is_active=True).count()
        ctx['quotes_count'] = PriceQuote.objects.count()

    elif user.role == 'analyst':
        ctx['materials_count'] = Material.objects.filter(is_active=True).count()
        ctx['quotes_count'] = PriceQuote.objects.count()
        ctx['low_stock'] = [
            s for s in WarehouseStock.objects.select_related('material').all()
            if s.is_low
        ][:10]
        ctx['recent_quotes'] = PriceQuote.objects.select_related(
            'material', 'supplier'
        ).order_by('-quote_date')[:10]

    elif user.role == 'manager':
        ctx['pending_requests'] = PurchaseRequest.objects.filter(
            status='submitted'
        ).order_by('need_date')[:15]
        ctx['pending_count'] = PurchaseRequest.objects.filter(status='submitted').count()
        ctx['emergency_count'] = PurchaseRequest.objects.filter(
            status='submitted', criticality='emergency'
        ).count()
        ctx['recent_approved'] = PurchaseRequest.objects.filter(
            status__in=('approved', 'ordered', 'completed'), approved_by=user
        ).order_by('-approved_at')[:5]

    elif user.role == 'admin':
        ctx['users_count'] = CustomUser.objects.filter(is_active=True).count()
        ctx['materials_count'] = Material.objects.filter(is_active=True).count()
        ctx['suppliers_count'] = Supplier.objects.filter(is_active=True).count()
        ctx['requests_total'] = PurchaseRequest.objects.count()
        ctx['orders_total'] = PurchaseOrder.objects.count()
        ctx['recent_logs'] = AuditLog.objects.select_related('user').order_by('-timestamp')[:15]
        ctx['status_data_json'] = json.dumps({
            label: PurchaseRequest.objects.filter(status=s).count()
            for s, label in PurchaseRequest.STATUS_CHOICES
        })

    return render(request, 'dashboard.html', ctx)


# ─────────────────── catalog: categories ───────────────────

@login_required
def category_list(request):
    qs = Category.objects.all()
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    page_obj = paginate(request, qs, 25)
    return render(request, 'catalog/category_list.html', {
        'categories': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@login_required
def category_create(request):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        cat = form.save()
        log_action(request, 'Создана категория', cat)
        messages.success(request, f'Категория «{cat.name}» создана.')
        return redirect('category_list')
    return render(request, 'catalog/category_form.html', {
        'form': form, 'title': 'Новая категория',
        'cancel_url': reverse('category_list'),
    })


@login_required
def category_update(request, pk):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменена категория', cat)
        messages.success(request, 'Категория обновлена.')
        return redirect('category_list')
    return render(request, 'catalog/category_form.html', {
        'form': form, 'title': f'Редактировать: {cat.name}',
        'cancel_url': reverse('category_list'),
    })


@login_required
def category_delete(request, pk):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if cat.materials.exists():
            messages.error(request, f'Категория «{cat.name}» содержит материалы — удаление невозможно.')
        else:
            name = cat.name
            log_action(request, 'Удалена категория', details=name)
            cat.delete()
            messages.success(request, f'Категория «{name}» удалена.')
    return redirect('category_list')


# ─────────────────── catalog: materials ───────────────────

@login_required
def material_list(request):
    qs = Material.objects.select_related('category').filter(is_active=True)
    q = request.GET.get('q', '')
    cat_id = request.GET.get('category', '')
    crit = request.GET.get('criticality', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if crit:
        qs = qs.filter(criticality=crit)
    categories = Category.objects.all()
    page_obj = paginate(request, qs)
    return render(request, 'catalog/material_list.html', {
        'materials': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'q': q, 'cat_id': cat_id, 'crit': crit,
    })


@login_required
def material_detail(request, pk):
    mat = get_object_or_404(Material, pk=pk)
    stocks = mat.warehouse_stocks.all()
    quotes = mat.price_quotes.select_related('supplier').order_by('-quote_date')[:20]
    price_history = list(
        mat.price_quotes.values('quote_date', 'supplier__name', 'price')
        .order_by('quote_date')
    )
    return render(request, 'catalog/material_detail.html', {
        'material': mat,
        'stocks': stocks,
        'quotes': quotes,
        'price_history_json': json.dumps(
            [{'date': str(p['quote_date']), 'supplier': p['supplier__name'], 'price': float(p['price'])}
             for p in price_history]
        ),
    })


@login_required
def material_create(request):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    form = MaterialForm(request.POST or None)
    if form.is_valid():
        mat = form.save()
        log_action(request, 'Создан материал', mat)
        messages.success(request, f'Материал «{mat.name}» добавлен в каталог.')
        return redirect('material_detail', pk=mat.pk)
    return render(request, 'catalog/material_form.html', {
        'form': form, 'title': 'Новый материал / оборудование',
        'cancel_url': reverse('material_list'),
    })


@login_required
def material_update(request, pk):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    mat = get_object_or_404(Material, pk=pk)
    form = MaterialForm(request.POST or None, instance=mat)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменён материал', mat)
        messages.success(request, 'Данные материала обновлены.')
        return redirect('material_detail', pk=mat.pk)
    return render(request, 'catalog/material_form.html', {
        'form': form, 'title': f'Редактировать: {mat.name}',
        'cancel_url': reverse('material_detail', kwargs={'pk': mat.pk}),
    })


@login_required
def material_delete(request, pk):
    if not request.user.can_manage_catalog:
        return HttpResponseForbidden()
    mat = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        mat.is_active = False
        mat.save()
        log_action(request, 'Материал деактивирован', mat)
        messages.success(request, f'Материал «{mat.name}» деактивирован.')
    return redirect('material_list')


# ─────────────────── warehouse ───────────────────

@login_required
def warehouse_list(request):
    qs = WarehouseStock.objects.select_related('material', 'material__category').all()
    q = request.GET.get('q', '')
    show_low = request.GET.get('low', '')
    if q:
        qs = qs.filter(Q(material__name__icontains=q) | Q(material__code__icontains=q) | Q(location__icontains=q))
    stocks = list(qs)
    if show_low:
        stocks = [s for s in stocks if s.is_low]
    page_obj = paginate(request, stocks)
    return render(request, 'warehouse/stock_list.html', {
        'stocks': page_obj,
        'page_obj': page_obj,
        'q': q, 'show_low': show_low,
        'low_count': sum(1 for s in WarehouseStock.objects.all() if s.is_low),
    })


@login_required
def warehouse_create(request):
    if request.user.role not in ('admin', 'purchaser', 'analyst'):
        return HttpResponseForbidden()
    form = WarehouseStockForm(request.POST or None)
    if form.is_valid():
        stock = form.save()
        log_action(request, 'Создана запись склада', stock)
        messages.success(request, 'Складской остаток добавлен.')
        return redirect('warehouse_list')
    return render(request, 'warehouse/stock_form.html', {
        'form': form, 'title': 'Добавить остаток',
        'cancel_url': reverse('warehouse_list'),
    })


@login_required
def warehouse_update(request, pk):
    if request.user.role not in ('admin', 'purchaser', 'analyst'):
        return HttpResponseForbidden()
    stock = get_object_or_404(WarehouseStock, pk=pk)
    form = WarehouseStockForm(request.POST or None, instance=stock)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменён остаток склада', stock)
        messages.success(request, 'Остаток обновлён.')
        return redirect('warehouse_list')
    return render(request, 'warehouse/stock_form.html', {
        'form': form, 'title': f'Редактировать: {stock.material.name}',
        'stock': stock,
        'cancel_url': reverse('warehouse_list'),
    })


@login_required
def warehouse_delete(request, pk):
    if request.user.role not in ('admin', 'purchaser', 'analyst'):
        return HttpResponseForbidden()
    stock = get_object_or_404(WarehouseStock, pk=pk)
    if request.method == 'POST':
        log_action(request, 'Удалена запись склада', stock)
        stock.delete()
        messages.success(request, 'Запись склада удалена.')
    return redirect('warehouse_list')


# ─────────────────── purchase requests ───────────────────

@login_required
def request_list(request):
    user = request.user
    qs = PurchaseRequest.objects.select_related('requester').all()

    if user.role == 'initiator':
        qs = qs.filter(requester=user)
    elif user.role == 'manager':
        qs = qs.filter(status__in=('submitted', 'approved', 'rejected', 'ordered', 'completed'))

    status_filter = request.GET.get('status', '')
    crit_filter = request.GET.get('criticality', '')
    q = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if crit_filter:
        qs = qs.filter(criticality=crit_filter)
    if q:
        qs = qs.filter(Q(request_number__icontains=q) | Q(department__icontains=q))

    page_obj = paginate(request, qs)
    return render(request, 'requests/request_list.html', {
        'requests': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'crit_filter': crit_filter,
        'q': q,
        'status_choices': PurchaseRequest.STATUS_CHOICES,
    })


@login_required
def request_create(request):
    form = PurchaseRequestForm(request.POST or None)
    if form.is_valid():
        req = form.save(commit=False)
        req.requester = request.user
        if not req.request_number:
            year = timezone.now().year
            count = PurchaseRequest.objects.filter(created_at__year=year).count() + 1
            req.request_number = f"ЗК-{year}-{count:04d}"
        req.save()
        log_action(request, 'Создана заявка', req)
        messages.success(request, f'Заявка {req.request_number} создана. Добавьте позиции.')
        return redirect('request_detail', pk=req.pk)
    return render(request, 'requests/request_form.html', {
        'form': form, 'title': 'Новая заявка на закупку',
        'cancel_url': reverse('request_list'),
        'is_edit': False,
    })


@login_required
def request_edit(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if req.status != 'draft':
        messages.error(request, 'Редактировать можно только черновик.')
        return redirect('request_detail', pk=pk)
    if request.user.role == 'initiator' and req.requester != request.user:
        return HttpResponseForbidden()
    form = PurchaseRequestForm(request.POST or None, instance=req)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменена заявка', req)
        messages.success(request, 'Заявка обновлена.')
        return redirect('request_detail', pk=pk)
    return render(request, 'requests/request_form.html', {
        'form': form,
        'title': f'Редактировать заявку {req.request_number}',
        'cancel_url': reverse('request_detail', kwargs={'pk': pk}),
        'is_edit': True,
    })


@login_required
def request_detail(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    user = request.user

    # Access control
    if user.role == 'initiator' and req.requester != user:
        return HttpResponseForbidden()

    items = req.items.select_related('material', 'selected_quote', 'selected_quote__supplier').all()
    orders = req.orders.select_related('supplier').all()

    return render(request, 'requests/request_detail.html', {
        'request': req,
        'items': items,
        'orders': orders,
        'item_form': RequestItemForm(),
        'reject_form': RejectRequestForm(),
    })


@login_required
def request_add_item(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if req.status != 'draft':
        messages.error(request, 'Нельзя изменять заявку не в статусе Черновик.')
        return redirect('request_detail', pk=pk)
    if request.user.role == 'initiator' and req.requester != request.user:
        return HttpResponseForbidden()

    form = RequestItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.request = req
        # Check warehouse stock
        available = item.material.get_available_stock()
        item.qty_available_at_warehouse = min(available, item.qty_requested)
        item.qty_to_purchase = max(0, item.qty_requested - item.qty_available_at_warehouse)
        # Auto-set target price from best quote
        best = item.material.get_best_price()
        if best and not item.target_price:
            item.target_price = best
        item.save()
        log_action(request, 'Добавлена позиция в заявку', item, f'{item.material.name} × {item.qty_requested}')
        messages.success(request, f'Позиция «{item.material.name}» добавлена.')
    else:
        for field, errs in form.errors.items():
            for e in errs:
                messages.error(request, f'{field}: {e}')
    return redirect('request_detail', pk=pk)


@login_required
def request_delete_item(request, pk, item_pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    item = get_object_or_404(RequestItem, pk=item_pk, request=req)
    if req.status != 'draft':
        messages.error(request, 'Нельзя удалять позиции из заявки не в статусе Черновик.')
        return redirect('request_detail', pk=pk)
    if request.user.role == 'initiator' and req.requester != request.user:
        return HttpResponseForbidden()
    name = item.material.name
    item.delete()
    messages.success(request, f'Позиция «{name}» удалена.')
    return redirect('request_detail', pk=pk)


@login_required
def request_submit(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if request.user.role == 'initiator' and req.requester != request.user:
        return HttpResponseForbidden()
    if not req.can_be_submitted:
        messages.error(request, 'Заявка не может быть подана на рассмотрение.')
        return redirect('request_detail', pk=pk)
    req.status = 'submitted'
    req.save()
    log_action(request, 'Заявка подана на рассмотрение', req)
    messages.success(request, f'Заявка {req.request_number} отправлена на рассмотрение.')
    return redirect('request_detail', pk=pk)


@login_required
def request_approve(request, pk):
    if not request.user.can_approve:
        return HttpResponseForbidden()
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if not req.can_be_approved:
        messages.error(request, 'Заявка не находится на рассмотрении.')
        return redirect('request_detail', pk=pk)
    req.status = 'approved'
    req.approved_by = request.user
    req.approved_at = timezone.now()
    req.rejection_comment = ''
    req.save()
    log_action(request, 'Заявка утверждена', req)
    messages.success(request, f'Заявка {req.request_number} утверждена.')
    return redirect('request_detail', pk=pk)


@login_required
def request_reject(request, pk):
    if not request.user.can_approve:
        return HttpResponseForbidden()
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if not req.can_be_approved:
        messages.error(request, 'Заявка не находится на рассмотрении.')
        return redirect('request_detail', pk=pk)
    form = RejectRequestForm(request.POST)
    if form.is_valid():
        req.status = 'rejected'
        req.rejection_comment = form.cleaned_data['rejection_comment']
        req.save()
        log_action(request, 'Заявка отклонена', req, req.rejection_comment)
        messages.warning(request, f'Заявка {req.request_number} отклонена.')
    return redirect('request_detail', pk=pk)


@login_required
def request_return_to_draft(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    if req.requester != request.user and not request.user.can_approve:
        return HttpResponseForbidden()
    if req.status not in ('rejected',):
        messages.error(request, 'Только отклонённую заявку можно вернуть в черновик.')
        return redirect('request_detail', pk=pk)
    req.status = 'draft'
    req.rejection_comment = ''
    req.save()
    messages.info(request, 'Заявка возвращена в статус Черновик.')
    return redirect('request_detail', pk=pk)


# ─────────────────── market analysis / quote selection ───────────────────

@login_required
def market_analysis(request, item_pk):
    """Show comparison table for a specific request item."""
    item = get_object_or_404(RequestItem, pk=item_pk)
    req = item.request
    user = request.user

    if user.role == 'initiator':
        return HttpResponseForbidden()

    comparisons = item.get_comparison_quotes()

    if request.method == 'POST':
        form = SelectQuoteForm(request.POST)
        if form.is_valid():
            quote = get_object_or_404(PriceQuote, pk=form.cleaned_data['quote_id'])
            item.selected_quote = quote
            item.target_price = quote.price
            item.justification_for_choice = form.cleaned_data.get('justification', '')
            item.save()
            log_action(request, 'Выбрано ценовое предложение', item,
                       f'Поставщик: {quote.supplier.name}, цена: {quote.price}')
            messages.success(request, f'Выбрано предложение от {quote.supplier.name}.')
            return redirect('request_detail', pk=req.pk)
    else:
        form = SelectQuoteForm()

    return render(request, 'requests/quote_select.html', {
        'item': item,
        'request': req,
        'comparisons': comparisons,
        'form': form,
    })


# ─────────────────── suppliers ───────────────────

@login_required
def supplier_list(request):
    qs = Supplier.objects.all()
    q = request.GET.get('q', '')
    active_only = request.GET.get('active', '1')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(inn__icontains=q))
    if active_only == '1':
        qs = qs.filter(is_active=True)
    page_obj = paginate(request, qs)
    return render(request, 'suppliers/supplier_list.html', {
        'suppliers': page_obj,
        'page_obj': page_obj,
        'q': q, 'active_only': active_only,
    })


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    quotes = supplier.price_quotes.select_related('material').order_by('-quote_date')[:30]
    orders = supplier.orders.select_related('request').order_by('-created_at')[:10]
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'quotes': quotes,
        'orders': orders,
    })


@login_required
def supplier_create(request):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        s = form.save()
        log_action(request, 'Создан поставщик', s)
        messages.success(request, f'Поставщик «{s.name}» добавлен.')
        return redirect('supplier_detail', pk=s.pk)
    return render(request, 'suppliers/supplier_form.html', {
        'form': form, 'title': 'Новый поставщик',
        'cancel_url': reverse('supplier_list'),
    })


@login_required
def supplier_update(request, pk):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменён поставщик', supplier)
        messages.success(request, 'Данные поставщика обновлены.')
        return redirect('supplier_detail', pk=supplier.pk)
    return render(request, 'suppliers/supplier_form.html', {
        'form': form, 'title': f'Редактировать: {supplier.name}',
        'supplier': supplier,
        'cancel_url': reverse('supplier_detail', kwargs={'pk': supplier.pk}),
    })


@login_required
def supplier_delete(request, pk):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.is_active = False
        supplier.save()
        log_action(request, 'Поставщик деактивирован', supplier)
        messages.success(request, f'Поставщик «{supplier.name}» деактивирован.')
    return redirect('supplier_list')


# ─────────────────── price quotes ───────────────────

@login_required
def quote_list(request):
    qs = PriceQuote.objects.select_related('material', 'supplier').order_by('-quote_date')
    mat_id = request.GET.get('material', '')
    sup_id = request.GET.get('supplier', '')
    q = request.GET.get('q', '')
    if mat_id:
        qs = qs.filter(material_id=mat_id)
    if sup_id:
        qs = qs.filter(supplier_id=sup_id)
    if q:
        qs = qs.filter(
            Q(material__name__icontains=q) | Q(material__code__icontains=q) |
            Q(supplier__name__icontains=q)
        )
    materials = Material.objects.filter(is_active=True).order_by('name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    page_obj = paginate(request, qs)
    return render(request, 'suppliers/quote_list.html', {
        'quotes': page_obj,
        'page_obj': page_obj,
        'materials': materials,
        'suppliers': suppliers,
        'mat_id': mat_id, 'sup_id': sup_id, 'q': q,
    })


@login_required
def quote_create(request):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    material_id = request.GET.get('material')
    supplier_id = request.GET.get('supplier')
    material = Material.objects.filter(pk=material_id).first() if material_id else None
    supplier = Supplier.objects.filter(pk=supplier_id).first() if supplier_id else None

    initial = {}
    if material:
        initial['material'] = material
    if supplier:
        initial['supplier'] = supplier

    if material:
        cancel_url = reverse('material_detail', kwargs={'pk': material.pk})
    elif supplier:
        cancel_url = reverse('supplier_detail', kwargs={'pk': supplier.pk})
    else:
        cancel_url = reverse('quote_list')

    form = PriceQuoteForm(request.POST or None, material=material, supplier=supplier, initial=initial)
    if form.is_valid():
        quote = form.save()
        log_action(request, 'Добавлено ценовое предложение', quote,
                   f'{quote.supplier.name} / {quote.material.name}: {quote.price}')
        messages.success(request, 'Ценовое предложение добавлено.')
        if material:
            return redirect('material_detail', pk=material.pk)
        return redirect('quote_list')
    return render(request, 'suppliers/quote_form.html', {
        'form': form, 'title': 'Новое ценовое предложение',
        'material': material, 'supplier': supplier,
        'cancel_url': cancel_url,
    })


@login_required
def quote_update(request, pk):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    quote = get_object_or_404(PriceQuote, pk=pk)
    form = PriceQuoteForm(request.POST or None, instance=quote)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменено ценовое предложение', quote)
        messages.success(request, 'Ценовое предложение обновлено.')
        return redirect('material_detail', pk=quote.material.pk)
    return render(request, 'suppliers/quote_form.html', {
        'form': form, 'title': 'Редактировать ценовое предложение',
        'quote': quote,
        'cancel_url': reverse('material_detail', kwargs={'pk': quote.material.pk}),
    })


@login_required
def quote_delete(request, pk):
    if not request.user.can_manage_suppliers:
        return HttpResponseForbidden()
    quote = get_object_or_404(PriceQuote, pk=pk)
    if request.method == 'POST':
        mat_pk = quote.material.pk
        log_action(request, 'Удалено ценовое предложение', quote)
        quote.delete()
        messages.success(request, 'Ценовое предложение удалено.')
        return redirect('material_detail', pk=mat_pk)
    return redirect('quote_list')


# ─────────────────── orders ───────────────────

@login_required
def order_list(request):
    qs = PurchaseOrder.objects.select_related('supplier', 'request').all()
    status_f = request.GET.get('status', '')
    supplier_f = request.GET.get('supplier', '')
    q = request.GET.get('q', '')
    if status_f:
        qs = qs.filter(status=status_f)
    if supplier_f:
        qs = qs.filter(supplier_id=supplier_f)
    if q:
        qs = qs.filter(
            Q(order_number__icontains=q) |
            Q(request__request_number__icontains=q) |
            Q(supplier__name__icontains=q)
        )
    page_obj = paginate(request, qs)
    suppliers_all = Supplier.objects.filter(is_active=True).order_by('name')
    return render(request, 'orders/order_list.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'status_filter': status_f,
        'supplier_filter': supplier_f,
        'q': q,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'suppliers_all': suppliers_all,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_create(request, request_pk):
    if request.user.role not in ('purchaser', 'admin'):
        return HttpResponseForbidden()
    req = get_object_or_404(PurchaseRequest, pk=request_pk, status='approved')

    # Determine supplier from selected quotes
    suppliers_used = set()
    for item in req.items.filter(qty_to_purchase__gt=0):
        if item.selected_quote:
            suppliers_used.add(item.selected_quote.supplier)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.request = req
            order.created_by = request.user
            order.save()
            req.status = 'ordered'
            req.save()
            log_action(request, 'Создан заказ поставщику', order)
            messages.success(request, f'Заказ {order.order_number} создан.')
            return redirect('order_detail', pk=order.pk)
    else:
        initial = {
            'order_date': timezone.now().date(),
        }
        if len(suppliers_used) == 1:
            initial['supplier'] = next(iter(suppliers_used))
            # Calculate total from selected quotes
            total = sum(
                float(item.qty_to_purchase) * float(item.selected_quote.price)
                for item in req.items.filter(qty_to_purchase__gt=0, selected_quote__isnull=False)
            )
            initial['total_amount'] = round(total, 2)
        form = PurchaseOrderForm(initial=initial)

    return render(request, 'orders/order_form.html', {
        'form': form,
        'purchase_request': req,
        'suppliers_used': suppliers_used,
        'cancel_url': reverse('request_detail', kwargs={'pk': req.pk}),
    })


@login_required
def order_status_update(request, pk):
    if request.user.role not in ('purchaser', 'admin'):
        return HttpResponseForbidden()
    order = get_object_or_404(PurchaseOrder, pk=pk)
    new_status = request.POST.get('status')
    valid = [s for s, _ in PurchaseOrder.STATUS_CHOICES]
    if new_status in valid:
        old = order.status
        order.status = new_status
        if new_status == 'delivered' and not order.actual_delivery_date:
            order.actual_delivery_date = timezone.now().date()
            # Mark request as completed if all orders delivered
            if all(o.status == 'delivered' for o in order.request.orders.all()):
                order.request.status = 'completed'
                order.request.save()
        order.save()
        log_action(request, f'Статус заказа изменён: {old} → {new_status}', order)
        messages.success(request, f'Статус заказа изменён: {order.get_status_display()}.')
    return redirect('order_detail', pk=pk)


# ─────────────────── analytics ───────────────────

@login_required
def analytics_dashboard(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return HttpResponseForbidden()

    materials_with_shortage = []
    for stock in WarehouseStock.objects.select_related('material').all():
        if stock.is_low:
            materials_with_shortage.append(stock)

    # Requests by status
    status_data = {}
    for s, label in PurchaseRequest.STATUS_CHOICES:
        status_data[label] = PurchaseRequest.objects.filter(status=s).count()

    # Top materials by number of quotes
    top_materials = (
        Material.objects.filter(is_active=True)
        .annotate(q_count=Count('price_quotes'))
        .order_by('-q_count')[:10]
    )

    # Recent price changes
    recent_quotes = PriceQuote.objects.select_related('material', 'supplier').order_by('-quote_date')[:15]

    return render(request, 'analytics/dashboard.html', {
        'shortage_stocks': materials_with_shortage[:15],
        'status_data_json': json.dumps(status_data),
        'top_materials': top_materials,
        'recent_quotes': recent_quotes,
        'total_requests': PurchaseRequest.objects.count(),
        'total_orders': PurchaseOrder.objects.count(),
        'total_quotes': PriceQuote.objects.count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
    })


@login_required
def price_dynamics(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return HttpResponseForbidden()
    materials = Material.objects.filter(is_active=True, price_quotes__isnull=False).distinct().order_by('name')
    selected_material_id = request.GET.get('material', '')
    selected_material = None
    price_data_json = '[]'

    if selected_material_id:
        selected_material = Material.objects.filter(pk=selected_material_id).first()
        if selected_material:
            quotes = (
                PriceQuote.objects
                .filter(material=selected_material)
                .select_related('supplier')
                .order_by('quote_date')
            )
            # Group by supplier
            supplier_data = {}
            for q in quotes:
                sname = q.supplier.name
                if sname not in supplier_data:
                    supplier_data[sname] = []
                supplier_data[sname].append({
                    'date': str(q.quote_date),
                    'price': float(q.price),
                })
            price_data_json = json.dumps(supplier_data)

    return render(request, 'analytics/price_dynamics.html', {
        'materials': materials,
        'selected_material': selected_material,
        'selected_material_id': selected_material_id,
        'price_data_json': price_data_json,
    })


@login_required
def shortage_report(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return HttpResponseForbidden()

    # Find all request items where qty_to_purchase > 0 (shortage from warehouse)
    shortage_items = RequestItem.objects.filter(
        qty_to_purchase__gt=0,
        request__status__in=('submitted', 'approved', 'ordered')
    ).select_related('request', 'material', 'material__category').order_by(
        'request__criticality', 'request__need_date'
    )

    # Also find materials below min stock
    low_stocks = [s for s in WarehouseStock.objects.select_related('material').all() if s.is_low]

    return render(request, 'analytics/shortage_report.html', {
        'shortage_items': shortage_items,
        'low_stocks': low_stocks,
    })


@login_required
def reports(request):
    if request.user.role not in ('analyst', 'manager', 'admin'):
        return HttpResponseForbidden()

    # Summary statistics
    total_approved_amount = sum(
        r.get_total_target_amount()
        for r in PurchaseRequest.objects.filter(status__in=('approved', 'ordered', 'completed'))
    )

    # Orders by status
    orders_by_status = {}
    for s, label in PurchaseOrder.STATUS_CHOICES:
        orders_by_status[label] = PurchaseOrder.objects.filter(status=s).count()

    # Top suppliers by order count
    top_suppliers = (
        Supplier.objects
        .annotate(order_count=Count('orders'))
        .filter(order_count__gt=0)
        .order_by('-order_count')[:10]
    )

    # Requests created per month (last 6 months)
    from django.db.models.functions import TruncMonth
    monthly = (
        PurchaseRequest.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    return render(request, 'analytics/reports.html', {
        'total_approved_amount': total_approved_amount,
        'orders_by_status': json.dumps(orders_by_status),
        'top_suppliers': top_suppliers,
        'monthly_json': json.dumps([
            {'month': str(m['month'])[:7], 'count': m['count']}
            for m in monthly
        ]),
        'requests_total': PurchaseRequest.objects.count(),
        'orders_total': PurchaseOrder.objects.count(),
        'emergency_ratio': PurchaseRequest.objects.filter(criticality='emergency').count(),
    })


# ─────────────────── admin panel ───────────────────

@login_required
def user_list(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    qs = CustomUser.objects.all().order_by('role', 'last_name')
    q = request.GET.get('q', '')
    role_f = request.GET.get('role', '')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(department__icontains=q))
    if role_f:
        qs = qs.filter(role=role_f)
    page_obj = paginate(request, qs, 25)
    return render(request, 'admin_panel/user_list.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'q': q, 'role_f': role_f,
        'role_choices': CustomUser.ROLE_CHOICES,
    })


@login_required
def user_create(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    form = CustomUserCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        log_action(request, 'Создан пользователь', user)
        messages.success(request, f'Пользователь {user.username} создан.')
        return redirect('user_list')
    return render(request, 'admin_panel/user_form.html', {
        'form': form, 'title': 'Новый пользователь',
        'cancel_url': reverse('user_list'),
    })


@login_required
def user_update(request, pk):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    user_obj = get_object_or_404(CustomUser, pk=pk)
    form = CustomUserEditForm(request.POST or None, instance=user_obj)
    if form.is_valid():
        form.save()
        log_action(request, 'Изменён пользователь', user_obj)
        messages.success(request, 'Данные пользователя обновлены.')
        return redirect('user_list')
    return render(request, 'admin_panel/user_form.html', {
        'form': form, 'title': f'Редактировать: {user_obj.username}',
        'user_obj': user_obj,
        'cancel_url': reverse('user_list'),
    })


@login_required
def audit_log_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    q = request.GET.get('q', '')
    model_f = request.GET.get('model', '')
    if q:
        logs = logs.filter(Q(action__icontains=q) | Q(object_repr__icontains=q))
    if model_f:
        logs = logs.filter(model_name=model_f)
    model_names = AuditLog.objects.values_list('model_name', flat=True).distinct()
    return render(request, 'admin_panel/audit_log.html', {
        'logs': logs[:200],
        'q': q,
        'model_f': model_f,
        'model_names': model_names,
    })
