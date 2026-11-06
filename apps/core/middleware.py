"""
Middleware для приложения core
"""
from typing import Callable
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.conf import settings


class CartSyncMiddleware:
    """
    Middleware для синхронизации корзины при логине пользователя.
    
    При входе авторизованного пользователя:
    1. Проверяет наличие корзины в сессии
    2. Если есть - переносит товары в БД корзину пользователя
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)


@receiver(user_logged_in)
def sync_cart_on_login(sender, request, user, **kwargs):
    """
    Сигнал: синхронизация корзины при логине пользователя.
    
    Объединяет корзину из сессии с БД корзиной пользователя.
    """
    from apps.cart.services import CART_SESSION_ID, CartService
    
    session_cart = request.session.get(CART_SESSION_ID)
    if not session_cart:
        return
    
    # Инициализируем CartService для синхронизации
    cart_service = CartService(request)
    # Логика синхронизации уже реализована в _init_user_cart