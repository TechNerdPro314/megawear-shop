from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Coupon
from apps.notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Coupon)
def notify_new_promotion(sender, instance, created, **kwargs):
    if created and instance.active:
        users = User.objects.filter(is_active=True)
        for user in users:
            Notification.objects.create(
                user=user,
                title=f'Новая акция: {instance.code}',
                message=f'Скидка {instance.discount_value}{"%" if instance.discount_type=="percent" else "₽"} на заказы от {instance.min_order_amount}₽. Действует до {instance.valid_to.strftime("%d.%m.%Y")}',
                notification_type='promo',
                content_object=instance
            )