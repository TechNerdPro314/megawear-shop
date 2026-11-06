# apps/orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('created/<int:order_id>/', views.order_created_view, name='order_created'),
    path('<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('my/', views.my_orders_view, name='my_orders'),
    path('pay/<int:order_id>/', views.pay_order_view, name='pay_order'),
    path('success/<int:order_id>/', views.order_success_view, name='order_success'),
]