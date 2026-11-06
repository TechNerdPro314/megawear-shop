from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone = forms.CharField(
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'class': 'phone-mask',
            'placeholder': '+7 (___) ___-__-__'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if not phone:
            return phone
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) != 11 or digits[0] not in ('7', '8'):
            raise forms.ValidationError("Некорректный номер телефона.")
        return digits


class ProfileForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'class': 'phone-mask',
            'placeholder': '+7 (___) ___-__-__'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if not phone:
            return phone
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) != 11 or digits[0] not in ('7', '8'):
            raise forms.ValidationError("Некорректный номер телефона.")
        return digits


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email адрес",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autocomplete': 'email'
        }),
        help_text="Введите email, привязанный к вашему аккаунту"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email, is_active=True).exists():
            pass
        return email