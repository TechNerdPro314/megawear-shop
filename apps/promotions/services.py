from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.db.models import Q, F          # ← добавлен импорт F
from django.utils import timezone
from .models import Coupon


class CouponService:
    """
    Сервис для управления купонами
    """

    @staticmethod
    def get_by_code(code: str) -> Optional[Coupon]:
        """
        Получает купон по коду (регистронезависимо).
        ВАЖНО: используется поле 'code', а не 'coupon_code'
        """
        try:
            return Coupon.objects.get(code__iexact=code.strip())
        except Coupon.DoesNotExist:
            return None

    @staticmethod
    def validate_coupon(coupon: Coupon, subtotal: Decimal, user=None) -> Dict[str, Any]:
        """
        Проверяет возможность применения купона.
        """
        if not coupon.is_valid():
            if not coupon.active:
                return {'valid': False, 'error': 'Купон неактивен', 'discount': Decimal('0')}
            now = timezone.now()
            if coupon.valid_from and now < coupon.valid_from:
                return {'valid': False, 'error': 'Купон еще не активен', 'discount': Decimal('0')}
            if coupon.valid_to and now > coupon.valid_to:
                return {'valid': False, 'error': 'Срок действия купона истек', 'discount': Decimal('0')}
            if coupon.usage_limit > 0 and coupon.usage_count >= coupon.usage_limit:
                return {'valid': False, 'error': 'Лимит использования исчерпан', 'discount': Decimal('0')}

        if subtotal < coupon.min_order_amount:
            return {
                'valid': False,
                'error': f'Минимальная сумма заказа: {coupon.min_order_amount} ₽',
                'discount': Decimal('0')
            }

        if coupon.per_user_limit > 0 and user and user.is_authenticated:
            used_count = coupon.user_usage_count(user)
            if used_count >= coupon.per_user_limit:
                return {'valid': False, 'error': 'Вы уже использовали этот купон', 'discount': Decimal('0')}

        discount = coupon.calculate_discount(subtotal)
        return {'valid': True, 'error': None, 'discount': discount}

    @staticmethod
    def apply_coupon(coupon: Coupon, user=None) -> None:
        """
        Применяет купон (увеличивает счетчик).
        """
        coupon.increment_usage()

    @staticmethod
    def get_available_coupons(
        subtotal: Decimal = None,
        user=None,
        active_only: bool = True
    ) -> List[Coupon]:
        """
        Получает список доступных купонов.
        """
        now = timezone.now()
        query = Q()

        if active_only:
            query &= Q(active=True)
            query &= Q(valid_to__gt=now)
            query &= Q(valid_from__lte=now)

        # Использование F для сравнения с полем БД
        query &= Q(usage_limit=0) | Q(usage_count__lt=F('usage_limit'))

        coupons = Coupon.objects.filter(query).order_by('-discount_value')

        available = []
        for coupon in coupons:
            if subtotal and coupon.min_order_amount > subtotal:
                continue
            if coupon.per_user_limit > 0 and user and user.is_authenticated:
                if coupon.user_usage_count(user) >= coupon.per_user_limit:
                    continue
            available.append(coupon)
        return available

    @staticmethod
    def create_coupon(
        code: str,
        discount_value: Decimal,
        discount_type: str = "percent",
        min_order_amount: Decimal = Decimal("0"),
        usage_limit: int = 0,
        per_user_limit: int = 0,
        valid_from: timezone.datetime = None,
        valid_to: timezone.datetime = None,
        name: str = "",
        max_discount: Decimal = None,
        active: bool = True
    ) -> Coupon:
        """
        Создает новый купон.
        """
        if valid_from is None:
            valid_from = timezone.now()
        if valid_to is None:
            valid_to = valid_from.replace(year=valid_from.year + 1)

        return Coupon.objects.create(
            code=code.upper(),
            name=name,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_amount=min_order_amount,
            usage_limit=usage_limit,
            per_user_limit=per_user_limit,
            valid_from=valid_from,
            valid_to=valid_to,
            max_discount=max_discount,
            active=active,
        )