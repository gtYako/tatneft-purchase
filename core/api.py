from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
import json

from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog
)
from .serializers import (
    UserSerializer, UserShortSerializer, UserCreateSerializer, UserEditSerializer,
    CategorySerializer, MaterialSerializer, MaterialShortSerializer,
    WarehouseStockSerializer, SupplierSerializer, SupplierShortSerializer,
    PriceQuoteSerializer, PurchaseRequestSerializer, PurchaseRequestListSerializer,
    RequestItemSerializer, PurchaseOrderSerializer, AuditLogSerializer,
    ComparisonQuoteSerializer,
)


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def log_action(request, action, obj=None, details=''):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=obj.__class__.__name__ if obj else '',
        object_id=obj.pk if obj else None,
        object_repr=str(obj) if obj else '',
        details=details,
        ip_address=ip,
    )


# ─────────────────── AUTH ───────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_view(request):
    return Response({'csrfToken': get_token(request)})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': 'Неверные логин или пароль'}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'detail': 'ok'})


@api_view(['GET'])
def me_view(request):
    return Response(UserSerializer(request.user).data)


# ─────────────────── CATEGORIES ───────────────────

class CategoryListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Category.objects.all()
        q = request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        pag = StandardPagination()
        page = pag.paginate_queryset(qs.order_by('name'), request)
        return pag.get_paginated_response(CategorySerializer(page, many=True).data)

    def post(self, request):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        ser = CategorySerializer(data=request.data)
        if ser.is_valid():
            cat = ser.save()
            log_action(request, 'Создана категория', cat)
            return Response(CategorySerializer(cat).data, status=201)
        return Response(ser.errors, status=400)


class CategoryDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        cat = self._get(pk)
        if cat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        return Response(CategorySerializer(cat).data)

    def put(self, request, pk):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        cat = self._get(pk)
        if cat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        ser = CategorySerializer(cat, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменена категория', cat)
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        cat = self._get(pk)
        if cat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        if cat.materials.exists():
            return Response({'detail': 'Категория содержит материалы — удаление невозможно'}, status=400)
        log_action(request, 'Удалена категория', details=cat.name)
        cat.delete()
        return Response(status=204)


# ─────────────────── MATERIALS ───────────────────

class MaterialListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        pag = StandardPagination()
        page = pag.paginate_queryset(qs, request)
        return pag.get_paginated_response(MaterialSerializer(page, many=True).data)

    def post(self, request):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        ser = MaterialSerializer(data=request.data)
        if ser.is_valid():
            mat = ser.save()
            log_action(request, 'Создан материал', mat)
            return Response(MaterialSerializer(mat).data, status=201)
        return Response(ser.errors, status=400)


class MaterialDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return Material.objects.select_related('category').get(pk=pk)
        except Material.DoesNotExist:
            return None

    def get(self, request, pk):
        mat = self._get(pk)
        if mat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        data = MaterialSerializer(mat).data
        data['stocks'] = WarehouseStockSerializer(mat.warehouse_stocks.all(), many=True).data
        quotes_qs = mat.price_quotes.select_related('supplier').order_by('-quote_date')[:20]
        data['quotes'] = PriceQuoteSerializer(quotes_qs, many=True).data
        price_history = list(
            mat.price_quotes.values('quote_date', 'supplier__name', 'price').order_by('quote_date')
        )
        data['price_history'] = [
            {'date': str(p['quote_date']), 'supplier': p['supplier__name'], 'price': float(p['price'])}
            for p in price_history
        ]
        return Response(data)

    def put(self, request, pk):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        mat = self._get(pk)
        if mat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        ser = MaterialSerializer(mat, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменён материал', mat)
            return Response(MaterialSerializer(mat).data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        if not request.user.can_manage_catalog:
            return Response({'detail': 'Нет прав'}, status=403)
        mat = self._get(pk)
        if mat is None:
            return Response({'detail': 'Не найдено'}, status=404)
        mat.is_active = False
        mat.save()
        log_action(request, 'Материал деактивирован', mat)
        return Response(status=204)


# ─────────────────── WAREHOUSE ───────────────────

class WarehouseListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WarehouseStock.objects.select_related('material', 'material__category').all()
        q = request.GET.get('q', '')
        show_low = request.GET.get('low', '')
        if q:
            qs = qs.filter(
                Q(material__name__icontains=q) | Q(material__code__icontains=q) | Q(location__icontains=q)
            )
        stocks = list(qs)
        if show_low:
            stocks = [s for s in stocks if s.is_low]
        pag = StandardPagination()
        page = pag.paginate_queryset(stocks, request)
        low_count = sum(1 for s in WarehouseStock.objects.all() if s.is_low)
        response = pag.get_paginated_response(WarehouseStockSerializer(page, many=True).data)
        response.data['low_count'] = low_count
        return response

    def post(self, request):
        if request.user.role not in ('admin', 'purchaser', 'analyst'):
            return Response({'detail': 'Нет прав'}, status=403)
        ser = WarehouseStockSerializer(data=request.data)
        if ser.is_valid():
            stock = ser.save()
            log_action(request, 'Создана запись склада', stock)
            return Response(WarehouseStockSerializer(stock).data, status=201)
        return Response(ser.errors, status=400)


class WarehouseDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return WarehouseStock.objects.select_related('material').get(pk=pk)
        except WarehouseStock.DoesNotExist:
            return None

    def get(self, request, pk):
        stock = self._get(pk)
        if stock is None:
            return Response({'detail': 'Не найдено'}, status=404)
        return Response(WarehouseStockSerializer(stock).data)

    def put(self, request, pk):
        if request.user.role not in ('admin', 'purchaser', 'analyst'):
            return Response({'detail': 'Нет прав'}, status=403)
        stock = self._get(pk)
        if stock is None:
            return Response({'detail': 'Не найдено'}, status=404)
        ser = WarehouseStockSerializer(stock, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменён остаток склада', stock)
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        if request.user.role not in ('admin', 'purchaser', 'analyst'):
            return Response({'detail': 'Нет прав'}, status=403)
        stock = self._get(pk)
        if stock is None:
            return Response({'detail': 'Не найдено'}, status=404)
        log_action(request, 'Удалена запись склада', stock)
        stock.delete()
        return Response(status=204)


# ─────────────────── SUPPLIERS ───────────────────

class SupplierListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Supplier.objects.all()
        q = request.GET.get('q', '')
        active_only = request.GET.get('active', '1')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(inn__icontains=q))
        if active_only == '1':
            qs = qs.filter(is_active=True)
        pag = StandardPagination()
        page = pag.paginate_queryset(qs, request)
        return pag.get_paginated_response(SupplierSerializer(page, many=True).data)

    def post(self, request):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        ser = SupplierSerializer(data=request.data)
        if ser.is_valid():
            s = ser.save()
            log_action(request, 'Создан поставщик', s)
            return Response(SupplierSerializer(s).data, status=201)
        return Response(ser.errors, status=400)


class SupplierDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return Supplier.objects.get(pk=pk)
        except Supplier.DoesNotExist:
            return None

    def get(self, request, pk):
        supplier = self._get(pk)
        if supplier is None:
            return Response({'detail': 'Не найдено'}, status=404)
        data = SupplierSerializer(supplier).data
        quotes = supplier.price_quotes.select_related('material').order_by('-quote_date')[:30]
        data['quotes'] = PriceQuoteSerializer(quotes, many=True).data
        orders = supplier.orders.select_related('request').order_by('-created_at')[:10]
        data['orders'] = PurchaseOrderSerializer(orders, many=True).data
        return Response(data)

    def put(self, request, pk):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        supplier = self._get(pk)
        if supplier is None:
            return Response({'detail': 'Не найдено'}, status=404)
        ser = SupplierSerializer(supplier, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменён поставщик', supplier)
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        supplier = self._get(pk)
        if supplier is None:
            return Response({'detail': 'Не найдено'}, status=404)
        supplier.is_active = False
        supplier.save()
        log_action(request, 'Поставщик деактивирован', supplier)
        return Response(status=204)


# ─────────────────── PRICE QUOTES ───────────────────

class QuoteListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        pag = StandardPagination()
        page = pag.paginate_queryset(qs, request)
        data = pag.get_paginated_response(PriceQuoteSerializer(page, many=True).data)
        data.data['materials'] = MaterialShortSerializer(
            Material.objects.filter(is_active=True).order_by('name'), many=True
        ).data
        data.data['suppliers'] = SupplierShortSerializer(
            Supplier.objects.filter(is_active=True).order_by('name'), many=True
        ).data
        return data

    def post(self, request):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        ser = PriceQuoteSerializer(data=request.data)
        if ser.is_valid():
            quote = ser.save()
            log_action(request, 'Добавлено ценовое предложение', quote,
                       f'{quote.supplier.name} / {quote.material.name}: {quote.price}')
            return Response(PriceQuoteSerializer(quote).data, status=201)
        return Response(ser.errors, status=400)


class QuoteDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return PriceQuote.objects.select_related('material', 'supplier').get(pk=pk)
        except PriceQuote.DoesNotExist:
            return None

    def get(self, request, pk):
        quote = self._get(pk)
        if quote is None:
            return Response({'detail': 'Не найдено'}, status=404)
        return Response(PriceQuoteSerializer(quote).data)

    def put(self, request, pk):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        quote = self._get(pk)
        if quote is None:
            return Response({'detail': 'Не найдено'}, status=404)
        ser = PriceQuoteSerializer(quote, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменено ценовое предложение', quote)
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        if not request.user.can_manage_suppliers:
            return Response({'detail': 'Нет прав'}, status=403)
        quote = self._get(pk)
        if quote is None:
            return Response({'detail': 'Не найдено'}, status=404)
        log_action(request, 'Удалено ценовое предложение', quote)
        quote.delete()
        return Response(status=204)


# ─────────────────── PURCHASE REQUESTS ───────────────────

class RequestListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = PurchaseRequest.objects.select_related('requester').all()
        if user.role == 'initiator':
            qs = qs.filter(requester=user)
        elif user.role == 'manager':
            qs = qs.filter(status__in=('submitted', 'approved', 'rejected', 'ordered', 'completed'))
        status_f = request.GET.get('status', '')
        crit_f = request.GET.get('criticality', '')
        q = request.GET.get('q', '')
        if status_f:
            qs = qs.filter(status=status_f)
        if crit_f:
            qs = qs.filter(criticality=crit_f)
        if q:
            qs = qs.filter(Q(request_number__icontains=q) | Q(department__icontains=q))
        pag = StandardPagination()
        page = pag.paginate_queryset(qs, request)
        return pag.get_paginated_response(PurchaseRequestListSerializer(page, many=True).data)

    def post(self, request):
        ser = PurchaseRequestSerializer(data=request.data)
        if ser.is_valid():
            req = ser.save(requester=request.user)
            log_action(request, 'Создана заявка', req)
            return Response(PurchaseRequestSerializer(req).data, status=201)
        return Response(ser.errors, status=400)


class RequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return PurchaseRequest.objects.prefetch_related(
                'items__material', 'items__selected_quote__supplier', 'orders__supplier'
            ).get(pk=pk)
        except PurchaseRequest.DoesNotExist:
            return None

    def get(self, request, pk):
        req = self._get(pk)
        if req is None:
            return Response({'detail': 'Не найдено'}, status=404)
        if request.user.role == 'initiator' and req.requester != request.user:
            return Response({'detail': 'Нет доступа'}, status=403)
        data = PurchaseRequestSerializer(req).data
        data['orders'] = PurchaseOrderSerializer(req.orders.all(), many=True).data
        return Response(data)

    def put(self, request, pk):
        req = self._get(pk)
        if req is None:
            return Response({'detail': 'Не найдено'}, status=404)
        if req.status != 'draft':
            return Response({'detail': 'Редактировать можно только черновик'}, status=400)
        if request.user.role == 'initiator' and req.requester != request.user:
            return Response({'detail': 'Нет доступа'}, status=403)
        ser = PurchaseRequestSerializer(req, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменена заявка', req)
            return Response(PurchaseRequestSerializer(req).data)
        return Response(ser.errors, status=400)


@api_view(['POST'])
def request_submit(request, pk):
    try:
        req = PurchaseRequest.objects.get(pk=pk)
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if request.user.role == 'initiator' and req.requester != request.user:
        return Response({'detail': 'Нет доступа'}, status=403)
    if not req.can_be_submitted:
        return Response({'detail': 'Заявка не может быть подана — добавьте позиции или проверьте статус'}, status=400)
    req.status = 'submitted'
    req.save()
    log_action(request, 'Заявка подана на рассмотрение', req)
    return Response(PurchaseRequestSerializer(req).data)


@api_view(['POST'])
def request_approve(request, pk):
    if not request.user.can_approve:
        return Response({'detail': 'Нет прав'}, status=403)
    try:
        req = PurchaseRequest.objects.get(pk=pk)
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if not req.can_be_approved:
        return Response({'detail': 'Заявка не находится на рассмотрении'}, status=400)
    req.status = 'approved'
    req.approved_by = request.user
    req.approved_at = timezone.now()
    req.rejection_comment = ''
    req.save()
    log_action(request, 'Заявка утверждена', req)
    return Response(PurchaseRequestSerializer(req).data)


@api_view(['POST'])
def request_reject(request, pk):
    if not request.user.can_approve:
        return Response({'detail': 'Нет прав'}, status=403)
    try:
        req = PurchaseRequest.objects.get(pk=pk)
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if not req.can_be_approved:
        return Response({'detail': 'Заявка не находится на рассмотрении'}, status=400)
    comment = request.data.get('rejection_comment', '')
    if not comment:
        return Response({'detail': 'Укажите причину отклонения'}, status=400)
    req.status = 'rejected'
    req.rejection_comment = comment
    req.save()
    log_action(request, 'Заявка отклонена', req, comment)
    return Response(PurchaseRequestSerializer(req).data)


@api_view(['POST'])
def request_return_to_draft(request, pk):
    try:
        req = PurchaseRequest.objects.get(pk=pk)
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if req.requester != request.user and not request.user.can_approve:
        return Response({'detail': 'Нет доступа'}, status=403)
    if req.status != 'rejected':
        return Response({'detail': 'Только отклонённую заявку можно вернуть в черновик'}, status=400)
    req.status = 'draft'
    req.rejection_comment = ''
    req.save()
    return Response(PurchaseRequestSerializer(req).data)


@api_view(['POST'])
def request_add_item(request, pk):
    try:
        req = PurchaseRequest.objects.get(pk=pk)
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if req.status != 'draft':
        return Response({'detail': 'Нельзя изменять заявку не в статусе Черновик'}, status=400)
    if request.user.role == 'initiator' and req.requester != request.user:
        return Response({'detail': 'Нет доступа'}, status=403)
    material_id = request.data.get('material')
    qty = request.data.get('qty_requested')
    notes = request.data.get('notes', '')
    try:
        material = Material.objects.get(pk=material_id, is_active=True)
    except Material.DoesNotExist:
        return Response({'detail': 'Материал не найден'}, status=400)
    try:
        qty_val = float(qty)
        if qty_val <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response({'detail': 'Некорректное количество'}, status=400)

    from decimal import Decimal
    qty_dec = Decimal(str(qty_val))
    available = material.get_available_stock()
    qty_avail = min(Decimal(str(available)), qty_dec)
    qty_purchase = max(Decimal('0'), qty_dec - qty_avail)
    best = material.get_best_price()

    item = RequestItem.objects.create(
        request=req,
        material=material,
        qty_requested=qty_dec,
        qty_available_at_warehouse=qty_avail,
        qty_to_purchase=qty_purchase,
        target_price=best,
        notes=notes,
    )
    log_action(request, 'Добавлена позиция в заявку', item, f'{material.name} × {qty_val}')
    return Response(RequestItemSerializer(item).data, status=201)


@api_view(['DELETE'])
def request_delete_item(request, pk, item_pk):
    try:
        req = PurchaseRequest.objects.get(pk=pk)
        item = RequestItem.objects.get(pk=item_pk, request=req)
    except (PurchaseRequest.DoesNotExist, RequestItem.DoesNotExist):
        return Response({'detail': 'Не найдено'}, status=404)
    if req.status != 'draft':
        return Response({'detail': 'Нельзя удалять позиции из заявки не в статусе Черновик'}, status=400)
    if request.user.role == 'initiator' and req.requester != request.user:
        return Response({'detail': 'Нет доступа'}, status=403)
    item.delete()
    return Response(status=204)


@api_view(['GET'])
def item_analyse(request, item_pk):
    if request.user.role == 'initiator':
        return Response({'detail': 'Нет доступа'}, status=403)
    try:
        item = RequestItem.objects.select_related('request', 'material').get(pk=item_pk)
    except RequestItem.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    comparisons = item.get_comparison_quotes()
    return Response({
        'item': RequestItemSerializer(item).data,
        'request_id': item.request.pk,
        'request_number': item.request.request_number,
        'comparisons': ComparisonQuoteSerializer(comparisons, many=True).data,
    })


@api_view(['POST'])
def item_select_quote(request, item_pk):
    if request.user.role == 'initiator':
        return Response({'detail': 'Нет доступа'}, status=403)
    try:
        item = RequestItem.objects.select_related('request').get(pk=item_pk)
    except RequestItem.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    quote_id = request.data.get('quote_id')
    justification = request.data.get('justification', '')
    try:
        quote = PriceQuote.objects.select_related('supplier').get(pk=quote_id)
    except PriceQuote.DoesNotExist:
        return Response({'detail': 'Ценовое предложение не найдено'}, status=400)
    item.selected_quote = quote
    item.target_price = quote.price
    item.justification_for_choice = justification
    item.save()
    log_action(request, 'Выбрано ценовое предложение', item,
               f'Поставщик: {quote.supplier.name}, цена: {quote.price}')
    return Response(RequestItemSerializer(item).data)


# ─────────────────── ORDERS ───────────────────

class OrderListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        pag = StandardPagination()
        page = pag.paginate_queryset(qs, request)
        resp = pag.get_paginated_response(PurchaseOrderSerializer(page, many=True).data)
        resp.data['suppliers_all'] = SupplierShortSerializer(
            Supplier.objects.filter(is_active=True).order_by('name'), many=True
        ).data
        return resp

    def post(self, request):
        if request.user.role not in ('purchaser', 'admin'):
            return Response({'detail': 'Нет прав'}, status=403)
        request_pk = request.data.get('request')
        try:
            purchase_request = PurchaseRequest.objects.get(pk=request_pk, status='approved')
        except PurchaseRequest.DoesNotExist:
            return Response({'detail': 'Заявка не найдена или не в статусе Утверждена'}, status=400)
        ser = PurchaseOrderSerializer(data=request.data)
        if ser.is_valid():
            order = ser.save(created_by=request.user)
            purchase_request.status = 'ordered'
            purchase_request.save()
            log_action(request, 'Создан заказ поставщику', order)
            return Response(PurchaseOrderSerializer(order).data, status=201)
        return Response(ser.errors, status=400)


class OrderDetail(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return PurchaseOrder.objects.select_related('supplier', 'request').get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self._get(pk)
        if order is None:
            return Response({'detail': 'Не найдено'}, status=404)
        return Response(PurchaseOrderSerializer(order).data)


@api_view(['POST'])
def order_status_update(request, pk):
    if request.user.role not in ('purchaser', 'admin'):
        return Response({'detail': 'Нет прав'}, status=403)
    try:
        order = PurchaseOrder.objects.select_related('request').get(pk=pk)
    except PurchaseOrder.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    new_status = request.data.get('status')
    valid = [s for s, _ in PurchaseOrder.STATUS_CHOICES]
    if new_status not in valid:
        return Response({'detail': 'Некорректный статус'}, status=400)
    old = order.status
    order.status = new_status
    if new_status == 'delivered' and not order.actual_delivery_date:
        order.actual_delivery_date = timezone.now().date()
        if all(o.status == 'delivered' for o in order.request.orders.all()):
            order.request.status = 'completed'
            order.request.save()
    order.save()
    log_action(request, f'Статус заказа изменён: {old} → {new_status}', order)
    return Response(PurchaseOrderSerializer(order).data)


# ─────────────────── ANALYTICS ───────────────────

@api_view(['GET'])
def analytics_dashboard(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return Response({'detail': 'Нет доступа'}, status=403)

    shortage = [s for s in WarehouseStock.objects.select_related('material').all() if s.is_low]
    status_data = {label: PurchaseRequest.objects.filter(status=s).count()
                   for s, label in PurchaseRequest.STATUS_CHOICES}
    top_materials = (
        Material.objects.filter(is_active=True)
        .annotate(q_count=Count('price_quotes'))
        .order_by('-q_count')[:10]
    )
    recent_quotes = PriceQuote.objects.select_related('material', 'supplier').order_by('-quote_date')[:15]

    return Response({
        'shortage_stocks': WarehouseStockSerializer(shortage[:15], many=True).data,
        'status_data': status_data,
        'top_materials': [{'name': m.name, 'code': m.code, 'q_count': m.q_count} for m in top_materials],
        'recent_quotes': PriceQuoteSerializer(recent_quotes, many=True).data,
        'total_requests': PurchaseRequest.objects.count(),
        'total_orders': PurchaseOrder.objects.count(),
        'total_quotes': PriceQuote.objects.count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
    })


@api_view(['GET'])
def analytics_price_dynamics(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return Response({'detail': 'Нет доступа'}, status=403)
    materials = Material.objects.filter(is_active=True, price_quotes__isnull=False).distinct().order_by('name')
    selected_id = request.GET.get('material', '')
    price_data = {}
    selected = None
    if selected_id:
        try:
            selected = Material.objects.get(pk=selected_id)
            quotes = PriceQuote.objects.filter(material=selected).select_related('supplier').order_by('quote_date')
            for q in quotes:
                sname = q.supplier.name
                if sname not in price_data:
                    price_data[sname] = []
                price_data[sname].append({'date': str(q.quote_date), 'price': float(q.price)})
        except Material.DoesNotExist:
            pass
    return Response({
        'materials': MaterialShortSerializer(materials, many=True).data,
        'selected_material': MaterialShortSerializer(selected).data if selected else None,
        'price_data': price_data,
    })


@api_view(['GET'])
def analytics_shortage(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return Response({'detail': 'Нет доступа'}, status=403)
    shortage_items = RequestItem.objects.filter(
        qty_to_purchase__gt=0,
        request__status__in=('submitted', 'approved', 'ordered')
    ).select_related('request', 'material', 'material__category').order_by(
        'request__criticality', 'request__need_date'
    )
    low_stocks = [s for s in WarehouseStock.objects.select_related('material').all() if s.is_low]
    return Response({
        'shortage_items': RequestItemSerializer(shortage_items, many=True).data,
        'low_stocks': WarehouseStockSerializer(low_stocks, many=True).data,
    })


@api_view(['GET'])
def analytics_reports(request):
    if request.user.role not in ('analyst', 'manager', 'admin', 'purchaser'):
        return Response({'detail': 'Нет доступа'}, status=403)

    orders_by_status = {label: PurchaseOrder.objects.filter(status=s).count()
                        for s, label in PurchaseOrder.STATUS_CHOICES}

    top_suppliers = (
        Supplier.objects.annotate(
            orders_count=Count('orders', distinct=True),
            quotes_count=Count('pricequote', distinct=True),
        ).order_by('-orders_count')[:10]
    )

    monthly_requests = (
        PurchaseRequest.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    return Response({
        'total_requests': PurchaseRequest.objects.count(),
        'approved_requests': PurchaseRequest.objects.filter(status__in=('approved', 'ordered', 'completed')).count(),
        'total_orders': PurchaseOrder.objects.count(),
        'delivered_orders': PurchaseOrder.objects.filter(status='delivered').count(),
        'orders_by_status': orders_by_status,
        'top_suppliers': [
            {
                'id': s.id,
                'name': s.name,
                'orders_count': s.orders_count,
                'quotes_count': s.quotes_count,
                'rating': float(s.rating),
                'delivery_reliability': float(s.delivery_reliability),
            }
            for s in top_suppliers
        ],
        'monthly_requests': [
            {'month': str(m['month'])[:7], 'count': m['count'], 'total': None}
            for m in monthly_requests
        ],
    })


# ─────────────────── ADMIN PANEL ───────────────────

@api_view(['GET', 'POST'])
def user_list_create(request):
    if request.user.role != 'admin':
        return Response({'detail': 'Нет прав'}, status=403)
    if request.method == 'GET':
        qs = CustomUser.objects.all().order_by('role', 'last_name')
        q = request.GET.get('q', '')
        role_f = request.GET.get('role', '')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) |
                           Q(last_name__icontains=q) | Q(department__icontains=q))
        if role_f:
            qs = qs.filter(role=role_f)
        pag = StandardPagination()
        pag.page_size = 25
        page = pag.paginate_queryset(qs, request)
        resp = pag.get_paginated_response(UserSerializer(page, many=True).data)
        resp.data['role_choices'] = CustomUser.ROLE_CHOICES
        return resp
    else:
        ser = UserCreateSerializer(data=request.data)
        if ser.is_valid():
            user = ser.save()
            log_action(request, 'Создан пользователь', user)
            return Response(UserSerializer(user).data, status=201)
        return Response(ser.errors, status=400)


@api_view(['GET', 'PUT'])
def user_detail(request, pk):
    if request.user.role != 'admin':
        return Response({'detail': 'Нет прав'}, status=403)
    try:
        user_obj = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'detail': 'Не найдено'}, status=404)
    if request.method == 'GET':
        return Response(UserSerializer(user_obj).data)
    else:
        ser = UserEditSerializer(user_obj, data=request.data)
        if ser.is_valid():
            ser.save()
            log_action(request, 'Изменён пользователь', user_obj)
            return Response(UserSerializer(user_obj).data)
        return Response(ser.errors, status=400)


@api_view(['GET'])
def audit_log_list(request):
    if request.user.role != 'admin':
        return Response({'detail': 'Нет прав'}, status=403)
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    q = request.GET.get('q', '')
    model_f = request.GET.get('model', '')
    if q:
        logs = logs.filter(Q(action__icontains=q) | Q(object_repr__icontains=q))
    if model_f:
        logs = logs.filter(model_name=model_f)
    pag = StandardPagination()
    page = pag.paginate_queryset(logs, request)
    resp = pag.get_paginated_response(AuditLogSerializer(page, many=True).data)
    resp.data['model_names'] = list(
        AuditLog.objects.values_list('model_name', flat=True).distinct()
    )
    return resp


# ─────────────────── HELPERS ───────────────────

@api_view(['GET'])
def materials_all(request):
    """All active materials for select dropdowns."""
    qs = Material.objects.filter(is_active=True).order_by('name')
    return Response(MaterialShortSerializer(qs, many=True).data)


@api_view(['GET'])
def suppliers_all(request):
    """All active suppliers for select dropdowns."""
    qs = Supplier.objects.filter(is_active=True).order_by('name')
    return Response(SupplierShortSerializer(qs, many=True).data)


@api_view(['GET'])
def categories_all(request):
    """All categories for select dropdowns."""
    qs = Category.objects.all().order_by('name')
    return Response(CategorySerializer(qs, many=True).data)


@api_view(['GET'])
def order_prefill(request, request_pk):
    """Prefill data for creating a new order from a purchase request."""
    if request.user.role not in ('purchaser', 'admin'):
        return Response({'detail': 'Нет прав'}, status=403)
    try:
        req = PurchaseRequest.objects.get(pk=request_pk, status='approved')
    except PurchaseRequest.DoesNotExist:
        return Response({'detail': 'Заявка не найдена или не в статусе Утверждена'}, status=404)
    suppliers_used = set()
    total = 0.0
    for item in req.items.filter(qty_to_purchase__gt=0):
        if item.selected_quote:
            suppliers_used.add(item.selected_quote.supplier)
            total += float(item.qty_to_purchase) * float(item.selected_quote.price)
    return Response({
        'request_number': req.request_number,
        'suppliers': SupplierShortSerializer(list(suppliers_used), many=True).data,
        'total_amount': round(total, 2),
        'order_date': str(timezone.now().date()),
    })
