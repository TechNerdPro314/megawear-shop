from .services import CartService

def cart_context(request):
    return {"global_cart": CartService(request)}