from decimal import Decimal
from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from apps.cart.services import CartService
from apps.catalog.models import Product
from .models import Order, OrderItem, OrderStatus


class OrderCreationError(Exception):
    pass


class StockReservationError(Exception):
    pass


class CheckoutService:
    def __init__(self, request):
        self.request = request
        self.cart = CartService(request)

    @transaction.atomic
    def create_order(self, cleaned_data: Dict[str, Any]) -> Order:
        delivery_method = cleaned_data.pop('delivery_method', None)
        if not delivery_method:
            delivery_method = self.cart.get_delivery_method()
        if not delivery_method:
            raise OrderCreationError("Выберите способ доставки")

        if self.cart.get_delivery_method() != delivery_method:
            self.cart.set_delivery_method(delivery_method)

        if self.cart.get_total_quantity() == 0:
            raise OrderCreationError("Корзина пуста")

        self._validate_and_reserve_stock()

        subtotal = self.cart.get_subtotal_price()
        discount = self.cart.get_discount_amount()
        delivery_cost = self.cart.get_delivery_cost()
        total = self.cart.get_final_price()
        coupon_data = self.cart.get_coupon()
        coupon_code = coupon_data['code'] if coupon_data else ""

        order = Order.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            customer_name=cleaned_data.get("customer_name", ""),
            customer_phone=cleaned_data.get("customer_phone", ""),
            customer_email=cleaned_data.get("customer_email", ""),
            delivery_address=cleaned_data.get("delivery_address", ""),
            delivery_method=delivery_method,
            comment=cleaned_data.get("comment", ""),
            payment_method=cleaned_data.get("payment_method", "card"),
            subtotal_amount=subtotal,
            discount_amount=discount,
            delivery_cost=delivery_cost,
            coupon_code=coupon_code,
            total_amount=total,
            status=OrderStatus.NEW,
        )

        for item in self.cart:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_sku=item.product.sku or "",
                price=item.product.price,
                quantity=item.quantity,
                total_price=item.total_price,
            )

        # Отправляем уведомления через Celery (задача в tasks.py)
        from .tasks import send_order_notifications
        send_order_notifications.delay(order.id)

        self.cart.clear()
        return order

    def _validate_and_reserve_stock(self):
        for item in self.cart:
            product = item.product
            if not product.is_active:
                raise StockReservationError(f"Товар '{product.name}' больше не доступен")
            if product.stock < item.quantity:
                raise StockReservationError(
                    f"Недостаточно товара '{product.name}'. "
                    f"Доступно: {product.stock}, требуется: {item.quantity}"
                )
            product.stock = max(0, product.stock - item.quantity)
            product.save(update_fields=['stock', 'updated_at'])