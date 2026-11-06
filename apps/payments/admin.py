from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'yookassa_id',
        'status',
        'amount',
        'created_at',
        'paid_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'yookassa_id']
    readonly_fields = [
        'yookassa_id',
        'status',
        'amount',
        'confirmation_url',
        'paid_at',
        'created_at',
    ]
    fieldsets = (
        (None, {
            'fields': ('order', 'amount', 'status', 'confirmation_url')
        }),
        ('Данные ЮKassa', {
            'fields': ('yookassa_id',),
        }),
        ('Даты', {
            'fields': ('created_at', 'paid_at'),
        }),
    )