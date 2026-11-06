from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Coupon


class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "discount_display",
        "min_order_amount",
        "usage_info",
        "valid_period",
        "active",
        "created_at",
    )
    list_filter = (
        "active",
        "discount_type",
        "created_at",
        "valid_from",
        "valid_to",
    )
    search_fields = (
        "code",
        "name",
    )
    readonly_fields = (
        "usage_count",
        "created_at",
        "updated_at",
        "is_active_now",
    )
    
    fieldsets = (
        (None, {
            "fields": ("code", "name", "active", "is_active_now"),
        }),
        ("Скидка", {
            "fields": (
                "discount_type",
                "discount_value",
                "max_discount",
            ),
            "description": "Тип и размер скидки",
        }),
        ("Ограничения заказа", {
            "fields": (
                "min_order_amount",
                "applicable_categories",
            ),
        }),
        ("Лимиты использования", {
            "fields": (
                "usage_limit",
                "usage_count",
                "per_user_limit",
            ),
        }),
        ("Период действия", {
            "fields": (
                "valid_from",
                "valid_to",
            ),
        }),
        ("Аудит", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    list_editable = ("active",)
    ordering = ("-created_at",)
    
    def discount_display(self, obj):
        """Отображение скидки"""
        if obj.discount_type == "percent":
            return f"{obj.discount_value}%"
        return f"{obj.discount_value} ₽"
    discount_display.short_description = "Скидка"
    
    def usage_info(self, obj):
        """Информация об использовании"""
        if obj.usage_limit == 0:
            return f"{obj.usage_count} / ∞"
        return f"{obj.usage_count} / {obj.usage_limit}"
    usage_info.short_description = "Использование"
    
    def valid_period(self, obj):
        """Период действия"""
        return f"{obj.valid_from.strftime('%d.%m %H:%M')} - {obj.valid_to.strftime('%d.%m %H:%M')}"
    valid_period.short_description = "Действителен"
    
    def is_active_now(self, obj):
        """Активен ли купон сейчас"""
        now = timezone.now()
        if not obj.active:
            return format_html('<span class="text-muted">Неактивен</span>')
        if obj.valid_from and now < obj.valid_from:
            return format_html('<span class="text-warning">Скоро</span>')
        if obj.valid_to and now > obj.valid_to:
            return format_html('<span class="text-danger">Истек</span>')
        return format_html('<span class="text-success">✓ Активен</span>')
    is_active_now.short_description = "Статус"
    
    def save_model(self, request, obj, form, change):
        """Установка периодов при создании"""
        if not change and not obj.valid_from:
            from django.utils import timezone
            obj.valid_from = timezone.now()
            if not obj.valid_to:
                obj.valid_to = obj.valid_from.replace(year=obj.valid_from.year + 1)
        super().save_model(request, obj, form, change)

admin.site.register(Coupon, CouponAdmin)