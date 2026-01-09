from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from store.models import Product
from django.http import JsonResponse, response
from django.contrib import messages


def cart_summary(request):
    # Get the cart
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    totals = cart.cart_total()
    return render(request, 'cart_summary.html', {'cart_products': cart_products, 'quantities': quantities, 'totals': totals})



def cart_add(request):
    # Get the Cart
    cart = Cart(request)
    # test for product
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
                
        # lookup the product in DB
        product = get_object_or_404(Product, id=product_id)
        
        # Save to session
        cart.add(product=product, quantity=product_qty)
        
        # Get cart quantity
        cart_quantity = cart.__len__()
        
        # Return Response
        # response = JsonResponse({'Product Name': product.name})
        
        # Get cart quantity
        cart_quantity = cart.__len__()
        response = JsonResponse({'qty': cart_quantity})
        messages.success(request, "Product Added To Cart.")

        return response


def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        
        cart.update(product_id=product_id, quantity=product_qty)
        
        response = JsonResponse({'qty': product_qty})
        messages.success(request, "Your Cart has been Updated Successfully.")
        return response
    
    return redirect('cart_summary')


def cart_remove(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        # Get stuff
        product_id = int(request.POST.get('product_id'))
        # Call delete method
        cart.delete(product=product_id)

        response = JsonResponse({'product': product_id})
        messages.warning(request, "Your cart has been Removed Successfully.")
        return response