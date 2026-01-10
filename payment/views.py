from django.shortcuts import render, redirect
from cart.cart import Cart
from django.contrib import messages
from payment.forms import ShippingForm, PaymentForm
from .models import ShippingAddress, Order, OrderItems
from django.contrib.auth.models import User
from store.models import Product, Profile
import datetime
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from sslcommerz_lib import SSLCOMMERZ


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

        # --- THE FIX STARTS HERE ---
        # 1. Create a dictionary that maps the HTML input names to the Billing Template variable names
        shipping_info = {
            'shipping_full_name': request.POST.get('full_name'),
            'shipping_email': request.POST.get('email'),
            'shipping_address1': request.POST.get('address1'),
            'shipping_address2': request.POST.get('address2'),
            'shipping_city': request.POST.get('city'),
            'shipping_state': request.POST.get('state'),
            'shipping_country': request.POST.get('country'),
            'shipping_zipcode': request.POST.get('zipcode'),
        }

        # 2. Save this MAPPED dictionary to the session 
        # (Now 'my_shipping' in the session will also have the correct keys for the next step)
        request.session['my_shipping'] = shipping_info
        
        # 3. Pass 'shipping_info' (the dictionary we just made) to the context
        billing_form = PaymentForm()
        return render(request, 'payment/billing_info.html', {
            'cart_products': cart_products, 
            'quantities': quantities, 
            'totals': totals, 
            'billing_form': billing_form,
            'shipping_info': shipping_info 
        })
        # --- THE FIX ENDS HERE ---
    
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')
    
def process_order(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_products()
        quantities = cart.get_quantities()
        totals = cart.cart_total()
        
        # Get shipping Session Data
        my_shipping = request.session.get('my_shipping')
        if not my_shipping:
            messages.error(request, "Shipping info missing")
            return redirect('checkout')

        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals

        # 1. Create the Order (Mark as NOT paid initially)
        user = request.user if request.user.is_authenticated else None
        
        create_order = Order(
            user=user, 
            full_name=full_name, 
            email=email, 
            shipping_address=shipping_address, 
            amount_paid=amount_paid,
            paid=False  # Explicitly set to False
        )
        create_order.save()

        # 2. Add Order Items
        order_id = create_order.pk
        for product in cart_products:
            product_id = product.id
            if product.on_sale:
                price = product.sale_price
            else:
                price = product.price
            
            for key, value in quantities.items():
                if int(key) == product.id:
                    OrderItems.objects.create(
                        order_id=order_id, 
                        product_id=product_id, 
                        user=user, 
                        quantity=value, 
                        price=price
                    )

        # 3. SSLCommerz Configuration
        sslcz_settings = { 
            'store_id': settings.SSLCOMMERZ_STORE_ID, 
            'store_pass': settings.SSLCOMMERZ_STORE_PASS, 
            'issandbox': settings.SSLCOMMERZ_ISSANDBOX 
        }
        sslcz = SSLCOMMERZ(sslcz_settings)
        
        # Build the dynamic URLs for callbacks
        current_host = request.build_absolute_uri('/')[:-1] # gets http://127.0.0.1:8000
        
        post_body = {
            'total_amount': float(totals),
            'currency': "BDT",
            'tran_id': f"Ord_{order_id}", # Unique Transaction ID
            'success_url': f"{current_host}/payment/payment_success_callback/",
            'fail_url': f"{current_host}/payment/payment_fail/",
            'cancel_url': f"{current_host}/payment/payment_cancel/",
            'emi_option': 0,
            'cus_name': full_name,
            'cus_email': email,
            'cus_phone': "01700000000", # Add phone to your shipping form if needed
            'cus_add1': my_shipping['shipping_address1'],
            'cus_city': my_shipping['shipping_city'],
            'cus_country': my_shipping['shipping_country'],
            'shipping_method': "NO",
            'multi_card_name': "",
            'num_of_item': len(cart_products),
            'product_name': "Goods",
            'product_category': "General",
            'product_profile': "general"
        }

        # 4. Request Session and Redirect
        response = sslcz.createSession(post_body)
        
        if 'GatewayPageURL' in response:
            return redirect(response['GatewayPageURL'])
        else:
            messages.error(request, "Error connecting to Payment Gateway")
            return redirect('checkout')
            
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')

@csrf_exempt
def payment_success_callback(request):
    if request.method == 'POST' or request.method == 'post':
        payment_data = request.POST
        
        # Extract the transaction ID we sent (e.g., "Ord_55")
        tran_id = payment_data.get('tran_id')
        val_id = payment_data.get('val_id') # Bank's validation ID
        
        # Parse the Order ID from tran_id
        try:
            order_id = int(tran_id.split('_')[1])
            order = Order.objects.get(id=order_id)
            
            # Update Order Status
            order.paid = True
            order.transaction_id = val_id # Store the bank reference
            order.save()
            
            # --- START: Clear Cart Logic (Moved from process_order) ---
            
            # Clear Session Cart
            for key in list(request.session.keys()):
                if key == 'session_key':
                    del request.session[key]
            
            # Clear Database Cart (if user is logged in)
            if request.user.is_authenticated:
                current_user = Profile.objects.filter(user__id=request.user.id)
                current_user.update(old_cart="")
            
            # --- END: Clear Cart Logic ---

            return render(request, 'payment/payment_success.html', {'order': order})

        except Order.DoesNotExist:
            return render(request, 'payment/payment_fail.html', {'message': 'Order not found'})
    
    return render(request, 'payment/payment_fail.html')


@csrf_exempt
def payment_fail(request):
    return render(request, 'payment/payment_fail.html')

@csrf_exempt
def payment_cancel(request):
    return render(request, 'payment/payment_cancel.html')

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