from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem, PurchaseOrder
)


class LoginForm(forms.Form):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Сохранить', css_class='btn-primary'))


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'code', 'name', 'category', 'unit', 'gost',
            'technical_specs', 'criticality', 'min_stock_level', 'is_active'
        ]
        widgets = {
            'technical_specs': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('code', css_class='col-md-3'), Column('name', css_class='col-md-9')),
            Row(Column('category', css_class='col-md-4'), Column('unit', css_class='col-md-2'),
                Column('criticality', css_class='col-md-3'), Column('min_stock_level', css_class='col-md-3')),
            'gost',
            'technical_specs',
            'is_active',
            Submit('submit', 'Сохранить', css_class='btn-primary mt-2'),
        )


class WarehouseStockForm(forms.ModelForm):
    class Meta:
        model = WarehouseStock
        fields = ['material', 'location', 'qty_on_hand', 'qty_reserved']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Сохранить', css_class='btn-primary'))


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'inn', 'contact_person', 'phone', 'email',
            'address', 'rating', 'delivery_reliability', 'is_active', 'notes'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-8'), Column('inn', css_class='col-md-4')),
            Row(Column('contact_person', css_class='col-md-6'), Column('phone', css_class='col-md-3'),
                Column('email', css_class='col-md-3')),
            Row(Column('rating', css_class='col-md-3'), Column('delivery_reliability', css_class='col-md-3'),
                Column('is_active', css_class='col-md-3 mt-4')),
            'address',
            'notes',
            Submit('submit', 'Сохранить', css_class='btn-primary mt-2'),
        )


class PriceQuoteForm(forms.ModelForm):
    class Meta:
        model = PriceQuote
        fields = [
            'supplier', 'material', 'price', 'delivery_days',
            'payment_terms', 'logistics_notes', 'quote_date', 'valid_until', 'notes'
        ]
        widgets = {
            'quote_date': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'logistics_notes': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        material = kwargs.pop('material', None)
        supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        if material:
            self.fields['material'].initial = material
            self.fields['material'].widget = forms.HiddenInput()
        if supplier:
            self.fields['supplier'].initial = supplier
            self.fields['supplier'].widget = forms.HiddenInput()
        self.helper.layout = Layout(
            'supplier', 'material',
            Row(Column('price', css_class='col-md-4'), Column('delivery_days', css_class='col-md-4'),
                Column('quote_date', css_class='col-md-4')),
            Row(Column('payment_terms', css_class='col-md-6'), Column('valid_until', css_class='col-md-3')),
            'logistics_notes',
            'notes',
            Submit('submit', 'Сохранить', css_class='btn-primary mt-2'),
        )


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['department', 'need_date', 'criticality', 'justification']
        widgets = {
            'need_date': forms.DateInput(attrs={'type': 'date'}),
            'justification': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('department', css_class='col-md-6'),
                Column('need_date', css_class='col-md-3'),
                Column('criticality', css_class='col-md-3')),
            'justification',
            Submit('submit', 'Сохранить заявку', css_class='btn-primary mt-2'),
        )


class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = ['material', 'qty_requested', 'target_price', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = Material.objects.filter(is_active=True).order_by('name')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'material',
            Row(Column('qty_requested', css_class='col-md-4'),
                Column('target_price', css_class='col-md-4')),
            'notes',
            Submit('submit', 'Добавить позицию', css_class='btn-success mt-2'),
        )


class RejectRequestForm(forms.Form):
    rejection_comment = forms.CharField(
        label='Причина отклонения',
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Отклонить заявку', css_class='btn-danger'))


class SelectQuoteForm(forms.Form):
    quote_id = forms.IntegerField(widget=forms.HiddenInput)
    justification = forms.CharField(
        label='Обоснование выбора',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'expected_delivery_date', 'total_amount', 'notes']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Создать заказ', css_class='btn-primary'))


class CustomUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'department', 'position']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Создать пользователя', css_class='btn-primary'))


class CustomUserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role', 'department', 'position', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Сохранить', css_class='btn-primary'))
