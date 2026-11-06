from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.promotions.services import CouponService


class Command(BaseCommand):
    help = 'Создание тестовых купонов'

    def add_arguments(self, self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие купоны перед созданием'
        )

    def handle(self, *args, **options):
        if options['clear']:
            from apps.promotions.models import Coupon
            count = Coupon.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'Удалено купонов: {count}'))

        coupons = [
            {
                'code': 'SALE10',
                'discount_value': 10,
                'discount_type': 'percent',
                'min_order_amount': 0,
                'name': 'Сезонная распродажа 10%',
            },
            {
                'code': 'VIP20',
                'discount_value': 20,
                'discount_type': 'percent',
                'min_order_amount': 5000,
                'name': 'VIP скидка 20% от 5000 ₽',
            },
            {
                'code': 'WELCOME5',
                'discount_value': 5,
                'discount_type': 'percent',
                'min_order_amount': 0,
                'name': 'Приветственная скидка 5%',
            },
            {
                'code': 'FLAT300',
                'discount_value': 300,
                'discount_type': 'fixed',
                'min_order_amount': 2000,
                'name': 'Скидка 300 ₽ от 2000 ₽',
            },
            {
                'code': 'BIGSAVE',
                'discount_value': 15,
                'discount_type': 'percent',
                'min_order_amount': 10000,
                'max_discount': 2000,
                'name': 'Большая скидка 15% от 10000 ₽ (макс. 2000 ₽)',
            },
        ]

        created = 0
        for coupon_data in coupons:
            try:
                coupon = CouponService.create_coupon(
                    **coupon_data,
                    valid_from=timezone.now(),
                    valid_to=timezone.now() + timedelta(days=365),
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Создан купон: {coupon.code}')
                )
                created += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Ошибка при создании {coupon_data["code"]}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nВсего создано купонов: {created}')
        )