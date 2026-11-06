from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .services import CouponService


def coupon_list_view(request):
    """
    Список доступных купонов (для администраторов)
    
    Возвращает JSON со списком активных купонов
    """
    subtotal = float(request.GET.get('subtotal', 0))
    user = request.user if request.user.is_authenticated else None
    
    coupons = CouponService.get_available_coupons(
        subtotal=subtotal if subtotal > 0 else None,
        user=user
    )
    
    data = [
        {
            'code': c.code,
            'name': c.name,
            'discount_type': c.discount_type,
            'discount_value': str(c.discount_value),
            'min_order_amount': str(c.min_order_amount),
            'usage_limit': c.usage_limit,
            'usage_count': c.usage_count,
            'valid_from': c.valid_from.isoformat(),
            'valid_to': c.valid_to.isoformat(),
        }
        for c in coupons
    ]
    
    return JsonResponse({'coupons': data})


@require_http_methods(["POST"])
def coupon_check_view(request):
    """
    Проверка купона
    
    POST data:
        code: str - код купона
        subtotal: decimal - сумма заказа
    
    Returns:
        JSON: {
            'valid': bool,
            'code': str,
            'discount': decimal,
            'error': str or None
        }
    """
    try:
        data = json.loads(request.body) if request.body else request.POST
        code = data.get('code', '').strip().upper()
        subtotal = float(data.get('subtotal', 0))
        user = request.user if request.user.is_authenticated else None
        
        if not code:
            return JsonResponse({'valid': False, 'error': 'Введите код купона'})
        
        coupon = CouponService.get_by_code(code)
        
        if not coupon:
            return JsonResponse({'valid': False, 'error': 'Купон не найден'})
        
        validation = CouponService.validate_coupon(coupon, subtotal, user)
        
        response = {
            'valid': validation['valid'],
            'code': coupon.code,
            'discount': str(validation['discount']),
            'error': validation['error'],
        }
        
        if validation['valid']:
            response.update({
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
            })
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({'valid': False, 'error': f'Ошибка: {str(e)}'})
