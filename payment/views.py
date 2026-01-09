from django.shortcuts import render, redirect
from cart.cart import Cart
from django.contrib import messages
from payment.forms import ShippingForm, PaymentForm
from .models import ShippingAddress, Order, OrderItems
from django.contrib.auth.models import User
from store.models import Product, Profile
import datetime

def payment_success(request):
    return render(request, 'payment/payment_success.html', {})


def checkout(request):
    # Get the cart
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    totals = cart.cart_total()
    
    if request.user.is_authenticated:
        # shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        shipping_user = ShippingAddress.objects.filter(user__id=request.user.id).first()
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        return render(request, 'payment/checkout.html', {'cart_products': cart_products, 'quantities': quantities, 'totals': totals, 'shipping_form': shipping_form})
    else:
        # Checkout as guest
        shipping_form = ShippingForm(request.POST or None)
        return render(request, 'payment/checkout.html', {'cart_products': cart_products, 'quantities': quantities, 'totals': totals, 'shipping_form': shipping_form})



def billing_info(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_products()
        quantities = cart.get_quantities()
        totals = cart.cart_total()

        # Create a session with Shipping Info
        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping
        
        # Check to see if user is logged in 
        if request.user.is_authenticated:
            billing_form = PaymentForm()
            return render(request, 'payment/billing_info.html', {
                'cart_products': cart_products, 
                'quantities': quantities, 
                'totals': totals, 
                'billing_form': billing_form,
                'shipping_info': request.POST
            })
        else:
            billing_form = PaymentForm()
            return render(request, 'payment/billing_info.html', {
                'cart_products': cart_products, 
                'quantities': quantities, 
                'totals': totals, 
                'billing_form': billing_form,
                'shipping_info': request.POST
            })
        # shipping_form = request.POST
        # return render(request, 'payment/billing_info.html', {'cart_products': cart_products, 'quantities': quantities, 'totals': totals, 'shipping_form': shipping_form})
    
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')
    
    
def process_order(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_products()
        quantities = cart.get_quantities()
        totals = cart.cart_total()
        # Get billing info from last page
        payment_form = PaymentForm(request.POST or None)
        # Get shipping Session Data
        my_shipping = request.session.get('my_shipping')
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        
        
        # Create Shipping Address from session info
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals

        # Let's create an Order
        if request.user.is_authenticated:
            # Lets gather user info
            user = request.user
            create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()
            
            # DELETE THE CART FROM THE DATABASE
            # Adjust this to your actual Profile model location
            current_user = Profile.objects.filter(user__id=request.user.id)
            # Clear the old cart data (usually stored as a string or JSON)
            current_user.update(old_cart="")
            # Add order items
            # Get the order ID
            order_id = create_order.pk
            
            # Get product info
            
            for product in cart_products:
                product_id = product.id
                # Get product price
                if product.on_sale:
                    price = product.sale_price
                else:
                    price = product.price
                    
                # Get quantity
                for key, value in quantities.items():
                    if int(key) == product.id:
                        # value
                        create_order_item = OrderItems(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
                        create_order_item.save()
                        
            # Delete the cart after checkout
            for key in list(request.session.keys()):
                if key == 'session_key':
                    # Delete key
                    del request.session[key]
            
            # DELETE THE CART FROM THE DATABASE
            current_user = Profile.objects.filter(user__id=request.user.id)
            # Clear the old cart data (usually stored as a string or JSON)
            current_user.update(old_cart="")
            
            messages.success(request, 'Order Placed!')
            return redirect('home')
        
        else:
            # Not logged in
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()
            
            # Add order items
            # Get the order ID
            order_id = create_order.pk
            
            # Get product info
            
            for product in cart_products:
                product_id = product.id
                # Get product price
                if product.on_sale:
                    price = product.sale_price
                else:
                    price = product.price

                # Get quantity
                for key, value in quantities.items():
                    if int(key) == product.id:
                        # value
                        create_order_item = OrderItems(order_id=order_id, product_id=product_id, quantity=value, price=price)
                        create_order_item.save()

            # Delete the cart after checkout
            for key in list(request.session.keys()):
                if key == 'session_key':
                    # Delete key
                    del request.session[key]
                        
            messages.success(request, 'Order Placed!')
            return redirect('home')
            
        
        
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')
    

def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True)
        if request.POST:
            status = request.POST['shipping_status']
            order_id = request.POST['order_id']
            # Get the order
            order = Order.objects.filter(id=order_id)
            
            order.update(shipped=False)
            return redirect('home')
        
        return render(request, 'payment/shipped_dash.html', {'orders': orders}) 
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')
    

def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False)
        if request.POST:
            status = request.POST['shipping_status']
            order_id = request.POST['order_id']
            # Get the order
            order = Order.objects.filter(id=order_id)
            
            now = datetime.datetime.now()
            order.update(shipped=True, date_shipped=now)
            
            messages.success(request, 'Shipping status updated')
            return redirect('home')
        return render(request, 'payment/not_shipped_dash.html', {'orders': orders}) 
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')


def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        # Get the order
        order = Order.objects.get(id=pk)
        # Get the order items
        items = OrderItems.objects.filter(order=pk)
        
        if request.POST:
            status = request.POST['shipping_status']
            # Check if true or false
            if status == 'true':
                # Get the order
                order = Order.objects.filter(id=pk)
                # Update the order
                now = datetime.datetime.now()
                order.update(shipped=True, date_shipped=now)
                
            else:
                # Get the order
                order = Order.objects.filter(id=pk)
                # Update the order
                order.update(shipped=False)
            messages.success(request, 'Shipping status updated')
            return redirect('home')
        
        return render(request, 'payment/orders.html', {'order': order, 'items': items})