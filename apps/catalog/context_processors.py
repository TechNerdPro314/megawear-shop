# apps/catalog/context_processors.py
from .models import Category

def footer_categories(request):
    categories = Category.objects.filter(is_active=True).exclude(slug='')[:10]
    return {'footer_categories': categories}

def recently_viewed(request):
    viewed = request.session.get('recently_viewed', [])
    # убираем дубликаты, ограничиваем 8 последними
    from .models import Product
    products = Product.objects.filter(id__in=viewed, is_active=True)[:8]
    return {'recently_viewed_products': products}