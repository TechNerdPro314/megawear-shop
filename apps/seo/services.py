# apps/seo/services.py

import json
from django.urls import reverse


class SEOContextProcessor:
    """
    Сервис для генерации SEO-контекста:
    - JSON-LD Schema.org разметка
    - Хлебные крошки
    - Мета-теги
    """

    @staticmethod
    def get_jsonld_schema(request, product=None, category=None, brand=None):
        """
        Генерация JSON-LD схемы в зависимости от типа страницы
        """
        schemas = []
        
        # Всегда добавляем WebSite и Organization
        schemas.append(SEOContextProcessor.website_schema(request))
        schemas.append(SEOContextProcessor.organization_schema(request))
        
        # BreadcrumbList для всех страниц кроме главной
        if request.path != "/":
            schemas.append(SEOContextProcessor.breadcrumb_schema(request))
        
        # Специфичные схемы
        if product:
            schemas.append(SEOContextProcessor.product_schema(request, product))
        elif category:
            schemas.append(SEOContextProcessor.category_schema(request, category))
        elif brand:
            schemas.append(SEOContextProcessor.brand_schema(request, brand))
        
        return schemas

    @staticmethod
    def website_schema(request):
        """Schema.org WebSite JSON-LD"""
        site_url = request.build_absolute_uri("/").rstrip("/")
        
        schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "MegaMart",
            "url": site_url,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{site_url}/catalog/?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        }
        
        return schema

    @staticmethod
    def organization_schema(request):
        """Schema.org Organization JSON-LD"""
        site_url = request.build_absolute_uri("/").rstrip("/")
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "MegaMart",
            "url": site_url,
            "logo": f"{site_url}/static/images/logo.png",
            "sameAs": [
                # Социальные сети (добавить при необходимости)
            ]
        }
        
        return schema

    @staticmethod
    def breadcrumb_schema(request):
        """Schema.org BreadcrumbList JSON-LD"""
        # Получаем breadcrumbs из контекста (если есть)
        # Или строим из URL
        breadcrumbs = getattr(request, 'breadcrumbs_items', [])
        
        if not breadcrumbs:
            # Базовые breadcrumbs по URL
            path_parts = [p for p in request.path.strip("/").split("/") if p]
            breadcrumbs = [{"name": "Главная", "url": request.build_absolute_uri("/").rstrip("/")}]
            
            current_url = request.build_absolute_uri("/").rstrip("/")
            for part in path_parts:
                current_url += f"/{part}"
                breadcrumbs.append({
                    "name": part.replace("-", " ").title(),
                    "url": current_url
                })
        
        item_list = []
        for i, crumb in enumerate(breadcrumbs, 1):
            item = {
                "@type": "ListItem",
                "position": i,
                "name": crumb.get("name", ""),
            }
            if "url" in crumb:
                item["item"] = crumb["url"]
            item_list.append(item)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list
        }
        
        return schema

    @staticmethod
    def product_schema(request, product):
        """Schema.org Product JSON-LD"""
        site_url = request.build_absolute_uri("/").rstrip("/")
        product_url = request.build_absolute_uri(product.get_absolute_url())
        
        # ← ИСПРАВЛЕНО: получаем URL изображения через main_image (property модели Product)
        image_url = None
        if product.main_image:
            image_url = request.build_absolute_uri(product.main_image.url)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product.name,
            "image": image_url,  # ← ИСПРАВЛЕНО: используем image_url вместо external_image_url
            "description": product.seo_description or product.short_description or "",
            "sku": product.sku,
            "url": product_url,
            "brand": {
                "@type": "Brand",
                "name": product.brand.name if product.brand else "MegaMart"
            },
            "offers": {
                "@type": "Offer",
                "url": product_url,
                "priceCurrency": "RUB",
                "price": str(product.price),
                "availability": "https://schema.org/InStock" if product.stock > 0 else "https://schema.org/OutOfStock",
                "itemCondition": "https://schema.org/NewCondition",
                "priceValidUntil": "",  # Можно добавить дату окончания акции
                "seller": {
                    "@type": "Organization",
                    "name": "MegaMart",
                    "url": site_url
                }
            }
        }
        
        # Добавляем aggregateRating если есть отзывы
        if hasattr(product, 'reviews'):
            from django.db.models import Avg, Count
            rating_data = product.reviews.filter(status="approved").aggregate(
                avg_rating=Avg("rating"),
                total_reviews=Count("id")
            )
            if rating_data["total_reviews"] and rating_data["total_reviews"] > 0:
                schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": str(round(float(rating_data["avg_rating"] or 0), 1)),
                    "reviewCount": str(rating_data["total_reviews"])
                }
        
        # Добавляем все изображения товара (опционально)
        all_images = []
        for img in product.images.all():
            all_images.append(request.build_absolute_uri(img.image.url))
        
        if len(all_images) > 1:
            schema["image"] = all_images  # Массив всех изображений
        elif image_url:
            schema["image"] = image_url  # Одно изображение
        
        return schema

    @staticmethod
    def category_schema(request, category):
        """Schema.org CollectionPage / ItemList JSON-LD для категории"""
        site_url = request.build_absolute_uri("/").rstrip("/")
        category_url = request.build_absolute_uri(category.get_absolute_url())
        
        # ← ИСПРАВЛЕНО: получаем URL изображения категории
        image_url = None
        if hasattr(category, 'image') and category.image:
            image_url = request.build_absolute_uri(category.image.url)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": category.name,
            "description": category.get_seo_description() or category.description or "",
            "url": category_url,
            "image": image_url,  # ← ИСПРАВЛЕНО
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": []
            }
        }
        
        # Добавляем товары категории (первые 10)
        products = category.products.filter(is_active=True)[:10]
        for i, product in enumerate(products, 1):
            product_image = None
            if product.main_image:
                product_image = request.build_absolute_uri(product.main_image.url)
            
            schema["mainEntity"]["itemListElement"].append({
                "@type": "ListItem",
                "position": i,
                "url": request.build_absolute_uri(product.get_absolute_url()),
                "name": product.name,
                "image": product_image,  # ← ИСПРАВЛЕНО
                "offers": {
                    "@type": "Offer",
                    "price": str(product.price),
                    "priceCurrency": "RUB"
                }
            })
        
        return schema

    @staticmethod
    def brand_schema(request, brand):
        """Schema.org Brand / Organization JSON-LD"""
        site_url = request.build_absolute_uri("/").rstrip("/")
        brand_url = request.build_absolute_uri(brand.get_absolute_url())
        
        # ← ИСПРАВЛЕНО: получаем URL логотипа бренда
        logo_url = None
        if hasattr(brand, 'logo') and brand.logo:
            logo_url = request.build_absolute_uri(brand.logo.url)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Brand",
            "name": brand.name,
            "description": brand.get_seo_description() or brand.description or "",
            "url": brand_url,
            "logo": logo_url,  # ← ИСПРАВЛЕНО: logo вместо external_image_url
            "image": logo_url,  # ← ИСПРАВЛЕНО
        }
        
        return schema

    @staticmethod
    def get_meta_tags(request, product=None, category=None, brand=None):
        """
        Генерация meta-тегов для страницы
        """
        meta = {
            "title": "MegaMart - Интернет-магазин сантехники",
            "description": "Большой выбор сантехники по выгодным ценам. Доставка по России.",
            "keywords": "сантехника, купить, магазин, цены",
            "robots": "index, follow",
            "canonical": request.build_absolute_uri(request.path),
        }
        
        if product:
            meta.update({
                "title": product.seo_title or f"Купить {product.name} - MegaMart",
                "description": product.seo_description or product.short_description or f"Товар {product.name} в MegaMart",
                "keywords": product.seo_keywords or f"{product.name}, {product.brand.name if product.brand else ''}, купить",
                "og:type": "product",
                "og:title": product.name,
                "og:description": product.short_description or "",
                "og:image": request.build_absolute_uri(product.main_image.url) if product.main_image else "",
                "og:url": request.build_absolute_uri(product.get_absolute_url()),
                "product:price:amount": str(product.price),
                "product:price:currency": "RUB",
            })
        elif category:
            meta.update({
                "title": category.get_seo_title(),
                "description": category.get_seo_description(),
                "keywords": category.seo_keywords or f"{category.name}, сантехника",
                "og:type": "website",
                "og:title": category.name,
                "og:description": category.get_seo_description() or "",
                "og:image": request.build_absolute_uri(category.image.url) if (hasattr(category, 'image') and category.image) else "",
                "og:url": request.build_absolute_uri(category.get_absolute_url()),
            })
        elif brand:
            meta.update({
                "title": brand.get_seo_title(),
                "description": brand.get_seo_description(),
                "keywords": brand.seo_keywords or f"{brand.name}, сантехника",
                "og:type": "website",
                "og:title": brand.name,
                "og:description": brand.get_seo_description() or "",
                "og:image": request.build_absolute_uri(brand.logo.url) if (hasattr(brand, 'logo') and brand.logo) else "",
                "og:url": request.build_absolute_uri(brand.get_absolute_url()),
            })
        
        return meta

    @staticmethod
    def get_breadcrumbs(request, product=None, category=None, brand=None):
        """
        Генерация хлебных крошек
        """
        site_url = request.build_absolute_uri("/").rstrip("/")
        
        breadcrumbs = [
            {"name": "Главная", "url": site_url}
        ]
        
        if category:
            breadcrumbs.append({
                "name": "Каталог",
                "url": f"{site_url}/catalog/"
            })
            breadcrumbs.append({
                "name": category.name,
                "url": f"{site_url}{category.get_absolute_url()}"
            })
        elif brand:
            breadcrumbs.append({
                "name": "Каталог",
                "url": f"{site_url}/catalog/"
            })
            breadcrumbs.append({
                "name": brand.name,
                "url": f"{site_url}{brand.get_absolute_url()}"
            })
        elif product:
            breadcrumbs.append({
                "name": "Каталог",
                "url": f"{site_url}/catalog/"
            })
            if product.category:
                breadcrumbs.append({
                    "name": product.category.name,
                    "url": f"{site_url}{product.category.get_absolute_url()}"
                })
            if product.brand:
                breadcrumbs.append({
                    "name": product.brand.name,
                    "url": f"{site_url}/catalog/brand/{product.brand.slug}/"
                })
            breadcrumbs.append({
                "name": product.name,
                "url": f"{site_url}{product.get_absolute_url()}"
            })
        
        return breadcrumbs