from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_notifications(order_id: int):
    """Отправляет уведомления клиенту и менеджерам."""
    from .models import Order

    try:
        order = Order.objects.select_related("user").get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Заказ #{order_id} не найден")
        return

    # Клиенту
    if order.customer_email:
        subject = f"Заказ №{order.id} принят"
        message = (
            f"Здравствуйте, {order.customer_name or 'покупатель'}!\n\n"
            f"Ваш заказ №{order.id} на сумму {order.total_amount} руб. успешно создан.\n"
            f"Статус: {order.get_status_display()}.\n\n"
            f"Спасибо за покупку!"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.customer_email])
            logger.info(f"Подтверждение заказа #{order.id} отправлено клиенту")
        except Exception as e:
            logger.error(f"Ошибка отправки клиенту: {e}")

    # Менеджерам
    manager_emails = getattr(settings, "MANAGER_EMAILS", [])
    if manager_emails:
        subject = f"Новый заказ №{order.id}"
        message = (
            f"Поступил заказ №{order.id} от {order.customer_name or 'неизвестного'}.\n"
            f"Сумма: {order.total_amount} руб.\n"
            f"Доставка: {order.get_delivery_method_display() or order.delivery_method}\n"
            f"Телефон: {order.customer_phone}\n"
            f"Email: {order.customer_email}"
        )
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, manager_emails)
            logger.info(f"Уведомление менеджерам отправлено")
        except Exception as e:
            logger.error(f"Ошибка отправки менеджерам: {e}")