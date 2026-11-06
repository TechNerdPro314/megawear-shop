import io
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import Category, Brand, Product, Attribute, ProductAttributeValue, ProductImage

def generate_placeholder_image(title: str) -> ContentFile:
    """Генерирует темную картинку с лаймовым текстом в стиле бренда."""
    width, height = 800, 800
    # Темный фон
    img = Image.new('RGB', (width, height), color='#111212')
    draw = ImageDraw.Draw(img)
    
    # Рисуем лаймовую рамку
    draw.rectangle([20, 20, width-20, height-20], outline='#d7ff00', width=5)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()

    # Переносим текст, если он длинный
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + word) < 15:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())

    # Центрируем текст
    y_text = height // 2 - (len(lines) * 30)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        draw.text((x, y_text), line, fill='#d7ff00', font=font)
        y_text += 70

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"{slugify(title)}.jpg")


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми товарами для магазина одежды MegaWear"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Начинаем заполнение базы данных..."))

        # 1. Создаем КАТЕГОРИИ
        categories_data = [
            {"name": "Худи и толстовки", "slug": "hudi-i-tolstovki"},
            {"name": "Футболки", "slug": "futbolki"},
            {"name": "Штаны", "slug": "shtany"},
            {"name": "Куртки", "slug": "kurtki"},
        ]
        categories = {}
        for cat in categories_data:
            obj, created = Category.objects.get_or_create(
                slug=cat["slug"],
                defaults={"name": cat["name"], "is_active": True}
            )
            categories[cat["slug"]] = obj
            if created:
                self.stdout.write(f"✓ Создана категория: {obj.name}")

        # 2. Создаем БРЕНДЫ
        brands_data = [
            {"name": "Nike", "slug": "nike"},
            {"name": "Adidas", "slug": "adidas"},
            {"name": "Carhartt", "slug": "carhartt"},
            {"name": "The North Face", "slug": "tnf"},
            {"name": "Stone Island", "slug": "stone-island"},
        ]
        brands = {}
        for b in brands_data:
            obj, created = Brand.objects.get_or_create(
                slug=b["slug"],
                defaults={"name": b["name"], "is_active": True}
            )
            brands[b["slug"]] = obj
            if created:
                self.stdout.write(f"✓ Создан бренд: {obj.name}")

        # 3. Создаем АТРИБУТЫ (Размеры и Цвета)
        size_attr, _ = Attribute.objects.get_or_create(
            slug="razmer", defaults={"name": "Размер", "is_filterable": True}
        )
        color_attr, _ = Attribute.objects.get_or_create(
            slug="cvet", defaults={"name": "Цвет", "is_filterable": True}
        )
        sizes = ["S", "M", "L", "XL"]
        colors = ["Черный", "Белый", "Серый", "Хаки"]

        # 4. Товары
        products_data = [
            {"name": "Худи Oversize Black", "cat": "hudi-i-tolstovki", "brand": "nike", "price": 5990, "stock": 50},
            {"name": "Толстовка Basic Grey", "cat": "hudi-i-tolstovki", "brand": "adidas", "price": 4500, "stock": 30},
            {"name": "Худи Zip Hoodie Green", "cat": "hudi-i-tolstovki", "brand": "carhartt", "price": 7200, "stock": 15},
            {"name": "Футболка Basic White", "cat": "futbolki", "brand": "nike", "price": 2500, "stock": 100},
            {"name": "Футболка Oversize Lime", "cat": "futbolki", "brand": "adidas", "price": 3200, "stock": 45},
            {"name": "Штаны Cargo Khaki", "cat": "shtany", "brand": "carhartt", "price": 6800, "stock": 25},
            {"name": "Спортивные штаны Tech", "cat": "shtany", "brand": "nike", "price": 5400, "stock": 40},
            {"name": "Куртка Windrunner", "cat": "kurtki", "brand": "tnf", "price": 15900, "stock": 10},
            {"name": "Бомбер Street", "cat": "kurtki", "brand": "stone-island", "price": 24500, "stock": 5},
        ]

        for p in products_data:
            product, created = Product.objects.get_or_create(
                sku=f"SKU-{slugify(p['name']).upper()[:10]}",
                defaults={
                    "name": p["name"],
                    "slug": slugify(p["name"]),
                    "category": categories[p["cat"]],
                    "brand": brands[p["brand"]],
                    "price": Decimal(p["price"]),
                    "stock": p["stock"],
                    "is_active": True,
                    "short_description": f"Качественный товар от бренда {brands[p['brand']].name}.",
                    "seo_title": f"{p['name']} — купить в MegaWear",
                }
            )

            if created:
                # Генерируем картинку
                img_content = generate_placeholder_image(p["name"])
                product_img = ProductImage(product=product, is_main=True)
                product_img.image.save(img_content.name, img_content, save=True)

                # Добавляем размеры (в одну запись через запятую)
                random_sizes = random.sample(sizes, k=random.randint(2, 4))
                ProductAttributeValue.objects.update_or_create(
                    product=product,
                    attribute=size_attr,
                    defaults={"value": ", ".join(sorted(random_sizes))}
                )
                
                # Добавляем цвет
                random_color = random.choice(colors)
                ProductAttributeValue.objects.update_or_create(
                    product=product,
                    attribute=color_attr,
                    defaults={"value": random_color}
                )
                
                self.stdout.write(f"✓ Создан товар: {product.name}")

        self.stdout.write(self.style.SUCCESS("\n✅ База данных успешно заполнена!"))