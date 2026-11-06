# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Валидатор для российского мобильного номера (11 цифр, начинается с 7 или 8)
phone_validator = RegexValidator(
    regex=r'^[78]\d{10}$',
    message="Введите номер в формате +7XXXXXXXXXX (11 цифр)."
)

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя с добавлением телефона.
    """
    username = models.CharField(_('username'), max_length=150, unique=True)
    
    phone = models.CharField(
        _('phone number'),
        max_length=18,             # достаточно для полной маски
        validators=[phone_validator],
        blank=True,
        help_text=_('Формат: +7 (999) 123-45-67')
    )

    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    email = models.EmailField(_('email address'), unique=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.get_full_name() or self.username