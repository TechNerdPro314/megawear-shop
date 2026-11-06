from django.contrib import admin
from django.utils.html import format_html
from .models import ImportProfile, ImportJob
from .tasks import process_import_job


@admin.register(ImportProfile)
class ImportProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'active', 'update_existing')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'status', 'success_count', 'error_count', 'created_by', 'created_at', 'action_buttons')
    list_filter = ('status', 'profile')
    readonly_fields = ('status', 'log', 'total_rows', 'success_count', 'error_count', 'created_at', 'completed_at')
    fieldsets = (
        (None, {
            'fields': ('profile', 'file', 'created_by')
        }),
        ('Результаты', {
            'fields': ('status', 'total_rows', 'success_count', 'error_count', 'log', 'completed_at')
        }),
    )

    def action_buttons(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">Запустить</a>',
                f'start/{obj.pk}/'
            )
        return ''
    action_buttons.short_description = 'Действия'

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        # Автоматический запуск при создании
        if not change and obj.file:
            process_import_job.delay(obj.pk)
            obj.status = 'processing'
            obj.save(update_fields=['status'])

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                'start/<int:job_id>/',
                self.admin_site.admin_view(self.start_import),
                name='importer_start_import',
            ),
        ]
        return custom_urls + urls

    def start_import(self, request, job_id):
        from django.shortcuts import redirect
        from django.contrib import messages
        try:
            job = ImportJob.objects.get(pk=job_id)
        except ImportJob.DoesNotExist:
            messages.error(request, "Задача не найдена")
            return redirect('admin:importer_importjob_changelist')
        if job.status == 'pending':
            process_import_job.delay(job.id)
            job.status = 'processing'
            job.save(update_fields=['status'])
            messages.success(request, f"Импорт #{job.id} запущен")
        else:
            messages.warning(request, f"Задача уже в статусе {job.get_status_display()}")
        return redirect('admin:importer_importjob_changelist')