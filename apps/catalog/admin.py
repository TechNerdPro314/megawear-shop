from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, ProductImage, Attribute, ProductAttributeValue,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_filterable")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id", "preview", "name", "sku", "supplier_sku", "price", "stock",
        "category", "brand", "is_active", "is_featured",
    )
    list_filter = ("is_active", "is_featured", "category", "brand")
    search_fields = ("name", "sku", "supplier_sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductAttributeInline]

    def get_queryset(self, request):
        """
        Оптимизация: подгружаем связанные объекты и prefetch изображений/атрибутов
        """
        qs = super().get_queryset(request)
        qs = qs.select_related('category', 'brand') \
               .prefetch_related('images', 'attribute_values__attribute')
        return qs

    def preview(self, obj):
        # Все изображения уже загружены через prefetch_related
        images = list(obj.images.all())   # запроса к БД не будет
        main_img = None
        # Ищем главное изображение
        for img in images:
            if img.is_main:
                main_img = img
                break
        if not main_img and images:
            main_img = images[0]
        if main_img:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover;" />',
                main_img.image.url
            )
        return "-"
    preview.short_description = "Фото"

    # Отключаем полный подсчёт количества записей (ускоряет пагинацию)
    show_full_result_count = False