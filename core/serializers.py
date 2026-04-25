from rest_framework import serializers
from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog
)


class UserShortSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'role', 'department', 'position']

    def get_full_name(self, obj):
        return obj.get_full_name_or_username()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'full_name',
            'email', 'role', 'department', 'position', 'is_active',
            'is_staff', 'date_joined',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name_or_username()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'password', 'first_name', 'last_name',
            'email', 'role', 'department', 'position', 'is_active',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'role', 'department', 'position', 'is_active',
        ]


class CategorySerializer(serializers.ModelSerializer):
    materials_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'materials_count']

    def get_materials_count(self, obj):
        return obj.get_materials_count()


class MaterialShortSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Material
        fields = ['id', 'code', 'name', 'unit', 'category', 'category_name', 'criticality']


class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    best_price = serializers.SerializerMethodField()
    criticality_color = serializers.SerializerMethodField()
    is_below_min_stock = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'code', 'name', 'category', 'category_name', 'unit',
            'gost', 'technical_specs', 'criticality', 'criticality_color',
            'min_stock_level', 'is_active', 'created_at', 'updated_at',
            'total_stock', 'available_stock', 'best_price', 'is_below_min_stock',
        ]

    def get_total_stock(self, obj):
        return float(obj.get_total_stock())

    def get_available_stock(self, obj):
        return float(obj.get_available_stock())

    def get_best_price(self, obj):
        p = obj.get_best_price()
        return float(p) if p is not None else None

    def get_criticality_color(self, obj):
        return obj.get_criticality_color()

    def get_is_below_min_stock(self, obj):
        return obj.is_below_min_stock()


class WarehouseStockSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_code = serializers.CharField(source='material.code', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    material_min_stock = serializers.DecimalField(
        source='material.min_stock_level', max_digits=12, decimal_places=3, read_only=True
    )
    qty_available = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    is_low = serializers.BooleanField(read_only=True)

    class Meta:
        model = WarehouseStock
        fields = [
            'id', 'material', 'material_name', 'material_code', 'material_unit',
            'material_min_stock', 'location', 'qty_on_hand', 'qty_reserved',
            'qty_available', 'is_low', 'last_update',
        ]


class SupplierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'inn', 'rating', 'is_active']


class SupplierSerializer(serializers.ModelSerializer):
    rating_color = serializers.SerializerMethodField()
    quotes_count = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'inn', 'contact_person', 'phone', 'email',
            'address', 'rating', 'delivery_reliability', 'is_active',
            'notes', 'created_at', 'rating_color', 'quotes_count', 'orders_count',
        ]

    def get_rating_color(self, obj):
        return obj.get_rating_color()

    def get_quotes_count(self, obj):
        return obj.get_quotes_count()

    def get_orders_count(self, obj):
        return obj.get_orders_count()


class PriceQuoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_code = serializers.CharField(source='material.code', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = PriceQuote
        fields = [
            'id', 'supplier', 'supplier_name', 'material', 'material_name',
            'material_code', 'material_unit', 'price', 'delivery_days',
            'payment_terms', 'logistics_notes', 'quote_date', 'valid_until',
            'notes', 'is_valid',
        ]


class RequestItemSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_code = serializers.CharField(source='material.code', read_only=True)
    material_unit = serializers.CharField(source='material.unit', read_only=True)
    selected_quote_supplier = serializers.CharField(
        source='selected_quote.supplier.name', read_only=True
    )
    selected_quote_price = serializers.DecimalField(
        source='selected_quote.price', max_digits=14, decimal_places=2, read_only=True
    )
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = RequestItem
        fields = [
            'id', 'material', 'material_name', 'material_code', 'material_unit',
            'qty_requested', 'qty_available_at_warehouse', 'qty_to_purchase',
            'target_price', 'selected_quote', 'selected_quote_supplier',
            'selected_quote_price', 'justification_for_choice', 'notes', 'line_total',
        ]

    def get_line_total(self, obj):
        return obj.line_total


class PurchaseRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.get_full_name_or_username', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    items = RequestItemSerializer(many=True, read_only=True)
    can_be_submitted = serializers.BooleanField(read_only=True)
    can_be_approved = serializers.BooleanField(read_only=True)
    can_generate_order = serializers.BooleanField(read_only=True)
    total_target_amount = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'request_number', 'requester', 'requester_name',
            'department', 'need_date', 'criticality', 'status', 'status_color',
            'justification', 'rejection_comment',
            'approved_by', 'approved_by_name', 'approved_at',
            'created_at', 'updated_at',
            'items', 'can_be_submitted', 'can_be_approved', 'can_generate_order',
            'total_target_amount',
        ]
        read_only_fields = ['request_number', 'requester', 'approved_by', 'approved_at']

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name_or_username() if obj.approved_by else None

    def get_status_color(self, obj):
        return obj.get_status_color()

    def get_total_target_amount(self, obj):
        return obj.get_total_target_amount()


class PurchaseRequestListSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.get_full_name_or_username', read_only=True)
    status_color = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    total_target_amount = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'request_number', 'requester', 'requester_name',
            'department', 'need_date', 'criticality', 'status', 'status_color',
            'created_at', 'items_count', 'total_target_amount',
        ]

    def get_status_color(self, obj):
        return obj.get_status_color()

    def get_items_count(self, obj):
        return obj.items.count()

    def get_total_target_amount(self, obj):
        return obj.get_total_target_amount()


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    request_number = serializers.CharField(source='request.request_number', read_only=True)
    status_color = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'request', 'request_number', 'supplier',
            'supplier_name', 'order_date', 'expected_delivery_date',
            'actual_delivery_date', 'status', 'status_color', 'total_amount',
            'notes', 'created_at', 'is_overdue', 'created_by_name',
        ]

    def get_status_color(self, obj):
        return obj.get_status_color()

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name_or_username() if obj.created_by else None


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'model_name',
            'object_id', 'object_repr', 'details', 'timestamp', 'ip_address',
        ]

    def get_user_name(self, obj):
        return obj.user.get_full_name_or_username() if obj.user else '—'


class ComparisonQuoteSerializer(serializers.Serializer):
    quote_id = serializers.IntegerField(source='quote.id')
    supplier_name = serializers.CharField(source='quote.supplier.name')
    price = serializers.DecimalField(source='quote.price', max_digits=14, decimal_places=2)
    delivery_days = serializers.IntegerField(source='quote.delivery_days')
    payment_terms = serializers.CharField(source='quote.payment_terms')
    quote_date = serializers.DateField(source='quote.quote_date')
    valid_until = serializers.DateField(source='quote.valid_until', allow_null=True)
    price_score = serializers.FloatField()
    delivery_score = serializers.FloatField()
    reliability_score = serializers.FloatField()
    total_score = serializers.FloatField()
    is_recommended = serializers.BooleanField()
    is_selected = serializers.BooleanField()
    supplier_rating = serializers.DecimalField(source='quote.supplier.rating', max_digits=3, decimal_places=1)
