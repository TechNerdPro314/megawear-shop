import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from yookassa import Payment as YooPayment

from apps.orders.models import Order
from .models import Payment
from .services import YooKassaService

logger = logging.getLogger(__name__)


def pay_order(request, order_id):
    # доступ для владельца (или гостя, если разрешено)
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)

    if order.status not in ['new', 'confirmed']:
        messages.warning(request, "Этот заказ не требует оплаты.")
        return redirect('orders:order_detail', order_id=order.id)

    # Если платёж уже был создан и оплачен/ожидает, не дублируем
    if hasattr(order, 'payment') and order.payment.status == 'succeeded':
        return redirect('orders:order_detail', order_id=order.id)

    # Удаляем старый неоплаченный платёж, если есть
    if hasattr(order, 'payment') and order.payment.status in ['pending', 'canceled']:
        order.payment.delete()

    return_url = request.build_absolute_uri(f'/payments/success/?order_id={order.id}')
    payment = YooKassaService.create_payment(order, return_url)
    return redirect(payment.confirmation_url)


@csrf_exempt
def yookassa_callback(request):
    """Webhook для ЮKassa. Не требует CSRF-токена."""
    import json
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    payment = YooKassaService.handle_callback(data)
    if payment:
        return HttpResponse(status=200)
    return HttpResponse(status=400)


def payment_success(request):
    """Страница после возврата с ЮKassa. Проверяет реальный статус платежа."""
    order_id = request.GET.get('order_id')
    if not order_id:
        return redirect('catalog:home')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return redirect('catalog:home')

    # Пытаемся получить платёж из БД
    payment = getattr(order, 'payment', None)
    if payment and payment.yookassa_id:
        try:
            # Запрашиваем актуальный статус из ЮKassa
            yoo_payment = YooPayment.find_one(payment.yookassa_id)
            if yoo_payment.status == 'succeeded':
                # Обновляем локальный статус, если ещё не обновлён
                if payment.status != 'succeeded':
                    payment.status = 'succeeded'
                    payment.paid_at = timezone.now()
                    payment.save()
                    order.status = 'paid'
                    order.save()
                return render(request, 'payments/success.html', {
                    'order': order,
                    'payment': payment,
                    'paid': True
                })
            elif yoo_payment.status == 'pending':
                messages.info(request, "Оплата ещё обрабатывается. Пожалуйста, подождите.")
                return redirect('orders:order_detail', order_id=order.id)
            else:
                # canceled или другой
                messages.warning(request, "Оплата не была завершена. Попробуйте снова.")
                return redirect('orders:order_detail', order_id=order.id)
        except Exception as e:
            logger.error(f"Ошибка проверки платежа {payment.yookassa_id}: {e}")
            messages.error(request, "Не удалось проверить статус оплаты. Свяжитесь с поддержкой.")
            return redirect('orders:order_detail', order_id=order.id)
    else:
        # Нет локальной записи о платеже – что-то пошло не так
        messages.warning(request, "Платёж не найден. Попробуйте оплатить заказ ещё раз.")
        return redirect('orders:order_detail', order_id=order.id)