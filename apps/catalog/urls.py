from django.urls import path
from django.shortcuts import redirect
from .views import HomePageView, ProductListView, ProductDetailView

app_name = 'catalog'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/all/', ProductListView.as_view(), name='product_list_all'),
    # редирект на корректный путь /products/?category=...
    path('category/<slug:category>/', lambda request, category: redirect(f'/products/?category={category}'), name='product_list_by_category'),
    path('brand/<slug:brand>/', lambda request, brand: redirect(f'/products/?brand={brand}'), name='product_list_by_brand'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]