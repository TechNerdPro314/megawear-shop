from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from apps.notifications.models import Notification

@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if created:
        # При создании заказа не отправляем уведомление (уже есть email)
        return

    # Проверяем, что статус действительно изменился
    try:
        old_instance = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if old_instance.status != instance.status and instance.user:
        Notification.objects.create(
            user=instance.user,
            title=f'Заказ #{instance.id}',
            message=f'Статус заказа изменён на "{instance.get_status_display()}"',
            notification_type='order_status',
            content_object=instance
        )