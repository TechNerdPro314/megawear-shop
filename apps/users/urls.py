# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    
    # Password
    path('password-change/', views.password_change_view, name='password_change'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Account
    path('delete/', views.delete_account_view, name='delete_account'),
    path('activate/<uidb64>/<token>/', views.activate_account_view, name='activate'),
]