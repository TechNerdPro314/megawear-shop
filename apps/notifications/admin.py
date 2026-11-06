from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Статус', {
            'fields': ('is_read',)
        }),
        ('Связь с объектом', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'send_mass_notification']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} уведомлений отмечено прочитанными.')
    mark_as_read.short_description = 'Отметить как прочитанные'

    def send_mass_notification(self, request, queryset):
        # Здесь queryset не используется – открываем форму для массовой рассылки
        from django.http import HttpResponseRedirect
        from django.urls import path
        # Перенаправляем на custom view
        return HttpResponseRedirect('../send-mass/')
    send_mass_notification.short_description = 'Создать массовое уведомление'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('send-mass/', self.admin_site.admin_view(self.send_mass_view), name='notification_send_mass'),
        ]
        return custom_urls + urls

    def send_mass_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
        from django import forms

        class MassNotificationForm(forms.Form):
            title = forms.CharField(label='Заголовок', max_length=255)
            message = forms.CharField(label='Сообщение', widget=forms.Textarea)
            notification_type = forms.ChoiceField(label='Тип', choices=Notification.TYPE_CHOICES)
            target = forms.ChoiceField(label='Получатели', choices=[
                ('all', 'Всем активным пользователям'),
                ('selected', 'Выбранным пользователям'),
            ])
            users = forms.ModelMultipleChoiceField(
                queryset=User.objects.filter(is_active=True),
                required=False,
                label='Пользователи'
            )

        if request.method == 'POST':
            form = MassNotificationForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data['title']
                message = form.cleaned_data['message']
                ntype = form.cleaned_data['notification_type']
                target = form.cleaned_data['target']

                if target == 'all':
                    users = User.objects.filter(is_active=True)
                else:
                    users = form.cleaned_data['users']

                created = 0
                for user in users:
                    Notification.objects.create(
                        user=user,
                        title=title,
                        message=message,
                        notification_type=ntype,
                    )
                    created += 1
                self.message_user(request, f'Уведомления отправлены {created} пользователям.')
                return redirect('admin:notifications_notification_changelist')
        else:
            form = MassNotificationForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
            title='Создать массовое уведомление',
        )
        return render(request, 'admin/notifications/send_mass.html', context)