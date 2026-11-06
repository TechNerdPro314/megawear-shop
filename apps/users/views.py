import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from django.urls import reverse

from apps.notifications.models import Notification

User = get_user_model()

from .forms import RegisterForm, ProfileForm, PasswordResetForm


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect("catalog:home")

    form = RegisterForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        
        # ИЗМЕНЕНО: Делаем пользователя активным по умолчанию
        user.is_active = True 
        user.save()
        
        # ИЗМЕНЕНО: Отключаем отправку письма активации, так как она больше не нужна
        # _send_activation_email(request, user)
        
        # ИЗМЕНЕНО: Сразу авторизуем пользователя для удобства
        login(request, user)
        
        messages.success(
            request, 
            "Регистрация прошла успешно! Добро пожаловать."
        )
        return redirect("catalog:home")

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """Вход в аккаунт"""
    if request.user.is_authenticated:
        return redirect("catalog:home")

    form = AuthenticationForm(request, data=request.POST or None)

    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        
        if user:
            if not user.is_active:
                messages.warning(
                    request, 
                    "Аккаунт не активирован."
                )
                return redirect("users:login")
                
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.first_name or user.username}!")
            
            # Обработка редиректа на запрошенную страницу
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url) if next_url else redirect("catalog:home")

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    """Выход из аккаунта"""
    logout(request)
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect("catalog:home")


@login_required
def profile_view(request):
    """Просмотр профиля"""
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, "Профиль обновлён.")
        return redirect("users:profile")

    # Получаем заказы пользователя (предполагаем related_name='orders')
    orders_manager = getattr(request.user, 'orders', None)
    if orders_manager:
        # Исключаем отменённые заказы из статистики
        valid_orders = orders_manager.exclude(status='cancelled')
        orders_count = valid_orders.count()
        total_spent = valid_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        recent_orders = orders_manager.order_by('-created_at')[:5]
    else:
        orders_count = 0
        total_spent = 0
        recent_orders = []

    context = {
        "form": form,
        "orders_count": orders_count,
        "total_spent": total_spent,
        "recent_orders": recent_orders,
    }
    return render(request, "users/profile.html", context)


@login_required
@never_cache
def notifications_view(request):
    """Страница уведомлений пользователя"""
    notifications = request.user.notifications.all().order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    mark_id = request.GET.get('mark_read')
    if mark_id:
        notif = get_object_or_404(Notification, pk=mark_id, user=request.user)
        if not notif.is_read:
            notif.is_read = True
            notif.save()
        # Принудительно обновляем страницу, добавляя случайный параметр
        return redirect(f'{reverse("users:notifications")}?ref={uuid.uuid4().hex[:6]}')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/notifications.html', {
        'notifications': page_obj,
        'unread_count': unread_count,
    })


@login_required
def profile_edit_view(request):
    """Редактирование профиля — отдельная страница"""
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, "Профиль успешно обновлён.")
        return redirect("users:profile")

    return render(request, "users/profile_edit.html", {
        "form": form,
        "page_title": "Редактирование профиля"
    })


@login_required
def password_change_view(request):
    """Смена пароля (для авторизованных пользователей)"""
    form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # Не разлогинивать после смены пароля
        messages.success(request, "Пароль успешно изменён.")
        return redirect("users:profile")

    return render(request, "users/password_change.html", {
        "form": form,
        "page_title": "Смена пароля"
    })


def password_reset_view(request):
    """Запрос сброса пароля"""
    if request.user.is_authenticated:
        return redirect("users:profile")
        
    form = PasswordResetForm(data=request.POST or None)

    if form.is_valid():
        email = form.cleaned_data["email"]
        users = User.objects.filter(email=email, is_active=True)
        
        if users.exists():
            _send_password_reset_email(request, users.first())
            
        messages.success(
            request, 
            "Если аккаунт с таким email существует, вы получите инструкцию по сбросу пароля."
        )
        return redirect("users:login")

    return render(request, "users/password_reset.html", {
        "form": form,
        "page_title": "Восстановление пароля"
    })


def password_reset_confirm_view(request, uidb64, token):
    """Подтверждение сброса пароля по ссылке из email"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        form = SetPasswordForm(user=user, data=request.POST or None)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Пароль успешно изменён. Теперь вы можете войти.")
            return redirect("users:login")
            
        return render(request, "users/password_reset_confirm.html", {
            "form": form,
            "valid_link": True,
            "page_title": "Новый пароль"
        })
    else:
        return render(request, "users/password_reset_confirm.html", {
            "valid_link": False,
            "page_title": "Ссылка недействительна"
        })


@login_required
@transaction.atomic
def delete_account_view(request):
    """Удаление аккаунта пользователя"""
    if request.method != "POST":
        return redirect("users:profile")
    
    password = request.POST.get("password_confirm")
    user = request.user
    
    if not authenticate(username=user.username, password=password):
        messages.error(request, "Неверный пароль. Удаление отменено.")
        return redirect("users:profile")
    
    user_email = user.email
    username = user.username
    
    # Анонимизация данных (сохраняем историю заказов)
    user.email = f"deleted_{user.id}@deleted.local"
    user.username = f"deleted_{user.id}"
    user.first_name = ""
    user.last_name = ""
    user.phone = ""
    user.is_active = False
    user.save()
    
    logout(request)
    
    # Уведомление об удалении (уйдет в dummy backend, никому не придет)
    try:
        send_mail(
            subject="Ваш аккаунт MegaMart удалён",
            message=f"Здравствуйте,\n\nВаш аккаунт '{username}' был успешно удалён.\n"
                   f"Если это сделали не вы, срочно свяжитесь с поддержкой.\n\n"
                   f"С уважением,\nКоманда MegaMart",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=True,
        )
    except Exception:
        pass
    
    messages.success(request, "Ваш аккаунт успешно удалён. Спасибо, что были с нами!")
    return redirect("catalog:home")


def activate_account_view(request, uidb64, token):
    """Активация аккаунта по ссылке из письма (оставлено для совместимости)"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if user.is_active:
            messages.info(request, "Аккаунт уже активирован. Можете войти.")
        else:
            user.is_active = True
            user.save()
            messages.success(request, "Аккаунт активирован! Теперь вы можете войти.")
        return redirect("users:login")
    else:
        messages.error(request, "Ссылка активации недействительна или истекла.")
        return redirect("users:register")


# Вспомогательные функции отправки email (оставлены, но не вызываются)

def _send_activation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    current_site = get_current_site(request)
    activate_url = request.build_absolute_uri(f"/users/activate/{uid}/{token}/")
    
    subject = "Активация аккаунта MegaMart"
    message = render_to_string("users/emails/activation_email.txt", {
        "user": user, "activate_url": activate_url, "site_name": current_site.name
    })
    html_message = render_to_string("users/emails/activation_email.html", {
        "user": user, "activate_url": activate_url, "site_name": current_site.name
    })
    
    send_mail(
        subject=subject, message=message, html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], fail_silently=False,
    )


def _send_password_reset_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    current_site = get_current_site(request)
    reset_url = request.build_absolute_uri(f"/users/password-reset-confirm/{uid}/{token}/")
    
    subject = "Сброс пароля MegaMart"
    message = render_to_string("users/emails/password_reset_email.txt", {
        "user": user, "reset_url": reset_url, "site_name": current_site.name
    })
    html_message = render_to_string("users/emails/password_reset_email.html", {
        "user": user, "reset_url": reset_url, "site_name": current_site.name
    })
    
    send_mail(
        subject=subject, message=message, html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], fail_silently=False,
    )