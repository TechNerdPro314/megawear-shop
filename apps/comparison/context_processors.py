from .services import ComparisonService

def comparison_count(request):
    count = len(ComparisonService(request).list)
    return {'comparison_count': count}