from django.urls import path
from .views import coupon_list_view, coupon_check_view

app_name = "promotions"

urlpatterns = [
    path("api/coupons/", coupon_list_view, name="coupon_list"),
    path("api/coupons/check/", coupon_check_view, name="coupon_check"),
]
