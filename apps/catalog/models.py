from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField


class Category(models.Model):
    """Категория товаров"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    
    # SEO поля
    seo_title = models.CharField("SEO заголовок", max_length=255, blank=True, null=True, help_text="Если пусто, используется название")
    seo_description = models.TextField("SEO описание", blank=True, null=True, help_text="Если пусто, используется краткое описание")
    seo_keywords = models.CharField("SEO ключевые слова", max_length=500, blank=True, null=True)
    
    # Контент
    description = RichTextField("Описание категории", blank=True, null=True)
    image = models.ImageField("Изображение", upload_to="categories/", blank=True, null=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("catalog:product_list_by_category", kwargs={"category": self.slug})
    
    def get_seo_title(self):
        return self.seo_title or f"{self.name} - Купить в MegaMart"
    
    def get_seo_description(self):
        return self.seo_description or f"Каталог {self.name} в интернет-магазине MegaMart. Большой выбор, выгодные цены, доставка."

    def clean(self):
        """Проверка обязательности slug"""
        if not self.slug:
            raise ValidationError({'slug': 'Slug не может быть пустым'})


class Brand(models.Model):
    """Бренд (Производитель)"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    
    # SEO поля
    seo_title = models.CharField("SEO заголовок", max_length=255, blank=True, null=True)
    seo_description = models.TextField("SEO описание", blank=True, null=True)
    seo_keywords = models.CharField("SEO ключевые слова", max_length=500, blank=True, null=True)
    
    # Контент
    description = RichTextField("Описание бренда", blank=True, null=True)
    logo = models.ImageField("Логотип", upload_to="brands/", blank=True, null=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("catalog:product_list_by_brand", kwargs={"brand": self.slug})
    
    def get_seo_title(self):
        return self.seo_title or f"Товары бренда {self.name} - MegaMart"
    
    def get_seo_description(self):
        return self.seo_description or f"Оригинальные товары бренда {self.name} в MegaMart. Гарантия качества, низкие цены."

    def clean(self):
        if not self.slug:
            raise ValidationError({'slug': 'Slug не может быть пустым'})


class Attribute(models.Model):
    """Глобальный справочник характеристик"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_filterable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар (Полная enterprise-модель)"""
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name="Категория")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products', verbose_name="Бренд", blank=True, null=True)
    
    name = models.CharField("Название товара", max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    sku = models.CharField("Артикул MegaMart", max_length=64, unique=True)
    supplier_sku = models.CharField("Артикул поставщика", max_length=64, blank=True, null=True)
    
    # Исправлено: убран лишний max_length, оставлены только max_digits и decimal_places
    price = models.DecimalField("Цена (руб.)", max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField("Остаток на складе", default=0)
    
    short_description = models.TextField("Краткое описание", blank=True, null=True)
    description = RichTextField("Полное описание (HTML)", blank=True, null=True)
    
    is_active = models.BooleanField("Активен", default=True)
    is_featured = models.BooleanField("Популярный товар", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO поля
    seo_title = models.CharField("SEO заголовок", max_length=255, blank=True, null=True)
    seo_description = models.TextField("SEO описание", blank=True, null=True)
    seo_keywords = models.CharField("SEO ключевые слова", max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
        # Добавлены индексы для часто фильтруемых полей
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['price']),
            models.Index(fields=['is_active', 'category']),
        ]

    def __str__(self):
        return f"[{self.sku}] {self.name}"

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def main_image(self):
        """Возвращает изображение, отмеченное как главное, либо самое первое из галереи"""
        main_img = self.images.filter(is_main=True).first()
        if not main_img:
            main_img = self.images.first()
        return main_img.image if main_img else None


class ProductImage(models.Model):
    """Галерея изображений товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField("Файл изображения", upload_to="products/")
    is_main = models.BooleanField("Главное фото", default=False)
    alt_text = models.CharField("Альтернативный текст", max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['-is_main', 'id']


class ProductAttributeValue(models.Model):
    """Значения атрибутов для конкретных товаров"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_values', verbose_name="Товар")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name="Характеристика")
    value = models.CharField("Значение", max_length=255)

    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товаров"
        unique_together = ['product', 'attribute']
        # Добавлен индекс для фильтрации по атрибуту и значению (EAV-запросы)
        indexes = [
            models.Index(fields=['attribute', 'value']),
        ]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"