import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import yookassa
from yookassa import Payment as YooPayment
from .models import Payment as PaymentModel

yookassa.Configuration.account_id = settings.YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

class YooKassaService:
    @staticmethod
    def create_payment(order, return_url):
        """Создаёт платёж в ЮKassa и запись в БД."""
        payment = PaymentModel.objects.create(
            order=order,
            amount=order.total_amount,
            status='pending'
        )

        idempotence_key = str(uuid.uuid4())
        yoo_payment = YooPayment.create({
            "amount": {
                "value": str(order.total_amount.quantize(Decimal('0.01'))),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": f"Заказ №{order.id}",
            "metadata": {
                "order_id": order.id,
                "payment_id": payment.id.hex  # для поиска при колбэке
            }
        }, idempotence_key)

        payment.yookassa_id = yoo_payment.id
        payment.status = yoo_payment.status
        payment.confirmation_url = yoo_payment.confirmation.confirmation_url
        payment.save()

        return payment

    @staticmethod
    def handle_callback(data):
        """Обрабатывает уведомление от YooKassa."""
        try:
            yoo_payment = YooPayment.find_one(data['object']['id'])
        except Exception:
            return None

        payment_id = yoo_payment.metadata.get('payment_id')
        if not payment_id:
            return None

        try:
            payment = PaymentModel.objects.get(id=payment_id)
        except PaymentModel.DoesNotExist:
            return None

        payment.status = yoo_payment.status
        payment.yookassa_id = yoo_payment.id
        if yoo_payment.status == 'succeeded' and not payment.paid_at:
            payment.paid_at = timezone.now()
            # Обновляем статус заказа
            payment.order.status = 'paid'
            payment.order.save()
        elif yoo_payment.status == 'canceled':
            payment.order.status = 'canceled'
            payment.order.save()
        payment.save()
        return payment