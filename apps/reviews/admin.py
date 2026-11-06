from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_link",
        "user",
        "rating_display",
        "is_verified",
        "status",
        "helpful_count",
        "created_at",
    )
    list_filter = (
        "status",
        "is_verified_purchase",
        "rating",
        "created_at",
    )
    search_fields = (
        "product__name",
        "user__username",
        "user__email",
        "text",
        "title",
    )
    readonly_fields = (
        "user",
        "product",
        "is_verified_purchase",
        "order",
        "created_at",
        "updated_at",
        "helpful_count",
        "not_helpful_count",
    )
    
    fieldsets = (
        (None, {
            "fields": ("product", "user", "rating", "title", "text"),
        }),
        ("Модерация", {
            "fields": ("status", "moderation_comment", "moderated_by", "moderated_at"),
            "classes": ("collapse",),
        }),
        ("Покупка", {
            "fields": ("is_verified_purchase", "order"),
        }),
        ("Статистика", {
            "fields": ("helpful_count", "not_helpful_count", "created_at", "updated_at"),
        }),
    )
    
    list_editable = ("status",)
    ordering = ("-created_at",)
    
    def product_link(self, obj):
        return format_html(
            '<a href="/admin/catalog/product/{}/change/">{}</a>',
            obj.product.id,
            obj.product.name[:50]
        )
    product_link.short_description = "Товар"
    
    def rating_display(self, obj):
        return format_html("⭐" * obj.rating)
    rating_display.short_description = "Рейтинг"
    
    def is_verified(self, obj):
        if obj.is_verified_purchase:
            return format_html('<span class="text-success">✓ Подтверждена</span>')
        return format_html('<span class="text-muted">—</span>')
    is_verified.short_description = "Покупка"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product", "user")
