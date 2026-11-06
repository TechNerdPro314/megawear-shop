from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.catalog.models import Product
from apps.promotions.models import Coupon as CouponModel
from apps.promotions.services import CouponService

User = get_user_model()

CART_SESSION_ID = "cart"
COUPON_SESSION_ID = "coupon"
DELIVERY_SESSION_ID = "delivery"


DELIVERY_OPTIONS = {
    "courier": {
        "name": "Курьерская доставка",
        "base_cost": Decimal("350"),
        "free_threshold": Decimal("5000"),
        "estimated_days": "1-2 дня",
    },
    "pickup": {
        "name": "Самовывоз",
        "base_cost": Decimal("0"),
        "free_threshold": Decimal("0"),
        "estimated_days": "Сегодня",
    },
    "post": {
        "name": "Почта России",
        "base_cost": Decimal("250"),
        "free_threshold": Decimal("3000"),
        "estimated_days": "3-7 дней",
    },
    "cdek": {
        "name": "СДЭК",
        "base_cost": Decimal("300"),
        "free_threshold": Decimal("4000"),
        "estimated_days": "2-4 дня",
    },
}


class CartItem:
    """Элемент корзины"""
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.total_price = product.price * quantity
    
    @property
    def price(self) -> Decimal:
        return self.product.price


