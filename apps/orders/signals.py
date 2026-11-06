from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order
from apps.notifications.models import Notification

@receiver(pre_save, sender=Order)
def store_old_status(sender, instance, **kwargs):
    """Сохраняем старый статус перед сохранением заказа."""
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Order.DoesNotExist:
            pass

@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    """Создаём уведомление, если статус изменился."""
    # При создании нового заказа уведомление не отправляем (уже есть email)
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    # Если старый статус известен и отличается от нового, и у заказа есть владелец
    if old_status and old_status != instance.status and instance.user:
        Notification.objects.create(
            user=instance.user,
            title=f'Заказ #{instance.id}',
            message=f'Статус заказа изменён на «{instance.get_status_display()}»',
            notification_type='order_status',
            content_object=instance
        )