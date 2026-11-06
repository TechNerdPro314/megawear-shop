# apps/cart/views.py
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from apps.catalog.models import Product
from .services import CartService

def cart_detail_view(request):
    cart = CartService(request)
    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Корзина'},
    ]
    return render(request, "cart/cart.html", {
        "cart": cart,
        "breadcrumbs_items": breadcrumbs,
        "page_title": "Корзина",
    })

@require_POST
def add_to_cart_view(request, product_id):
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    qty = max(1, int(request.POST.get("quantity", 1)))
    success = cart.add(product.id, qty)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        summary = cart.get_summary()
        return JsonResponse({
            'success': success,
            'total_quantity': summary['total_quantity'],
            'subtotal': round(float(summary['subtotal']), 2),
            'discount': round(float(summary.get('discount', 0)), 2),
            'delivery_cost': round(float(summary.get('delivery_cost', 0)), 2),
            'total': round(float(summary['total']), 2),
            'items_count': summary['items_count'],
            'message': f"{product.name} добавлен." if success else "Не удалось добавить.",
        })

    if success:
        messages.success(request, f"{product.name} добавлен в корзину.")
    else:
        messages.error(request, "Не удалось добавить товар.")
    return redirect("cart:cart_detail")

@require_POST
def remove_from_cart_view(request, product_id):
    cart = CartService(request)
    cart.remove(product_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        summary = cart.get_summary()
        return JsonResponse({
            'success': True,
            'total_quantity': summary['total_quantity'],
            'subtotal': round(float(summary['subtotal']), 2),
            'discount': round(float(summary.get('discount', 0)), 2),
            'delivery_cost': round(float(summary.get('delivery_cost', 0)), 2),
            'total': round(float(summary['total']), 2),
            'items_count': summary['items_count'],
        })
    messages.info(request, "Товар удалён из корзины.")
    return redirect("cart:cart_detail")

@require_POST
def update_cart_view(request, product_id):
    cart = CartService(request)
    qty = max(0, int(request.POST.get("quantity", 1)))
    success = cart.update(product_id, qty)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        summary = cart.get_summary()
        return JsonResponse({
            'success': success,
            'total_quantity': summary['total_quantity'],
            'subtotal': round(float(summary['subtotal']), 2),
            'discount': round(float(summary.get('discount', 0)), 2),
            'delivery_cost': round(float(summary.get('delivery_cost', 0)), 2),
            'total': round(float(summary['total']), 2),
            'items_count': summary['items_count'],
        })
    messages.success(request, "Корзина обновлена.")
    return redirect("cart:cart_detail")

@require_POST
def apply_coupon_view(request):
    cart = CartService(request)
    code = request.POST.get("coupon", "").strip()
    if not code:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Введите код купона.'})
        messages.error(request, "Введите код купона.")
        return redirect("cart:cart_detail")

    coupon = cart.apply_coupon(code)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if coupon:
            summary = cart.get_summary()
            return JsonResponse({
                'success': True,
                'message': f"Купон {coupon.code} применён.",
                'coupon_code': coupon.code,
                'discount': round(float(summary.get('discount', 0)), 2),
                'subtotal': round(float(summary['subtotal']), 2),
                'delivery_cost': round(float(summary.get('delivery_cost', 0)), 2),
                'total': round(float(summary['total']), 2),
            })
        else:
            return JsonResponse({'success': False, 'message': 'Купон недействителен.'})
    if coupon:
        messages.success(request, f"Купон {coupon.code} применён.")
    else:
        messages.error(request, "Купон недействителен.")
    return redirect("cart:cart_detail")

@require_POST
def remove_coupon_view(request):
    cart = CartService(request)
    cart.remove_coupon()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        summary = cart.get_summary()
        return JsonResponse({
            'success': True,
            'message': 'Купон удалён.',
            'discount': 0,
            'subtotal': round(float(summary['subtotal']), 2),
            'delivery_cost': round(float(summary.get('delivery_cost', 0)), 2),
            'total': round(float(summary['total']), 2),
        })
    messages.info(request, "Купон удалён.")
    return redirect("cart:cart_detail")

@require_POST
def set_delivery_view(request):
    cart = CartService(request)
    method = request.POST.get("delivery_method", "")
    success = cart.set_delivery_method(method)
    summary = cart.get_summary()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'subtotal': round(float(summary['subtotal']), 2),
            'delivery_cost': round(float(summary['delivery_cost']), 2),
            'discount': round(float(summary.get('discount', 0)), 2),
            'total': round(float(summary['total']), 2),
        })
    if success:
        messages.success(request, "Способ доставки изменён.")
    else:
        messages.error(request, "Неверный способ доставки.")
    return redirect("cart:cart_detail")

@require_POST
def clear_cart_view(request):
    cart = CartService(request)
    cart.clear()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'total_quantity': 0,
            'subtotal': 0.0,
            'discount': 0.0,
            'delivery_cost': 0.0,
            'total': 0.0,
            'items_count': 0,
        })
    messages.info(request, "Корзина очищена.")
    return redirect("cart:cart_detail")

@require_POST
def quick_order_view(request, product_id):
    """Покупка в один клик: добавляет товар в корзину и сразу переходит к оформлению."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = CartService(request)
    cart.add(product.id, 1)
    return redirect('orders:checkout')