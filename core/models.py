from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum, Min, Max


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('initiator', 'Инициатор (Производство)'),
        ('purchaser', 'Закупщик (Снабжение)'),
        ('analyst', 'Аналитик'),
        ('manager', 'Руководитель'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='initiator', verbose_name='Роль')
    department = models.CharField(max_length=200, blank=True, verbose_name='Подразделение')
    position = models.CharField(max_length=200, blank=True, verbose_name='Должность')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_full_name_or_username(self):
        full = super().get_full_name()
        return full if full else self.username

    @property
    def is_initiator(self):
        return self.role == 'initiator'

    @property
    def is_purchaser(self):
        return self.role == 'purchaser'

    @property
    def is_analyst(self):
        return self.role == 'analyst'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def can_manage_catalog(self):
        return self.role in ('admin', 'purchaser')

    @property
    def can_manage_suppliers(self):
        return self.role in ('admin', 'purchaser')

    @property
    def can_approve(self):
        return self.role in ('manager', 'admin')


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_materials_count(self):
        return self.materials.filter(is_active=True).count()


class Material(models.Model):
    CRITICALITY_CHOICES = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
        ('critical', 'Критическая'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='Код МТР')
    name = models.CharField(max_length=500, verbose_name='Наименование')
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='materials', verbose_name='Категория'
    )
    unit = models.CharField(max_length=20, verbose_name='Ед. изм.')
    gost = models.CharField(max_length=200, blank=True, verbose_name='ГОСТ/ТУ')
    technical_specs = models.TextField(blank=True, verbose_name='Технические характеристики')
    criticality = models.CharField(
        max_length=10, choices=CRITICALITY_CHOICES,
        default='medium', verbose_name='Критичность'
    )
    min_stock_level = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Минимальный запас'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Материал / Оборудование'
        verbose_name_plural = 'Материалы / Оборудование'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_total_stock(self):
        result = self.warehouse_stocks.aggregate(total=Sum('qty_on_hand'))
        return result['total'] or 0

    def get_available_stock(self):
        stocks = self.warehouse_stocks.all()
        return sum(s.qty_available for s in stocks)

    def get_best_price(self):
        quote = self.price_quotes.filter(
            supplier__is_active=True
        ).order_by('price').first()
        return quote.price if quote else None

    def get_latest_quote_date(self):
        quote = self.price_quotes.order_by('-quote_date').first()
        return quote.quote_date if quote else None

    def is_below_min_stock(self):
        return self.get_total_stock() < self.min_stock_level

    CRITICALITY_COLORS = {
        'low': 'secondary',
        'medium': 'primary',
        'high': 'warning',
        'critical': 'danger',
    }

    def get_criticality_color(self):
        return self.CRITICALITY_COLORS.get(self.criticality, 'secondary')


class WarehouseStock(models.Model):
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE,
        related_name='warehouse_stocks', verbose_name='Материал'
    )
    location = models.CharField(max_length=100, verbose_name='Место хранения')
    qty_on_hand = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Кол-во на складе'
    )
    qty_reserved = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Зарезервировано'
    )
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'
        unique_together = ['material', 'location']
        ordering = ['material__name', 'location']

    def __str__(self):
        return f"{self.material.name} — {self.location}: {self.qty_on_hand}"

    @property
    def qty_available(self):
        return max(self.qty_on_hand - self.qty_reserved, 0)

    @property
    def is_low(self):
        return self.qty_available <= self.material.min_stock_level


