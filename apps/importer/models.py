import json
from django.db import models
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone


class ImportProfile(models.Model):
    """Профиль импорта – настройка маппинга полей и правил"""
    name = models.CharField("Название профиля", max_length=200)
    field_mapping = models.JSONField(
        "Маппинг полей",
        encoder=DjangoJSONEncoder,
        default=dict,
        help_text='Пример: {"sku": "Артикул", "name": "Наименование", "price": "Цена"}'
    )
    default_values = models.JSONField(
        "Значения по умолчанию",
        encoder=DjangoJSONEncoder,
        default=dict,
        blank=True,
        help_text='Пример: {"category__name": "Сантехника", "is_active": true}'
    )
    default_category = models.ForeignKey(
        'catalog.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория по умолчанию"
    )
    default_brand = models.ForeignKey(
        'catalog.Brand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Бренд по умолчанию"
    )
    skip_header = models.BooleanField("Пропустить первую строку", default=True)
    sheet_name = models.CharField(
        "Имя листа",
        max_length=100,
        blank=True,
        help_text="Оставьте пустым для первого листа"
    )
    update_existing = models.BooleanField(
        "Обновлять существующие товары",
        default=True,
        help_text="Если товар с таким SKU уже есть – обновить его данные"
    )
    active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Профиль импорта"
        verbose_name_plural = "Профили импорта"
        ordering = ['-id']

    def __str__(self):
        return self.name


class ImportJob(models.Model):
    """Конкретная задача импорта – файл + профиль + результат"""
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('processing', 'Выполняется'),
        ('completed', 'Завершён'),
        ('failed', 'Ошибка'),
    )

    profile = models.ForeignKey(
        ImportProfile,
        on_delete=models.PROTECT,
        related_name='jobs',
        verbose_name="Профиль импорта"
    )
    file = models.FileField("Excel-файл", upload_to='imports/%Y/%m/')
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    log = models.TextField("Лог выполнения", blank=True, default='')
    total_rows = models.PositiveIntegerField("Всего строк", default=0)
    success_count = models.PositiveIntegerField("Успешно", default=0)
    error_count = models.PositiveIntegerField("С ошибками", default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Кто запустил"
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    completed_at = models.DateTimeField("Завершён", null=True, blank=True)

    class Meta:
        verbose_name = "Задача импорта"
        verbose_name_plural = "Задачи импорта"
        ordering = ['-created_at']

    def __str__(self):
        return f"Импорт #{self.pk} ({self.profile.name})"

    def append_log(self, message: str):
        """Добавляет строку в лог с временной меткой"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log += f"[{timestamp}] {message}\n"
        self.save(update_fields=['log'])