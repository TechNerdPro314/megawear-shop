# apps/info/urls.py
from django.urls import path
from . import views

app_name = 'info'

urlpatterns = [
    path('promo/', views.PromoListView.as_view(), name='promo'),
    # Остальные страницы можно добавить позже
]