from decimal import Decimal
from django.db import models
from django.db.models import F, Sum
from django.conf import settings
from django.utils import timezone


class Cart(models.Model):
    """Корзина пользователя в БД"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Cart for {self.user.username}"

    def clear(self):
        """Очистка всех товаров в корзине"""
        self.items.all().delete()
    
    def get_total_quantity(self) -> int:
        """Общее количество товаров в корзине"""
        return self.items.aggregate(total=models.Sum('quantity', default=0))['total'] or 0
    
    def get_subtotal(self) -> Decimal:
        """Сумма товаров без скидок и доставки (Исправленный ORM запрос)"""
        result = self.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total']
        return Decimal(result) if result is not None else Decimal('0.00')
    
    def add_item(self, product, quantity: int = 1):
        """Добавление товара в корзину"""
        item, created = self.items.get_or_create(product=product)
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()
        return item
    
    def remove_item(self, product):
        """Удаление товара из корзины"""
        self.items.filter(product=product).delete()
    
    def update_item_quantity(self, product, quantity: int):
        """Обновление количества товара"""
        if quantity <= 0:
            self.remove_item(product)
        else:
            self.items.filter(product=product).update(quantity=quantity)


class CartItem(models.Model):
    """Элемент корзины"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        """Оптимизированный метод сохранения с обновлением родительской корзины"""
        super().save(*args, **kwargs)
        # Явно обновляем дату изменения корзины с использованием timezone
        self.cart.updated_at = timezone.now()
        self.cart.save(update_fields=['updated_at'])