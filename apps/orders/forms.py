from django import forms
from .models import Order
from apps.cart.services import DELIVERY_OPTIONS

class CheckoutForm(forms.ModelForm):
    customer_phone = forms.CharField(
        max_length=18,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'class': 'phone-mask',
            'placeholder': '+7 (___) ___-__-__'
        })
    )
    delivery_address = forms.CharField(
        required=False,  # сделаем необязательным, если самовывоз
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Город, улица, дом, квартира',
            'class': 'form-control',
        })
    )
    delivery_method = forms.CharField(widget=forms.HiddenInput(), required=True)
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHODS,
        widget=forms.RadioSelect(),
        initial='online',
        label='Способ оплаты'
    )

    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_email',
            'customer_phone',
            'delivery_address',
            'comment',
            'payment_method',
        ]

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '')
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) != 11 or digits[0] not in ('7', '8'):
            raise forms.ValidationError("Некорректный номер телефона.")
        return digits

    def clean_delivery_method(self):
        method = self.cleaned_data['delivery_method']
        if method not in DELIVERY_OPTIONS:
            raise forms.ValidationError("Выберите способ доставки")
        return method

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('payment_method')
        delivery = cleaned.get('delivery_method')
        address = cleaned.get('delivery_address', '')

        # Наличные только при курьерской доставке и адрес обязателен
        if method == 'cash':
            if delivery != 'courier':
                self.add_error('payment_method', 'Наличные доступны только при курьерской доставке.')
            if not address.strip():
                self.add_error('delivery_address', 'Укажите адрес доставки.')
        # Оплата в магазине только при самовывозе
        if method == 'store' and delivery != 'pickup':
            self.add_error('payment_method', 'Оплата в магазине доступна только при самовывозе.')
        # Для доставки курьером адрес обязателен
        if delivery == 'courier' and not address.strip():
            self.add_error('delivery_address', 'Введите адрес доставки.')
        return cleaned