class Supplier(models.Model):
    name = models.CharField(max_length=500, verbose_name='Наименование')
    inn = models.CharField(max_length=12, unique=True, verbose_name='ИНН')
    contact_person = models.CharField(max_length=200, blank=True, verbose_name='Контактное лицо')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Адрес')
    rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=5.0,
        verbose_name='Рейтинг (1–10)'
    )
    delivery_reliability = models.DecimalField(
        max_digits=5, decimal_places=1, default=95.0,
        verbose_name='Надёжность поставок, %'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['-rating', 'name']

    def __str__(self):
        return self.name

    def get_quotes_count(self):
        return self.price_quotes.count()

    def get_orders_count(self):
        return self.orders.count()

    def get_avg_price_change(self):
        """Returns average price change trend as percentage (positive = growth)."""
        return None  # Placeholder for analytics

    RATING_COLORS = {
        range(1, 4): 'danger',
        range(4, 7): 'warning',
        range(7, 9): 'info',
        range(9, 11): 'success',
    }

    def get_rating_color(self):
        r = int(self.rating)
        if r <= 3:
            return 'danger'
        elif r <= 6:
            return 'warning'
        elif r <= 8:
            return 'info'
        return 'success'


class PriceQuote(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE,
        related_name='price_quotes', verbose_name='Поставщик'
    )
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE,
        related_name='price_quotes', verbose_name='Материал'
    )
    price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Цена, руб.')
    delivery_days = models.PositiveIntegerField(verbose_name='Срок поставки, дней')
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name='Условия оплаты')
    logistics_notes = models.TextField(blank=True, verbose_name='Условия логистики')
    quote_date = models.DateField(verbose_name='Дата предложения')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Действительно до')
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Ценовое предложение'
        verbose_name_plural = 'Ценовые предложения'
        ordering = ['-quote_date', 'price']

    def __str__(self):
        return f"{self.supplier.name} / {self.material.code}: {self.price} руб."

    @property
    def is_valid(self):
        if self.valid_until:
            return self.valid_until >= timezone.now().date()
        return True


class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'На рассмотрении'),
        ('approved', 'Утверждена'),
        ('rejected', 'Отклонена'),
        ('ordered', 'Заказ размещён'),
        ('completed', 'Исполнена'),
    ]
    CRITICALITY_CHOICES = [
        ('planned', 'Плановая'),
        ('emergency', 'Аварийная'),
    ]
    STATUS_COLORS = {
        'draft': 'secondary',
        'submitted': 'primary',
        'approved': 'success',
        'rejected': 'danger',
        'ordered': 'info',
        'completed': 'dark',
    }

    request_number = models.CharField(max_length=30, unique=True, verbose_name='Номер заявки')
    requester = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT,
        related_name='my_requests', verbose_name='Инициатор'
    )
    department = models.CharField(max_length=200, verbose_name='Подразделение')
    need_date = models.DateField(verbose_name='Дата необходимости')
    criticality = models.CharField(
        max_length=10, choices=CRITICALITY_CHOICES,
        default='planned', verbose_name='Тип заявки'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='draft', verbose_name='Статус'
    )
    justification = models.TextField(blank=True, verbose_name='Обоснование потребности')
    rejection_comment = models.TextField(blank=True, verbose_name='Комментарий при отклонении')
    approved_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_requests', verbose_name='Утверждено'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка на закупку'
        verbose_name_plural = 'Заявки на закупку'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка {self.request_number}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            year = timezone.now().year
            count = PurchaseRequest.objects.filter(created_at__year=year).count() + 1
            self.request_number = f"ЗК-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    def get_total_target_amount(self):
        total = 0
        for item in self.items.all():
            if item.target_price and item.qty_to_purchase:
                total += item.qty_to_purchase * item.target_price
        return total

    def check_and_update_stock(self):
        """Check warehouse availability for all items and update qty_to_purchase."""
        for item in self.items.all():
            available = item.material.get_available_stock()
            item.qty_available_at_warehouse = min(available, item.qty_requested)
            item.qty_to_purchase = max(0, item.qty_requested - item.qty_available_at_warehouse)
            item.save()

    def all_items_have_quotes(self):
        items_need_purchase = self.items.filter(qty_to_purchase__gt=0)
        return all(item.selected_quote_id for item in items_need_purchase)

    @property
    def can_be_submitted(self):
        return self.status == 'draft' and self.items.exists()

    @property
    def can_be_approved(self):
        return self.status == 'submitted'

    @property
    def can_generate_order(self):
        return self.status == 'approved'


