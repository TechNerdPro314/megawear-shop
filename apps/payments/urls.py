from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('pay/<int:order_id>/', views.pay_order, name='pay_order'),
    path('callback/', views.yookassa_callback, name='yookassa_callback'),
    path('success/', views.payment_success, name='payment_success'),
]