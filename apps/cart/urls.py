# apps/cart/urls.py
from django.urls import path
from .views import (
    cart_detail_view,
    add_to_cart_view,
    remove_from_cart_view,
    update_cart_view,
    apply_coupon_view,
    remove_coupon_view,
    set_delivery_view,
    clear_cart_view,
    quick_order_view,
)

app_name = 'cart'

urlpatterns = [
    path("", cart_detail_view, name="cart_detail"),
    path("add/<int:product_id>/", add_to_cart_view, name="add_to_cart"),
    path("remove/<int:product_id>/", remove_from_cart_view, name="remove_from_cart"),
    path("update/<int:product_id>/", update_cart_view, name="update_cart"),
    path("coupon/", apply_coupon_view, name="apply_coupon"),
    path("coupon/remove/", remove_coupon_view, name="remove_coupon"),
    path("delivery/", set_delivery_view, name="set_delivery"),
    path("clear/", clear_cart_view, name="clear_cart"),
    path("quick-order/<int:product_id>/", quick_order_view, name="quick_order"),
]