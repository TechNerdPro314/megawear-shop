from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.catalog.models import Product
from apps.orders.models import Order, OrderStatus


class Review(models.Model):
    STATUS_CHOICES = (
        ("pending", "На модерации"),
        ("approved", "Одобрен"),
        ("rejected", "Отклонен"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    rating = models.PositiveSmallIntegerField(
        "Оценка",
        choices=[(i, f"{i} ⭐") for i in range(1, 6)],
        default=5
    )
    title = models.CharField(
        "Заголовок",
        max_length=200,
        blank=True,
        help_text="Краткое название отзыва"
    )
    text = models.TextField("Текст отзыва")

    # Статус модерации
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    # Проверка покупки
    is_verified_purchase = models.BooleanField(
        "Подтвержденная покупка",
        default=False,
        editable=False,
        db_index=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        help_text="Заказ, в рамках которого был сделан отзыв"
    )

    # Модерация
    moderation_comment = models.TextField(
        "Комментарий модератора",
        blank=True
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_reviews"
    )
    moderated_at = models.DateTimeField(null=True, blank=True)

    # Помощь отзыву
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]
        unique_together = ("product", "user")  # Один отзыв на товар от пользователя

    def __str__(self):
        return f"{self.user.username} -> {self.product.name} ({self.rating}⭐)"

    @property
    def is_approved(self):
        """Для обратной совместимости"""
        return self.status == "approved"

    @is_approved.setter
    def is_approved(self, value):
        self.status = "approved" if value else "rejected"

    def can_be_reviewed_by_user(self, user) -> bool:
        """Проверка: может ли пользователь написать отзыв"""
        if not user.is_authenticated:
            return False
        
        # Проверяем, есть ли уже отзыв
        if Review.objects.filter(product=self.product, user=user).exists():
            return False
        
        return True

    @classmethod
    def is_verified_purchase_for_user(cls, product, user) -> bool:
        """Проверяет, покупал ли пользователь этот товар"""
        return Order.objects.filter(
            user=user,
            status__in=[OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
            items__product=product
        ).exists()

    def approve(self, moderator=None, comment=""):
        """Одобрить отзыв"""
        self.status = "approved"
        self._moderate(moderator, comment)

    def reject(self, moderator=None, comment=""):
        """Отклонить отзыв"""
        self.status = "rejected"
        self._moderate(moderator, comment)

    def _moderate(self, moderator=None, comment=""):
        """Внутренняя логика модерации"""
        if moderator:
            self.moderated_by = moderator
        self.moderation_comment = comment
        self.moderated_at = timezone.now()
        self.save(update_fields=[
            "status", "moderated_by", "moderation_comment", "moderated_at", "updated_at"
        ])

    @classmethod
    def get_average_rating(cls, product):
        """Средний рейтинг товара"""
        from django.db.models import Avg
        result = cls.objects.filter(
            product=product,
            status="approved"
        ).aggregate(avg=Avg("rating"))
        return result["avg"] or 0

    @classmethod
    def get_rating_distribution(cls, product):
        """Распределение оценок"""
        from django.db.models import Count
        distribution = cls.objects.filter(
            product=product,
            status="approved"
        ).values("rating").annotate(count=Count("id")).order_by("-rating")
        
        return {i: 0 for i in range(1, 6)} | {item["rating"]: item["count"] for item in distribution}
