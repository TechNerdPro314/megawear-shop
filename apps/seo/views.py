from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string
from django.utils import timezone
from apps.catalog.models import Product, Category, Brand


@require_GET
def sitemap_view(request):
    """Генерация sitemap.xml"""
    # Получаем все активные сущности
    products = Product.objects.filter(is_active=True).select_related("category", "brand")
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    site_url = request.build_absolute_uri("/").rstrip("/")
    
    context = {
        "products": products,
        "categories": categories,
        "brands": brands,
        "site_url": site_url,
        "lastmod": timezone.now().date(),
    }
    
    xml_content = render_to_string("seo/sitemap.xml", context)
    
    return HttpResponse(xml_content, content_type="application/xml; charset=utf-8")


@require_GET
def robots_view(request):
    """Генерация robots.txt"""
    site_url = request.build_absolute_uri("/").rstrip("/")
    
    content = f"""# MegaMart robots.txt
# Дата генерации: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

User-agent: *
Allow: /

# Sitemap
Sitemap: {site_url}/sitemap.xml

# Запрещенные пути для индексации
Disallow: /admin/
Disallow: /cart/
Disallow: /orders/
Disallow: /users/
Disallow: /payments/
Disallow: /importer/
Disallow: /promotions/
Disallow: /media/
Disallow: /static/
Disallow: /ht/

# Разрешаем доступ к полезным ресурсам
Allow: /media/products/
Allow: /static/
"""
    
    return HttpResponse(content, content_type="text/plain; charset=utf-8")
