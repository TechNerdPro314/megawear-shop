from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q

from apps.orders.models import Order, OrderStatus


class EmailNotificationService:
    """Сервис для отправки email уведомлений"""
    
    @staticmethod
    def send_order_confirmation(
        order: Order,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> bool:
        """
        Отправить подтверждение заказа клиенту
        
        Args:
            order: Заказ
            recipient_email: Email получателя (опционально, берется из заказа)
            recipient_name: Имя получателя (опционально, берется из заказа)
            
        Returns:
            bool: Успешно ли отправлено
        """
        email = recipient_email or order.customer_email
        name = recipient_name or order.customer_name
        
        subject = f"Заказ #{order.id} подтвержден"
        
        try:
            html_message = render_to_string("emails/order_customer.html", {
                "order": order,
                "customer_name": name,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Ошибка отправки подтверждения заказа: {e}")
            return False
    
    @staticmethod
    def send_manager_alert(order: Order) -> bool:
        """
        Отправить уведомление менеджеру о новом заказе
        
        Args:
            order: Заказ
            
        Returns:
            bool: Успешно ли отправлено
        """
        # Получаем email менеджеров (из настроек или администраторов)
        manager_emails = getattr(settings, "MANAGER_EMAILS", [])
        if not manager_emails:
            # Если не задано, отправляем всем суперюзерам
            from django.contrib.auth import get_user_model
            User = get_user_model()
            managers = User.objects.filter(is_superuser=True).values_list("email", flat=True)
            manager_emails = [e for e in managers if e]
        
        if not manager_emails:
            print("Нет email адресов менеджеров")
            return False
        
        subject = f"🛒 Новый заказ #{order.id}"
        
        try:
            html_message = render_to_string("emails/order_manager.html", {
                "order": order,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=manager_emails,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Ошибка отправки уведомления менеджеру: {e}")
            return False
    
    @staticmethod
    def send_status_update(
        order: Order,
        new_status: OrderStatus,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> bool:
        """
        Отправить уведомление об изменении статуса заказа
        
        Args:
            order: Заказ
            new_status: Новый статус
            recipient_email: Email получателя
            recipient_name: Имя получателя
            
        Returns:
            bool: Успешно ли отправлено
        """
        email = recipient_email or order.customer_email
        name = recipient_name or order.customer_name
        
        subject = f"Статус заказа #{order.id} изменен на {order.get_status_display()}"
        
        try:
            html_message = render_to_string("emails/order_status.html", {
                "order": order,
                "customer_name": name,
                "new_status": order.get_status_display(),
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Ошибка отправки обновления статуса: {e}")
            return False


class NotificationManager:
    """Менеджер уведомлений с поддержкой очереди и асинхронной отправки"""
    
    @staticmethod
    def create_notification(
        notification_type: str,
        recipient_email: str,
        subject: str,
        message: str,
        recipient=None,
        order=None,
        metadata: dict = None
    ):
        """Создать уведомление в базе данных"""
        from apps.notifications.models import Notification
        
        return Notification.objects.create(
            notification_type=notification_type,
            recipient_email=recipient_email,
            subject=subject,
            message=message,
            recipient=recipient,
            order=order,
            metadata=metadata or {},
        )
    
    @staticmethod
    def get_pending_notifications(limit: int = 100):
        """Получить уведомления в очереди"""
        from apps.notifications.models import Notification
        return Notification.objects.filter(
            status="pending"
        ).order_by("created_at")[:limit]
    
    @staticmethod
    def process_pending_notifications():
        """Обработать все уведомления в очереди (для celery beat)"""
        from apps.notifications.models import Notification
        from apps.notifications.tasks import send_email_notification_task
        
        notifications = NotificationManager.get_pending_notifications()
        
        for notification in notifications:
            send_email_notification_task.delay(notification.id)
        
        return notifications.count()


class TelegramNotificationService:
    """Сервис для отправки уведомлений в Telegram (заготовка)"""
    
    @staticmethod
    def send_order_alert(order: Order) -> bool:
        """
        Отправить уведомление в Telegram о новом заказе
        
        Пока заготовка - реализуется позже
        """
        # TODO: Реализовать отправку в Telegram
        # 1. Получить токен бота из .env
        # 2. Получить chat_id менеджера(ов)
        # 3. Формировать сообщение с деталями заказа
        # 4. Отправлять через Telegram Bot API
        
        return False
    
    @staticmethod
    def send_status_update(order: Order, new_status: str) -> bool:
        """
        Отправить уведомление в Telegram об изменении статуса
        
        Пока заготовка - реализуется позже
        """
        # TODO: Реализовать отправку в Telegram
        return False


def send_order_notification(order: Order) -> None:
    """
    Отправить уведомления о заказе (клиенту и менеджеру)
    
    Args:
        order: Заказ
    """
    from apps.orders.models import OrderStatus
    
    # Отправка клиенту
    EmailNotificationService.send_order_confirmation(order)
    
    # Отправка менеджеру
    EmailNotificationService.send_manager_alert(order)