from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from apps.cart.services import CartService, DELIVERY_OPTIONS
from .forms import CheckoutForm
from .services import CheckoutService, OrderCreationError, StockReservationError
from .tasks import send_order_notifications

def checkout_view(request):
    cart = CartService(request)

    if cart.get_total_quantity() == 0:
        messages.error(request, "Корзина пуста. Добавьте товары перед оформлением заказа.")
        return redirect("cart:cart_detail")

    current_delivery = cart.get_delivery_method()

    if request.method == "POST":
        if not current_delivery:
            messages.error(request, "Пожалуйста, выберите способ доставки.")
            return redirect("orders:checkout")

        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                checkout_service = CheckoutService(request)
                # Передаём payment_method в cleaned_data
                order = checkout_service.create_order(form.cleaned_data)

                # Отправляем уведомления (email и т.п.)
                send_order_notifications.delay(order.id)

                # Если оплата онлайн – перенаправляем на страницу оплаты
                if order.payment_method == 'online':
                    return redirect("payments:pay_order", order_id=order.id)
                else:
                    # Для наличных/в магазине сразу показываем успех
                    return redirect("orders:order_success", order_id=order.id)

            except OrderCreationError as e:
                messages.error(request, f"Ошибка: {e}")
            except StockReservationError as e:
                messages.error(request, f"Товар недоступен: {e}")
            except Exception as e:
                messages.error(request, f"Произошла ошибка: {e}")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial.update({
                "customer_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                "customer_email": request.user.email or "",
                "customer_phone": getattr(request.user, 'phone', '') or "",
            })
        initial['delivery_method'] = current_delivery or ""
        form = CheckoutForm(initial=initial)

    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Корзина', 'url': '/cart/'},
        {'name': 'Оформление заказа'},
    ]
    return render(request, "orders/checkout.html", {
        "form": form,
        "cart": cart,
        "delivery_options": DELIVERY_OPTIONS,
        "current_delivery": current_delivery,
        "breadcrumbs_items": breadcrumbs,
        "page_title": "Оформление заказа",
    })

def order_created_view(request, order_id):
    """Страница подтверждения создания заказа перед оплатой (для онлайн)."""
    from .models import Order
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, "Заказ не найден.")
        return redirect("catalog:product_list")
    if order.status in ["paid", "processing"]:
        return redirect("orders:order_detail", order_id=order.id)
    return render(request, "orders/order_created.html", {"order": order})

def order_detail_view(request, order_id):
    from .models import Order
    # разрешим просмотр без авторизации, если знаем id (можно добавить проверку по email/телефону)
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, "Заказ не найден")
        return redirect("catalog:product_list")
    return render(request, "orders/order_detail.html", {"order": order})

def my_orders_view(request):
    if not request.user.is_authenticated:
        return redirect('users:login')
    from .models import Order
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": orders})

def pay_order_view(request, order_id):
    return redirect("payments:pay_order", order_id=order_id)

def order_success_view(request, order_id):
    from .models import Order
    order = Order.objects.filter(id=order_id).first()
    if not order:
        messages.error(request, "Заказ не найден")
        return redirect("catalog:product_list")
    return render(request, "orders/success.html", {"order": order})