from django.db import models
from django.conf import settings
from apps.catalog.models import Product


class OrderStatus(models.TextChoices):
    NEW = "new", "Новый"
    CONFIRMED = "confirmed", "Подтверждён"
    PAID = "paid", "Оплачен"
    PROCESSING = "processing", "В обработке"
    SHIPPED = "shipped", "Отправлен"
    DELIVERED = "delivered", "Доставлен"
    CANCELLED = "cancelled", "Отменён"


class Order(models.Model):
    PAYMENT_METHODS = [
        ("card", "Банковская карта"),
        ("cash", "Наличные при доставке"),
        ("online", "Онлайн оплата"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="orders"
    )
    customer_name = models.CharField("Имя покупателя", max_length=200, blank=True, null=True)
    customer_phone = models.CharField("Телефон", max_length=30, blank=True, null=True)
    customer_email = models.EmailField("Email", blank=True, null=True, help_text="Email для подтверждения заказа")
    delivery_address = models.TextField("Адрес доставки", blank=True, null=True)
    delivery_method = models.CharField(
        "Способ доставки",
        max_length=50,
        blank=True,
        null=True,
        help_text="courier, pickup, post, cdek"
    )
    comment = models.TextField("Комментарий к заказу", blank=True)
    manager_comment = models.TextField("Комментарий менеджера", blank=True)
    subtotal_amount = models.DecimalField("Сумма товаров", max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField("Скидка", max_digits=12, decimal_places=2, default=0)
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField("Код купона", max_length=50, blank=True)
    total_amount = models.DecimalField("Итоговая сумма", max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=50,
        choices=PAYMENT_METHODS,
        default="card"
    )
    status = models.CharField(
        "Статус",
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_name or 'без имени'}"

    def get_status_display_full(self):
        return self.get_status_display()

    def can_be_cancelled(self):
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED]

    def get_items_total(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    product_name = models.CharField("Название товара", max_length=255, blank=True)
    product_sku = models.CharField("Артикул", max_length=100, blank=True)
    price = models.DecimalField("Цена за шт", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("Количество", default=1)
    total_price = models.DecimalField("Сумма", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Товар заказа"
        verbose_name_plural = "Товары заказа"

    def __str__(self):
        return f"{self.product_name or self.product} x {self.quantity}"

    def save(self, *args, **kwargs):
        if self.product:
            self.product_name = self.product.name
            self.product_sku = self.product.sku or ""
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)