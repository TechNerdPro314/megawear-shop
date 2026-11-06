from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .services import ComparisonService
from apps.catalog.models import Product

def comparison_view(request):
    service = ComparisonService(request)
    products = service.get_products()

    products_data = []
    attr_names_set = set()
    if products:
        for product in products:
            attrs = {}
            for attr_val in product.attribute_values.select_related('attribute'):
                name = attr_val.attribute.name
                attrs[name] = attr_val.value
                attr_names_set.add(name)
            products_data.append({
                'product': product,
                'attrs': attrs,
            })
        attr_names = sorted(attr_names_set)
    else:
        attr_names = []

    comparison_rows = []
    for attr_name in attr_names:
        row = {
            'name': attr_name,
            'values': [item['attrs'].get(attr_name, '—') for item in products_data],
        }
        comparison_rows.append(row)

    price_values = [f"{item['product'].price:,.0f} ₽" for item in products_data]
    stock_values = [
        f"{item['product'].stock} шт." if item['product'].stock > 0 else "Нет"
        for item in products_data
    ]
    comparison_rows.append({'name': 'Цена', 'values': price_values})
    comparison_rows.append({'name': 'Наличие', 'values': stock_values})

    breadcrumbs = [
        {'name': 'Главная', 'url': '/'},
        {'name': 'Сравнение товаров'},
    ]
    return render(request, 'comparison/compare.html', {
        'products_data': products_data,
        'comparison_rows': comparison_rows,
        'breadcrumbs_items': breadcrumbs,
        'page_title': 'Сравнение товаров',
    })

@require_POST
def add_to_comparison(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    service = ComparisonService(request)
    if service.add(product.id):
        messages.success(request, f'{product.name} добавлен к сравнению')
    else:
        messages.info(request, f'{product.name} уже в сравнении')
    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def remove_from_comparison(request, product_id):
    service = ComparisonService(request)
    if service.remove(product_id):
        messages.success(request, 'Товар удалён из сравнения')
    return redirect('comparison:compare')

@require_POST
def remove_all_comparison(request):
    service = ComparisonService(request)
    service.clear()
    messages.info(request, 'Сравнение очищено')
    return redirect('comparison:compare')