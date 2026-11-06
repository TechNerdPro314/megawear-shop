from django.urls import path
from . import views

app_name = 'comparison'

urlpatterns = [
    path('', views.comparison_view, name='compare'),
    path('add/<int:product_id>/', views.add_to_comparison, name='add_to_comparison'),
    path('remove/<int:product_id>/', views.remove_from_comparison, name='remove_from_comparison'),
    path('remove-all/', views.remove_all_comparison, name='remove_all'),
]