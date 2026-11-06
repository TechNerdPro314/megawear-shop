import uuid
from django.db import models
from django.conf import settings
from apps.orders.models import Order

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('waiting_for_capture', 'Ожидает подтверждения'),
        ('succeeded', 'Оплачен'),
        ('canceled', 'Отменён'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    yookassa_id = models.CharField('ID платежа в ЮKassa', max_length=255, blank=True, null=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2)
    confirmation_url = models.URLField('URL для оплаты', blank=True, null=True)
    paid_at = models.DateTimeField('Время оплаты', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"Платёж #{self.pk} по заказу #{self.order_id}"