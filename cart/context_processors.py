from .cart import Cart

def cart_context_processor(request):
    """
    A context processor to make the cart available in all templates.
    """
    cart = Cart(request)
    return {'cart': cart}