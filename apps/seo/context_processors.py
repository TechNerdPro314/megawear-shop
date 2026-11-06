from .services import SEOContextProcessor


def seo_tags(request):
    """
    Контекстный процессор для SEO тегов
    
    Добавляет в каждый шаблон:
    - seo_meta: мета-теги (title, description, keywords)
    - seo_og: Open Graph теги для соцсетей
    - seo_twitter: Twitter Card теги
    - seo_canonical: canonical URL
    - seo_jsonld: JSON-LD структурированные данные
    - seo_breadcrumbs: хлебные крошки
    """
    return {
        'seo_processor': SEOContextProcessor,
        'seo_meta': None,
        'request': request,
    }
