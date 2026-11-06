from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from .models import Product, Category, Brand, Attribute, ProductAttributeValue
from apps.seo.services import SEOContextProcessor
from apps.reviews.forms import ReviewForm
from .models import Product


class HomePageView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_products"] = Product.objects.filter(is_active=True).select_related("category", "brand")[:8]
        # Исключаем категории и бренды с пустым slug
        context["categories"] = Category.objects.filter(is_active=True).exclude(slug='')[:8]
        context["brands"] = Brand.objects.filter(is_active=True).exclude(slug='')[:10]

        site_url = self.request.build_absolute_uri("/")
        context["seo_meta"] = {
            "title": "MegaMart - Интернет-магазин сантехники",
            "description": "Большой выбор сантехники по выгодным ценам. Доставка по России.",
            "keywords": "сантехника, купить, магазин, цены",
        }
        context["page_title"] = "MegaMart - Интернет-магазин сантехники"
        context["breadcrumbs_items"] = [
            {"name": "Главная", "url": site_url.rstrip("/")}
        ]
        context["seo_jsonld_schemas"] = SEOContextProcessor.get_jsonld_schema(self.request)
        return context


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 24

    SORT_OPTIONS = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'popular': '-is_featured',
    }

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related("brand", "category")

        # 1. Категории
        selected_categories = [c.strip() for c in self.request.GET.getlist('category') if c.strip()]
        if selected_categories:
            qs = qs.filter(category__slug__in=selected_categories)

        # 2. Бренды
        selected_brands = [b.strip() for b in self.request.GET.getlist('brand') if b.strip()]
        if selected_brands:
            qs = qs.filter(brand__slug__in=selected_brands)

        # 3. Поиск (название, артикул, артикул поставщика, бренд, категория)
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(supplier_sku__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(category__name__icontains=search)
            )

        # 4. Цена
        price_min = self.request.GET.get('price_min', '').strip()
        price_max = self.request.GET.get('price_max', '').strip()
        if price_min:
            qs = qs.filter(price__gte=price_min)
        if price_max:
            qs = qs.filter(price__lte=price_max)

        # 5. Атрибуты (характеристики)
        for key in self.request.GET:
            if key.startswith('attr_'):
                attr_slug = key[5:]
                values = [v.strip() for v in self.request.GET.getlist(key) if v.strip()]
                if values:
                    qs = qs.filter(
                        attribute_values__attribute__slug=attr_slug,
                        attribute_values__value__in=values
                    )

        # Сохраняем базовый queryset для построения доступных фильтров атрибутов
        self.base_queryset = qs

        # Сортировка
        sort_param = self.request.GET.get('sort', 'newest')
        if sort_param == 'popular':
            qs = qs.order_by('-is_featured', '-created_at')
        else:
            order_field = self.SORT_OPTIONS.get(sort_param, '-created_at')
            qs = qs.order_by(order_field)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True).exclude(slug='')
        context["brands"] = Brand.objects.filter(is_active=True).exclude(slug='')

        selected_categories = [c.strip() for c in self.request.GET.getlist('category') if c.strip()]
        selected_brands = [b.strip() for b in self.request.GET.getlist('brand') if b.strip()]

        context["selected_categories"] = selected_categories
        context["selected_brands"] = selected_brands
        context["current_sort"] = self.request.GET.get('sort', 'newest')

        # Выбранные атрибуты
        selected_attrs = {}
        for key in self.request.GET:
            if key.startswith('attr_'):
                values = [v.strip() for v in self.request.GET.getlist(key) if v.strip()]
                if values:
                    selected_attrs[key] = values
        context['selected_attrs'] = selected_attrs

        # Доступные атрибуты (на основе текущего фильтра, кроме атрибутов)
        if hasattr(self, 'base_queryset'):
            attribute_qs = Attribute.objects.filter(
                productattributevalue__product__in=self.base_queryset
            ).distinct()
            filter_attributes = []
            for attr in attribute_qs:
                values = ProductAttributeValue.objects.filter(
                    attribute=attr,
                    product__in=self.base_queryset
                ).values_list('value', flat=True).distinct().order_by('value')
                if values:
                    filter_attributes.append({
                        'attribute': attr,
                        'values': list(values),
                    })
            context['filter_attributes'] = filter_attributes
        else:
            context['filter_attributes'] = []

        # Параметры для пагинации и сортировки (без page и sort)
        params = self.request.GET.copy()
        params.pop('page', None)
        params.pop('sort', None)
        context['filter_params'] = params.urlencode()

        # SEO и хлебные крошки
        site_url = self.request.build_absolute_uri("/")

        if len(selected_categories) == 1:
            category_slug = selected_categories[0]
            category = Category.objects.filter(slug=category_slug, is_active=True).first()
            if category:
                context["current_category"] = category
                context["page_title"] = category.get_seo_title()
                context["seo_meta"] = {
                    "title": category.get_seo_title(),
                    "description": category.get_seo_description(),
                    "keywords": category.seo_keywords or f"{category.name}, сантехника",
                }
                context["breadcrumbs_items"] = [
                    {"name": "Главная", "url": site_url.rstrip("/")},
                    {"name": "Каталог", "url": f"{site_url}catalog/"},
                    {"name": category.name, "url": f"{site_url}{category.get_absolute_url()}"},
                ]
                context["seo_jsonld_schemas"] = SEOContextProcessor.get_jsonld_schema(
                    self.request, category=category
                )
            else:
                self._set_default_seo(context, site_url)
        elif len(selected_brands) == 1:
            brand_slug = selected_brands[0]
            brand = Brand.objects.filter(slug=brand_slug, is_active=True).first()
            if brand:
                context["current_brand"] = brand
                context["page_title"] = brand.get_seo_title()
                context["seo_meta"] = {
                    "title": brand.get_seo_title(),
                    "description": brand.get_seo_description(),
                    "keywords": brand.seo_keywords or f"{brand.name}, сантехника",
                }
                context["breadcrumbs_items"] = [
                    {"name": "Главная", "url": site_url.rstrip("/")},
                    {"name": "Каталог", "url": f"{site_url}catalog/"},
                    {"name": brand.name, "url": f"{site_url}{brand.get_absolute_url()}"},
                ]
                context["seo_jsonld_schemas"] = SEOContextProcessor.get_jsonld_schema(
                    self.request, brand=brand
                )
            else:
                self._set_default_seo(context, site_url)
        else:
            self._set_default_seo(context, site_url)

        return context

    def _set_default_seo(self, context, site_url):
        context["page_title"] = "Каталог товаров - MegaMart"
        context["seo_meta"] = {
            "title": "Каталог товаров - Купить сантехнику в MegaMart",
            "description": "Полный каталог сантехники. Большой выбор товаров, низкие цены, доставка.",
            "keywords": "каталог, сантехника, товары, цены",
        }
        context["breadcrumbs_items"] = [
            {"name": "Главная", "url": site_url.rstrip("/")},
            {"name": "Каталог"},
        ]
        context["seo_jsonld_schemas"] = SEOContextProcessor.get_jsonld_schema(self.request)


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_products"] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).select_related("brand").exclude(id=self.object.id)[:4]

        # Статистика по отзывам
        rating_data = self.object.reviews.filter(status="approved").aggregate(
            avg_rating=Avg("rating"),
            total_reviews=Count("id")
        )
        context["avg_rating"] = rating_data["avg_rating"] or 0
        context["total_reviews"] = rating_data["total_reviews"] or 0

        # Сами отзывы (одобренные)
        context["reviews"] = self.object.reviews.filter(
            status="approved"
        ).select_related("user").order_by("-created_at")

        product_ids = self.request.session.get('recently_viewed', [])
        if self.object.id not in product_ids:
            product_ids.insert(0, self.object.id)
            self.request.session['recently_viewed'] = product_ids[:20]

        context['recently_viewed_products'] = Product.objects.filter(
            id__in=product_ids, is_active=True
        ).exclude(id=self.object.id)[:8]
        
        # Форма добавления отзыва
        context["review_form"] = ReviewForm()

        site_url = self.request.build_absolute_uri("/")
        context["page_title"] = self.object.seo_title or f"Купить {self.object.name} - MegaMart"
        context["seo_meta"] = {
            "title": self.object.seo_title or f"Купить {self.object.name} - MegaMart",
            "description": self.object.seo_description or self.object.short_description or f"Товар {self.object.name} в MegaMart",
            "keywords": self.object.seo_keywords or f"{self.object.name}, {self.object.brand.name if self.object.brand else ''}, купить",
        }

        breadcrumbs = [
            {"name": "Главная", "url": site_url.rstrip("/")},
            {"name": "Каталог", "url": f"{site_url}catalog/"},
        ]
        if self.object.category:
            breadcrumbs.append({
                "name": self.object.category.name,
                "url": f"{site_url}{self.object.category.get_absolute_url()}"
            })
        if self.object.brand:
            breadcrumbs.append({
                "name": self.object.brand.name,
                "url": f"{site_url}/catalog/brand/{self.object.brand.slug}/"
            })
        breadcrumbs.append({"name": self.object.name, "url": f"{site_url}{self.object.get_absolute_url()}"})
        context["breadcrumbs_items"] = breadcrumbs
        context["seo_jsonld_schemas"] = SEOContextProcessor.get_jsonld_schema(
            self.request, product=self.object
        )
        return context