from decimal import Decimal
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_CHOICES = (
        ("percent", "Процентная скидка"),
        ("fixed", "Фиксированная сумма"),
    )

    code = models.CharField(
        "Код купона",
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Уникальный код для применения"
    )
    
    name = models.CharField(
        "Название",
        max_length=200,
        blank=True,
        help_text="Внутреннее описание купона"
    )
    
    # Тип и размер скидки
    discount_type = models.CharField(
        "Тип скидки",
        max_length=10,
        choices=DISCOUNT_CHOICES,
        default="percent",
        help_text="percent - скидка в %, fixed - фиксированная сумма"
    )
    
    discount_value = models.DecimalField(
        "Размер скидки",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Процент (0-100) или сумма в рублях"
    )
    
    # Ограничения
    min_order_amount = models.DecimalField(
        "Минимальная сумма заказа",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Минимальная сумма заказа для применения купона"
    )
    
    max_discount = models.DecimalField(
        "Максимальная сумма скидки",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        blank=True,
        null=True,
        help_text="Максимальная скидка (для процентных купонов). 0 - без ограничения"
    )
    
    # Лимиты использования
    usage_limit = models.PositiveIntegerField(
        "Лимит использования",
        default=0,
        help_text="Максимальное количество использований. 0 - без ограничений"
    )
    
    usage_count = models.PositiveIntegerField(
        "Количество использований",
        default=0,
        editable=False
    )
    
    # Ограничение на одного пользователя
    per_user_limit = models.PositiveIntegerField(
        "Лимит на пользователя",
        default=0,
        help_text="Максимум использований одним пользователем. 0 - без ограничений"
    )
    
    # Статус и период действия
    active = models.BooleanField(
        "Активен",
        default=True,
        db_index=True
    )
    
    valid_from = models.DateTimeField(
        "Действителен с",
        help_text="Дата и время начала действия"
    )
    
    valid_to = models.DateTimeField(
        "Действителен по",
        help_text="Дата и время окончания действия"
    )
    
    # Применение к категориям (опционально)
    applicable_categories = models.ManyToManyField(
        "catalog.Category",
        blank=True,
        related_name="coupons",
        help_text="Оставьте пустым для применения ко всем товарам"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Купон"
        verbose_name_plural = "Купоны"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        
        if self.discount_type == "percent" and not (0 <= self.discount_value <= 100):
            raise ValidationError({"discount_value": "Процент скидки должен быть от 0 до 100"})
        
        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError({"valid_to": "Дата окончания должна быть позже даты начала"})

    def is_valid(self) -> bool:
        """
        Проверяет актуальность купона
        
        Returns:
            bool: Активен ли купон в текущий момент
        """
        now = timezone.now()
        
        if not self.active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_to and now > self.valid_to:
            return False
        
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            return False
        
        return True

    def is_usable_by_user(self, user) -> bool:
        """
        Проверяет возможность использования купона пользователем
        
        Args:
            user: Пользователь (User или None для гостя)
            
        Returns:
            bool: Можно ли применить купон
        """
        if not self.is_valid():
            return False
        
        # Проверка лимита на пользователя
        if self.per_user_limit > 0 and user and user.is_authenticated:
            used_count = self.user_usage_count(user)
            if used_count >= self.per_user_limit:
                return False
        
        return True

    def user_usage_count(self, user) -> int:
        """
        Количество использований купона пользователем.
        Считаем заказы, где купон был применён (поле coupon_code)
        и которые не были отменены.
        """
        if not user or not user.is_authenticated:
            return 0
        
        # Убедимся, что модель Order имеет поле coupon_code
        from apps.orders.models import Order
        
        # Список статусов, которые считаем "выполненными"
        completed_statuses = ['paid', 'processing', 'shipped', 'delivered']
        
        return Order.objects.filter(
            user=user,
            coupon_code__iexact=self.code,
            status__in=completed_statuses
        ).count()

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """
        Рассчитывает сумму скидки
        
        Args:
            subtotal: Сумма заказа до скидки
            
        Returns:
            Decimal: Сумма скидки
        """
        if subtotal < self.min_order_amount:
            return Decimal("0")
        
        if self.discount_type == "percent":
            discount = subtotal * self.discount_value / Decimal("100")
            
            # Применяем ограничение максимальной скидки
            if self.max_discount and self.max_discount > 0:
                discount = min(discount, self.max_discount)
        else:  # fixed
            discount = min(self.discount_value, subtotal)
        
        return discount.quantize(Decimal("0.01"))

    def increment_usage(self):
        """Увеличивает счетчик использований"""
        self.usage_count += 1
        self.save(update_fields=["usage_count", "updated_at"])

    def can_apply_to_order(self, order) -> bool:
        """
        Проверяет возможность применения купона к заказу
        
        Args:
            order: Заказ
            
        Returns:
            bool: Можно ли применить
        """
        if not self.is_valid():
            return False
        
        # Проверка минимальной суммы
        if order.subtotal_amount < self.min_order_amount:
            return False
        
        # Проверка категорий (если указаны)
        if self.applicable_categories.exists():
            order_categories = set(
                item.product.category_id 
                for item in order.items.all() 
                if item.product.category_id
            )
            valid_categories = set(self.applicable_categories.values_list("id", flat=True))
            
            if not order_categories & valid_categories:  # Пересечение пустое
                return False
        
        return True