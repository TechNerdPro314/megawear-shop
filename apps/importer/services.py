import uuid
import requests
import openpyxl
from decimal import Decimal, InvalidOperation
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from apps.catalog.models import Product, Category, Brand, Attribute, ProductAttributeValue, ProductImage


class ExcelImporter:
    CHUNK_SIZE = 200

    def __init__(self, job):
        self.job = job
        self.profile = job.profile
        self.field_mapping = self.profile.field_mapping or {}
        self.default_values = self.profile.default_values or {}
        self.stats = {'total': 0, 'success': 0, 'error': 0}
        self.errors = []
        self._header = None
        self._categories_cache = {}
        self._brands_cache = {}
        self._attributes_cache = {}

    def run(self):
        self.job.status = 'processing'
        self.job.save(update_fields=['status'])
        try:
            wb = openpyxl.load_workbook(self.job.file.path, data_only=True)
            ws = wb[self.profile.sheet_name] if self.profile.sheet_name else wb.active
            rows = list(ws.iter_rows(values_only=True))
            start_row = 0
            if self.profile.skip_header and rows:
                self._header = rows[0]
                start_row = 1
            total = max(0, len(rows) - start_row)
            self.job.total_rows = total
            self.job.save(update_fields=['total_rows'])

            # предзагрузка категорий и брендов
            self._categories_cache = {c.name.lower(): c for c in Category.objects.filter(is_active=True)}
            self._brands_cache = {b.name.lower(): b for b in Brand.objects.filter(is_active=True)}

            products_to_create = []
            products_to_update = []
            row_errors = []

            for row_idx, row in enumerate(rows[start_row:], start=start_row + 1):
                try:
                    product_obj, created = self._process_row_to_object(row, row_idx)
                    if created:
                        products_to_create.append(product_obj)
                    else:
                        products_to_update.append(product_obj)
                    self.stats['success'] += 1
                except Exception as e:
                    error_msg = f"Строка {row_idx}: {e}"
                    row_errors.append(error_msg)
                    self.stats['error'] += 1

                if len(products_to_create) >= self.CHUNK_SIZE:
                    self._bulk_save(products_to_create, products_to_update)
                    products_to_create.clear()
                    products_to_update.clear()

            if products_to_create or products_to_update:
                self._bulk_save(products_to_create, products_to_update)

            self.job.success_count = self.stats['success']
            self.job.error_count = self.stats['error']
            log_text = '\n'.join(row_errors) if row_errors else 'Импорт завершён без ошибок.'
            self.job.append_log(log_text)
            self.job.status = 'completed'
        except Exception as e:
            self.job.append_log(f"Критическая ошибка: {e}")
            self.job.status = 'failed'
        finally:
            self.job.completed_at = timezone.now()
            self.job.save(update_fields=['status', 'success_count', 'error_count', 'log', 'completed_at'])

    def _process_row_to_object(self, row, row_number):
        data = {}
        for field_name, column_name in self.field_mapping.items():
            col_idx = self._find_column_index(column_name)
            value = row[col_idx] if col_idx is not None and col_idx < len(row) else None
            if (value is None or str(value).strip() == '') and field_name in self.default_values:
                value = self.default_values[field_name]
            data[field_name] = value

        name = str(data.get('name', '')).strip()
        if not name:
            raise ValueError("Не указано название товара")

        sku = str(data.get('sku', '')).strip()
        if not sku:
            base_sku = slugify(name)[:16].upper()
            random_suffix = uuid.uuid4().hex[:6].upper()
            sku = f"{base_sku}-{random_suffix}"

        price = self._parse_decimal(data.get('price'))
        stock = self._parse_int(data.get('stock', 0))
        category = self._resolve_category(data.get('category__name'))
        brand = self._resolve_brand(data.get('brand__name'))

        existing = Product.objects.filter(sku=sku).first()
        if existing and not self.profile.update_existing:
            raise ValueError(f"SKU {sku} уже существует (обновление отключено)")

        defaults = {
            'name': name,
            'slug': self._generate_slug(name, existing),
            'price': price if price is not None else Decimal('0'),
            'stock': stock,
            'short_description': str(data.get('short_description', '')) or None,
            'description': str(data.get('description', '')) or None,
            'is_active': self._parse_bool(data.get('is_active', True)),
            'category': category or self.profile.default_category,
            'brand': brand or self.profile.default_brand,
            'seo_title': str(data.get('seo_title', '')) or None,
            'seo_description': str(data.get('seo_description', '')) or None,
            'seo_keywords': str(data.get('seo_keywords', '')) or None,
        }

        if existing:
            for key, val in defaults.items():
                setattr(existing, key, val)
            product_obj = existing
            created = False
        else:
            product_obj = Product(**defaults)
            created = True

        attr_data = {}
        for field_name, value in data.items():
            if field_name.startswith('attribute__'):
                attr_name = field_name.split('__')[1]
                if value and str(value).strip():
                    attr_data[attr_name] = str(value).strip()

        image_url = str(data.get('image_url', '')).strip()
        product_obj._import_attributes = attr_data
        product_obj._import_image_url = image_url
        return product_obj, created

    def _bulk_save(self, create_list, update_list):
        with transaction.atomic():
            if create_list:
                Product.objects.bulk_create(create_list, batch_size=self.CHUNK_SIZE)
                for p in create_list:
                    self._save_attributes(p)
                    self._save_image(p)
            if update_list:
                for p in update_list:
                    p.save()
                    self._save_attributes(p)
                    self._save_image(p)

    def _save_attributes(self, product):
        attrs = getattr(product, '_import_attributes', {})
        for attr_name, value in attrs.items():
            attr, _ = Attribute.objects.get_or_create(name__iexact=attr_name, defaults={'name': attr_name})
            ProductAttributeValue.objects.update_or_create(
                product=product, attribute=attr, defaults={'value': value}
            )

    def _save_image(self, product):
        url = getattr(product, '_import_image_url', None)
        if not url:
            return
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                img_name = url.split('/')[-1].split('?')[0] or f"{product.sku}.jpg"
                img_content = ContentFile(resp.content, name=img_name)
                ProductImage.objects.create(product=product, image=img_content, is_main=True, alt_text=product.name)
        except Exception:
            pass

    def _resolve_category(self, name):
        if not name:
            return None
        name = str(name).strip().lower()
        return self._categories_cache.get(name)

    def _resolve_brand(self, name):
        if not name:
            return None
        name = str(name).strip().lower()
        return self._brands_cache.get(name)

    def _find_column_index(self, column_name):
        if self._header is None:
            return None
        try:
            return self._header.index(column_name)
        except ValueError:
            return None

    def _parse_decimal(self, value):
        if value is None or str(value).strip() == '':
            return None
        try:
            return Decimal(str(value).replace(',', '.'))
        except InvalidOperation:
            raise ValueError(f"Некорректная цена: {value}")

    def _parse_int(self, value):
        try:
            return int(value) if value is not None else 0
        except (ValueError, TypeError):
            return 0

    def _parse_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'да')
        return bool(value)

    def _generate_slug(self, name, existing=None):
        slug = slugify(name)
        if existing and existing.slug and existing.name == name:
            return existing.slug
        if Product.objects.filter(slug=slug).exclude(pk=existing.pk if existing else None).exists():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        return slug