class CartService:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None
        
        self.cart_model = None
        self.cart = {}
        self._cache = {}
        
        if self.user:
            self._init_user_cart()
        else:
            self._load_from_session()

    def _reset_cache(self):
        self._cache = {}

    def _init_user_cart(self):
        from apps.cart.models import Cart as CartModel
        try:
            self.cart_model = self.user.cart
            self._load_from_db()
        except CartModel.DoesNotExist:
            self.cart_model = CartModel.objects.create(user=self.user)
            self.cart = {}
        
        session_cart_data = self.session.get(CART_SESSION_ID, {})
        if session_cart_data:
            self._sync_session_to_db(session_cart_data)
            self.session[CART_SESSION_ID] = {}
            self.session.modified = True

    def _load_from_session(self):
        cart_data = self.session.get(CART_SESSION_ID, {})
        self.cart = {str(k): v for k, v in cart_data.items()}

    def _sync_session_to_db(self, session_cart: dict):
        from apps.cart.models import Cart as CartModel, CartItem as CartItemModel
        if not self.user or not self.cart_model:
            return
        for product_id, item_data in session_cart.items():
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                existing_item = self.cart_model.items.filter(product=product).first()
                if existing_item:
                    new_qty = existing_item.quantity + item_data['quantity']
                    existing_item.quantity = min(new_qty, product.stock)
                    existing_item.save()
                else:
                    qty = min(item_data['quantity'], product.stock)
                    CartItemModel.objects.create(
                        cart=self.cart_model, product=product, quantity=qty
                    )
            except Product.DoesNotExist:
                continue
        self.cart_model.updated_at = timezone.now()
        self.cart_model.save(update_fields=['updated_at'])

    def _load_from_db(self):
        self.cart = {}
        for item in self.cart_model.items.all():
            self.cart[str(item.product_id)] = {'quantity': item.quantity}

    def _save_to_session(self):
        if not self.user:
            self.session[CART_SESSION_ID] = self.cart
            self.session.modified = True

    def _save_to_db(self):
        from apps.cart.models import Cart as CartModel, CartItem as CartItemModel
        if not self.user or not self.cart_model:
            return
        self.cart_model.items.all().delete()
        for product_id, item_data in self.cart.items():
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                CartItemModel.objects.create(
                    cart=self.cart_model, product=product, quantity=item_data['quantity']
                )
            except Product.DoesNotExist:
                continue
        self.cart_model.updated_at = timezone.now()
        self.cart_model.save(update_fields=['updated_at'])

    def save(self):
        if self.user and self.cart_model:
            self._save_to_db()
        else:
            self._save_to_session()
        self._reset_cache()

    def add(self, product_id: int, quantity: int = 1) -> bool:
        product_id = str(product_id)
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return False
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0}
        new_quantity = self.cart[product_id]['quantity'] + quantity
        self.cart[product_id]['quantity'] = min(new_quantity, product.stock)
        self.save()
        return True

    def update(self, product_id: int, quantity: int) -> bool:
        product_id = str(product_id)
        if product_id not in self.cart:
            return False
        if quantity <= 0:
            self.remove(product_id)
            return True
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            self.cart[product_id]['quantity'] = min(quantity, product.stock)
        except Product.DoesNotExist:
            del self.cart[product_id]
        self.save()
        return True

    def remove(self, product_id: int) -> bool:
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
            return True
        return False

    def clear(self):
        from apps.cart.models import Cart as CartModel
        self.cart = {}
        if self.user and self.cart_model:
            self.cart_model.items.all().delete()
            self.cart_model.updated_at = timezone.now()
            self.cart_model.save(update_fields=['updated_at'])
        self.session[CART_SESSION_ID] = {}
        self.session[COUPON_SESSION_ID] = None
        self.session[DELIVERY_SESSION_ID] = None
        self.session.modified = True
        self._reset_cache()

    def __iter__(self):
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = Product.objects.filter(id__in=product_ids, is_active=True).select_related('category', 'brand')
        products_dict = {str(p.id): p for p in products}
        for product_id, item_data in self.cart.items():
            if product_id in products_dict:
                yield CartItem(products_dict[product_id], item_data['quantity'])

    def get_total_quantity(self) -> int:
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal_price(self) -> Decimal:
        if 'subtotal' not in self._cache:
            self._cache['subtotal'] = sum(item.product.price * item.quantity for item in self)
        return self._cache['subtotal']

    def get_coupon(self) -> Optional[Dict[str, Any]]:
        return self.session.get(COUPON_SESSION_ID)

    def apply_coupon(self, code: str) -> Optional[CouponModel]:
        code = code.strip().upper()
        coupon = CouponService.get_by_code(code)
        if not coupon:
            return None
        subtotal = self.get_subtotal_price()
        validation = CouponService.validate_coupon(coupon, subtotal, self.user)
        if not validation['valid']:
            return None
        self.session[COUPON_SESSION_ID] = {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'min_order_amount': str(coupon.min_order_amount),
        }
        self.session.modified = True
        self._reset_cache()
        return coupon

    def remove_coupon(self):
        self.session[COUPON_SESSION_ID] = None
        self.session.modified = True
        self._reset_cache()

    def get_discount_amount(self) -> Decimal:
        if 'discount' not in self._cache:
            coupon_data = self.get_coupon()
            if not coupon_data:
                self._cache['discount'] = Decimal("0.00")
            else:
                try:
                    coupon = CouponService.get_by_code(coupon_data['code'])
                    if not coupon:
                        self.remove_coupon()
                        self._cache['discount'] = Decimal("0.00")
                    else:
                        subtotal = self.get_subtotal_price()
                        validation = CouponService.validate_coupon(coupon, subtotal, self.user)
                        if not validation['valid']:
                            self.remove_coupon()
                            self._cache['discount'] = Decimal("0.00")
                        else:
                            self._cache['discount'] = validation['discount']
                except Exception:
                    self._cache['discount'] = Decimal("0.00")
        return self._cache['discount']

    def get_delivery_method(self) -> Optional[str]:
        return self.session.get(DELIVERY_SESSION_ID)

    def set_delivery_method(self, method: str) -> bool:
        if method not in DELIVERY_OPTIONS:
            return False
        self.session[DELIVERY_SESSION_ID] = method
        self.session.modified = True
        self._reset_cache()   # ← важно сбросить кэш, чтобы пересчиталась стоимость
        return True

    def get_delivery_cost(self) -> Decimal:
        if 'delivery_cost' not in self._cache:
            method = self.get_delivery_method()
            if not method or method not in DELIVERY_OPTIONS:
                self._cache['delivery_cost'] = Decimal("0.00")
            else:
                delivery_info = DELIVERY_OPTIONS[method]
                subtotal = self.get_subtotal_price()
                discount = self.get_discount_amount()
                amount_after_discount = subtotal - discount
                if amount_after_discount >= delivery_info['free_threshold']:
                    self._cache['delivery_cost'] = Decimal("0.00")
                else:
                    self._cache['delivery_cost'] = delivery_info['base_cost']
        return self._cache['delivery_cost']

    def get_delivery_info(self) -> Optional[Dict[str, Any]]:
        method = self.get_delivery_method()
        if not method or method not in DELIVERY_OPTIONS:
            return None
        info = DELIVERY_OPTIONS[method].copy()
        info['cost'] = self.get_delivery_cost()
        info['is_free'] = info['cost'] == Decimal("0.00")
        return info

    def get_final_price(self) -> Decimal:
        if 'final_price' not in self._cache:
            subtotal = self.get_subtotal_price()
            discount = self.get_discount_amount()
            delivery = self.get_delivery_cost()
            total = subtotal - discount + delivery
            self._cache['final_price'] = max(total, Decimal("0.00")).quantize(Decimal("0.01"))
        return self._cache['final_price']

    def get_summary(self) -> Dict[str, Any]:
        delivery_info = self.get_delivery_info()
        coupon_data = self.get_coupon()
        discount = self.get_discount_amount()
        coupon_info = {}
        if coupon_data:
            try:
                coupon = CouponService.get_by_code(coupon_data['code'])
                if coupon:
                    coupon_info = {
                        'code': coupon.code,
                        'discount_type': coupon.discount_type,
                        'discount_value': coupon.discount_value,
                        'discount_percent': coupon.discount_value if coupon.discount_type == 'percent' else 0,
                    }
            except Exception:
                pass
        return {
            'subtotal': self.get_subtotal_price(),
            'discount': discount,
            'coupon_code': coupon_info.get('code'),
            'discount_type': coupon_info.get('discount_type'),
            'discount_percent': coupon_info.get('discount_percent', 0),
            'delivery_cost': self.get_delivery_cost(),
            'delivery_method': delivery_info['name'] if delivery_info else None,
            'delivery_estimated': delivery_info['estimated_days'] if delivery_info else None,
            'total': self.get_final_price(),
            'total_quantity': self.get_total_quantity(),
            'items_count': len(self.cart),
        }