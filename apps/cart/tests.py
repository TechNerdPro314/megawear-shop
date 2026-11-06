"""
Тесты для приложения cart
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings

from apps.cart.services import CartService, DELIVERY_OPTIONS
from apps.catalog.models import Category, Product
from apps.cart.models import Cart, CartItem


User = get_user_model()


def add_session_to_request(request):
    """Добавляет сессию к запросу для тестов"""
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


class CartServiceTest(TestCase):
    """Тесты для CartService"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product1 = Product.objects.create(
            name='Товар 1',
            slug='product-1',
            category=self.category,
            price=Decimal('1000.00'),
            stock=100,
            is_active=True
        )
        self.product2 = Product.objects.create(
            name='Товар 2',
            slug='product-2',
            category=self.category,
            price=Decimal('2000.00'),
            stock=50,
            is_active=True
        )
    
    def _create_request(self, user=None):
        """Создаёт запрос с сессией"""
        request = self.factory.get('/cart/')
        request = add_session_to_request(request)
        if user:
            request.user = user
        else:
            request.user = AnonymousUser()
        return request
    
    def test_cart_add_item(self):
        """Тест добавления товара в корзину"""
        request = self._create_request()
        cart = CartService(request)
        
        result = cart.add(self.product1.id, 2)
        
        self.assertTrue(result)
        self.assertEqual(cart.get_total_quantity(), 2)
        self.assertEqual(cart.get_subtotal_price(), Decimal('2000.00'))
    
    def test_cart_update_quantity(self):
        """Тест обновления количества товара"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 1)
        cart.update(self.product1.id, 5)
        
        self.assertEqual(cart.get_total_quantity(), 5)
        self.assertEqual(cart.get_subtotal_price(), Decimal('5000.00'))
    
    def test_cart_remove_item(self):
        """Тест удаления товара из корзины"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 2)
        cart.remove(self.product1.id)
        
        self.assertEqual(cart.get_total_quantity(), 0)
    
    def test_cart_clear(self):
        """Тест очистки корзины"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 2)
        cart.add(self.product2.id, 1)
        cart.clear()
        
        self.assertEqual(cart.get_total_quantity(), 0)
        self.assertIsNone(cart.get_coupon())
    
    def test_apply_coupon(self):
        """Тест применения купона"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 2)  # 2000 руб
        
        coupon = cart.apply_coupon('SALE10')
        
        self.assertIsNotNone(coupon)
        self.assertEqual(coupon.code, 'SALE10')
        self.assertEqual(cart.get_discount_amount(), Decimal('200.00'))
    
    def test_coupon_min_order_amount(self):
        """Тест минимальной суммы заказа для купона"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 1)  # 1000 руб < 5000 руб (мин для VIP20)
        
        coupon = cart.apply_coupon('VIP20')
        
        self.assertIsNone(coupon)
    
    def test_remove_coupon(self):
        """Тест удаления купона"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 2)
        cart.apply_coupon('SALE10')
        cart.remove_coupon()
        
        self.assertIsNone(cart.get_coupon())
        self.assertEqual(cart.get_discount_amount(), Decimal('0.00'))
    
    def test_delivery_cost(self):
        """Тест расчета стоимости доставки"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 1)
        cart.set_delivery_method('courier')
        
        self.assertEqual(cart.get_delivery_cost(), Decimal('350.00'))
    
    def test_free_delivery_threshold(self):
        """Тест бесплатной доставки при превышении порога"""
        request = self._create_request()
        cart = CartService(request)
        
        # 20 товаров по 1000 руб = 20000 руб > 5000 руб (порог для курьера)
        cart.add(self.product1.id, 20)
        cart.set_delivery_method('courier')
        
        self.assertEqual(cart.get_delivery_cost(), Decimal('0.00'))
    
    def test_final_price_calculation(self):
        """Тест расчета итоговой суммы"""
        request = self._create_request()
        cart = CartService(request)
        
        cart.add(self.product1.id, 2)  # 2000 руб
        cart.apply_coupon('SALE10')    # скидка 200 руб
        cart.set_delivery_method('courier')  # доставка 350 руб
        
        # 2000 - 200 + 350 = 2150
        self.assertEqual(cart.get_final_price(), Decimal('2150.00'))
    
    def test_anonymous_user_cart(self):
        """Тест корзины для анонимного пользователя"""
        request = self.factory.get('/cart/')
        request = add_session_to_request(request)
        request.user = AnonymousUser()
        
        cart = CartService(request)
        cart.add(self.product1.id, 3)
        
        self.assertEqual(cart.get_total_quantity(), 3)
        self.assertIn('cart', request.session)


class CartModelTest(TestCase):
    """Тесты для моделей Cart и CartItem"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            category=self.category,
            price=Decimal('1000.00'),
            stock=100,
            is_active=True
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            category=self.category,
            price=Decimal('2000.00'),
            stock=50,
            is_active=True
        )
    
    def test_cart_creation(self):
        """Тест создания корзины"""
        cart = Cart.objects.create(user=self.user)
        
        self.assertIsNotNone(cart.created_at)
        self.assertIsNotNone(cart.updated_at)
        self.assertEqual(str(cart), f"Cart for {self.user.username}")
    
    def test_cart_add_item(self):
        """Тест добавления товара в корзину модели"""
        cart = Cart.objects.create(user=self.user)
        item = cart.add_item(self.product1, 2)
        
        self.assertEqual(item.quantity, 2)
        self.assertEqual(cart.get_total_quantity(), 2)
    
    def test_cart_get_subtotal(self):
        """Тест подсчета суммы корзины"""
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)  # 2000
        cart.add_item(self.product2, 1)  # 2000
        
        self.assertEqual(cart.get_subtotal(), Decimal('4000.00'))
    
    def test_cart_clear(self):
        """Тест очистки корзины модели"""
        cart = Cart.objects.create(user=self.user)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        
        cart.clear()
        
        self.assertEqual(cart.items.count(), 0)


class CartPersistenceTest(TestCase):
    """Тесты persistence корзины для авторизованных пользователей"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            name='Product',
            slug='product',
            category=self.category,
            price=Decimal('1000.00'),
            stock=100,
            is_active=True
        )
    
    def _create_request(self, user):
        request = self.factory.get('/cart/')
        request = add_session_to_request(request)
        request.user = user
        return request
    
    def test_cart_saved_to_db(self):
        """Тест сохранения корзины в БД"""
        request = self._create_request(self.user)
        cart = CartService(request)
        
        cart.add(self.product.id, 3)
        cart.save()
        
        # Проверяем, что корзина создана в БД
        self.assertTrue(Cart.objects.filter(user=self.user).exists())
        
        db_cart = Cart.objects.get(user=self.user)
        self.assertEqual(db_cart.items.count(), 1)
        self.assertEqual(db_cart.items.first().quantity, 3)
    
    def test_cart_loads_from_db(self):
        """Тест загрузки корзины из БД"""
        # Создаем корзину в БД
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=5)
        
        request = self._create_request(self.user)
        cart_service = CartService(request)
        
        self.assertEqual(cart_service.get_total_quantity(), 5)