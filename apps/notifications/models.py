from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    TYPE_CHOICES = [
        ('order_status', 'Статус заказа'),
        ('promo', 'Акция'),
        ('system', 'Системное'),
        ('personal', 'Персональное'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    title = models.CharField('Заголовок', max_length=255, default='')
    message = models.TextField('Сообщение', default='')
    notification_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField('Прочитано', default=False, db_index=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'[{self.get_notification_type_display()}] {self.title}'