class RequestItem(models.Model):
    request = models.ForeignKey(
        PurchaseRequest, on_delete=models.CASCADE,
        related_name='items', verbose_name='Заявка'
    )
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT,
        verbose_name='Материал'
    )
    qty_requested = models.DecimalField(
        max_digits=12, decimal_places=3,
        verbose_name='Количество'
    )
    qty_available_at_warehouse = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='Доступно на складе'
    )
    qty_to_purchase = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        verbose_name='К закупке'
    )
    target_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name='Целевая цена, руб.'
    )
    selected_quote = models.ForeignKey(
        PriceQuote, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Выбранное предложение'
    )
    justification_for_choice = models.TextField(
        blank=True, verbose_name='Обоснование выбора поставщика'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')

    class Meta:
        verbose_name = 'Позиция заявки'
        verbose_name_plural = 'Позиции заявки'

    def __str__(self):
        return f"{self.request.request_number} — {self.material.name}"

    @property
    def line_total(self):
        if self.target_price and self.qty_to_purchase:
            return float(self.qty_to_purchase) * float(self.target_price)
        return None

    def get_comparison_quotes(self):
        """Score available quotes by criteria weighted for request criticality."""
        quotes = list(
            PriceQuote.objects.filter(
                material=self.material, supplier__is_active=True
            ).select_related('supplier').order_by('price')
        )
        if not quotes:
            return []

        criticality = self.request.criticality
        if criticality == 'emergency':
            w_price, w_delivery, w_reliability = 0.20, 0.70, 0.10
        else:
            w_price, w_delivery, w_reliability = 0.60, 0.20, 0.20

        prices = [float(q.price) for q in quotes]
        deliveries = [q.delivery_days for q in quotes]
        min_p, max_p = min(prices), max(prices)
        min_d, max_d = min(deliveries), max(deliveries)

        results = []
        for q in quotes:
            p = float(q.price)
            d = q.delivery_days
            price_score = 1.0 if max_p == min_p else 1.0 - (p - min_p) / (max_p - min_p)
            delivery_score = 1.0 if max_d == min_d else 1.0 - (d - min_d) / (max_d - min_d)
            reliability_score = float(q.supplier.rating) / 10.0
            total = (price_score * w_price + delivery_score * w_delivery + reliability_score * w_reliability) * 100
            results.append({
                'quote': q,
                'price_score': round(price_score * 100, 1),
                'delivery_score': round(delivery_score * 100, 1),
                'reliability_score': round(reliability_score * 100, 1),
                'total_score': round(total, 1),
                'is_recommended': False,
                'is_selected': self.selected_quote_id == q.id,
            })

        if results:
            best_idx = max(range(len(results)), key=lambda i: results[i]['total_score'])
            results[best_idx]['is_recommended'] = True

        return sorted(results, key=lambda x: x['total_score'], reverse=True)


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent', 'Отправлен поставщику'),
        ('confirmed', 'Подтверждён'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    STATUS_COLORS = {
        'draft': 'secondary',
        'sent': 'primary',
        'confirmed': 'info',
        'delivered': 'success',
        'cancelled': 'danger',
    }

    order_number = models.CharField(max_length=30, unique=True, verbose_name='Номер заказа')
    request = models.ForeignKey(
        PurchaseRequest, on_delete=models.PROTECT,
        related_name='orders', verbose_name='Заявка'
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT,
        related_name='orders', verbose_name='Поставщик'
    )
    order_date = models.DateField(verbose_name='Дата заказа')
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name='Ожидаемая дата доставки')
    actual_delivery_date = models.DateField(null=True, blank=True, verbose_name='Фактическая дата доставки')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='draft', verbose_name='Статус'
    )
    total_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=0,
        verbose_name='Сумма, руб.'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Заказ поставщику'
        verbose_name_plural = 'Заказы поставщикам'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            year = timezone.now().year
            count = PurchaseOrder.objects.filter(created_at__year=year).count() + 1
            self.order_number = f"ЗП-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def get_status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def is_overdue(self):
        if self.expected_delivery_date and self.status not in ('delivered', 'cancelled'):
            return timezone.now().date() > self.expected_delivery_date
        return False


class AuditLog(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, verbose_name='Пользователь'
    )
    action = models.CharField(max_length=500, verbose_name='Действие')
    model_name = models.CharField(max_length=100, verbose_name='Объект')
    object_id = models.IntegerField(null=True, blank=True, verbose_name='ID')
    object_repr = models.CharField(max_length=500, blank=True, verbose_name='Описание')
    details = models.TextField(blank=True, verbose_name='Детали')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')

    class Meta:
        verbose_name = 'Журнал операций'
        verbose_name_plural = 'Журнал операций'
        ordering = ['-timestamp']

    def __str__(self):
        ts = self.timestamp.strftime('%d.%m.%Y %H:%M') if self.timestamp else '—'
        return f"{ts} — {self.user} — {self.action}"
