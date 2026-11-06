import logging
import requests
import socket

# =========================================================
# ПРИНУДИТЕЛЬНЫЙ ПЕРЕХОД НА IPv4 (Решение для Docker/WSL2)
# =========================================================
# Docker на Windows (WSL2) часто не может достучаться до внешних 
# сайтов по IPv6. Эти строки заставляют библиотеку requests 
# использовать только IPv4.
try:
    import urllib3.util.connection as urllib3_cn
    def allowed_gai_family():
        return socket.AF_INET
    urllib3_cn.allowed_gai_family = allowed_gai_family
except ImportError:
    pass
# =========================================================

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ==========================================
# TASKS ДЛЯ EMAIL УВЕДОМЛЕНИЙ
# ==========================================

@shared_task(bind=True, max_retries=3)
def send_email_notification_task(self, notification_id: int) -> bool:
    """
    Асинхронная задача отправки email уведомления
    """
    from apps.notifications.models import Notification
    from apps.orders.models import Order
    
    try:
        notification = Notification.objects.select_related("order", "recipient").get(
            id=notification_id
        )
        
        recipient_email = notification.recipient_email
        subject = notification.subject
        message = notification.message
        
        if notification.order:
            order = notification.order
            if notification.notification_type == "order_confirmation":
                html_message = render_to_string("emails/order_customer.html", {
                    "order": order,
                    "customer_name": notification.recipient.username if notification.recipient else recipient_email.split("@")[0],
                })
            elif notification.notification_type == "manager_alert":
                html_message = render_to_string("emails/order_manager.html", {
                    "order": order,
                })
            elif notification.notification_type == "status_update":
                html_message = render_to_string("emails/order_status.html", {
                    "order": order,
                    "customer_name": notification.recipient.username if notification.recipient else recipient_email.split("@")[0],
                    "new_status": order.get_status_display(),
                })
            else:
                html_message = message
            
            plain_message = strip_tags(html_message)
        else:
            html_message = message
            plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        notification.mark_sent()
        logger.info(f"Email уведомление {notification_id} отправлено успешно")
        return True
        
    except Notification.DoesNotExist:
        logger.error(f"Уведомление {notification_id} не найдено")
        return False
    except Exception as exc:
        logger.error(f"Ошибка отправки email уведомления {notification_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_order_confirmation_email(order_id: int) -> bool:
    """Отправить подтверждение заказа клиенту (прямой вызов)"""
    from apps.notifications.services import EmailNotificationService
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        return EmailNotificationService.send_order_confirmation(order)
    except Order.DoesNotExist:
        logger.error(f"Заказ {order_id} не найден")
        return False


@shared_task
def send_manager_alert_email(order_id: int) -> bool:
    """Отправить уведомление менеджеру о новом заказе (прямой вызов)"""
    from apps.notifications.services import EmailNotificationService
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        return EmailNotificationService.send_manager_alert(order)
    except Order.DoesNotExist:
        logger.error(f"Заказ {order_id} не найден")
        return False


@shared_task
def send_status_update_email(order_id: int, new_status: str) -> bool:
    """Отправить уведомление об изменении статуса заказа"""
    from apps.notifications.services import EmailNotificationService
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        return EmailNotificationService.send_status_update(order, new_status)
    except Order.DoesNotExist:
        logger.error(f"Заказ {order_id} не найден")
        return False


@shared_task
def send_bulk_notifications(limit: int = 100) -> int:
    """Обработать пакет уведомлений (для Celery Beat)"""
    from apps.notifications.services import NotificationManager
    
    count = NotificationManager.process_pending_notifications()
    logger.info(f"Обработано {count} уведомлений")
    return count


# ==========================================
# TASKS ДЛЯ TELEGRAM УВЕДОМЛЕНИЙ
# ==========================================

@shared_task(bind=True, max_retries=3)
def send_telegram_order_notification(self, order_id: int, customer_name: str, total_amount: str, items_text: str, phone: str = "", address: str = ""):
    """
    Асинхронная отправка уведомления о новом заказе в Telegram.
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')

    if not bot_token or not chat_id:
        logger.warning("Telegram settings (TOKEN or CHAT_ID) are missing in .env")
        return "Settings missing"

    text = (
        f"🚨 *НОВЫЙ ЗАКАЗ #{order_id}*\n\n"
        f"👤 *Клиент:* {customer_name}\n"
        f"📞 *Телефон:* {phone}\n"
        f"📍 *Адрес:* {address}\n"
        f"💰 *Сумма:* {total_amount} ₽\n\n"
        f"📦 *Состав заказа:*\n{items_text}\n\n"
        f"👉 [Открыть в админке](http://localhost:8000/admin/orders/order/{order_id}/change/)"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram уведомление по заказу {order_id} отправлено успешно")
        return "Success"
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to send Telegram notification for order {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)