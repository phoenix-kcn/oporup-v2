from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, UpdateUserForm, UpdatePasswordForm, UpdateInfoForm
from django.db.models import Q
import json
from cart.cart import Cart
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django.core.paginator import Paginator

# New home view with pagination
def home(request):
    product_list = Product.objects.all().order_by('id') # Must handle ordering
    paginator = Paginator(product_list, 12) # Show 12 contacts per page.

    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'home.html', {'products': products})


def about(request):
    return render(request, 'about.html', {})

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Get the shopping cart stuff
            current_user = Profile.objects.get(user__id=request.user.id)
            # Get their saved cart from database
            saved_cart = current_user.old_cart
            
            # Convert database string to python dict.
            if saved_cart:
                # convert to dictionary using JSON
                converted_cart = json.loads(saved_cart)
                
                # Add the loaded cart dictionary to our session
                cart = Cart(request)
                
                for key, value in converted_cart.items():
                    # cart.add(product=key, quantity=value)
                    cart.db_add(product=key, quantity=value)
                    
            
            messages.success(request, "You have successfully logged in.")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
        
    return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')


# def register_user(request):
#     form = SignUpForm()
#     if request.method == 'POST':
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             raw_password = form.cleaned_data.get('password1')
            
#             # log in user after registration
#             user = authenticate(username=username, password=raw_password)
#             login(request, user)
#             messages.success(request, "Registration successful. Fill out the form to continue.")
#             return redirect('update_info')
#         else:
#             for error in list(form.errors.values()):
#                 messages.error(request, error)
#             return redirect('register')
#     return render(request, 'register.html', {'form': form})

def register_user(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save() # This returns the user object            
            login(request, user) # Log them in directly
            
            messages.success(request, "Registration successful.")
            return redirect('update_info')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
            return redirect('register')
    return render(request, 'register.html', {'form': form})


def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    return render(request, 'product_detail.html', {'product': product})

 
    
def category(request, foo):
    # 1. Replace hyphens with spaces to match category names
    category_name = foo.replace('-', ' ')
    
    try:
        # 2. FIX: Use .get() and the correct field name 'name'
        # This retrieves a single Category object or raises Category.DoesNotExist
        category = Category.objects.get(name=category_name)
        
        # 3. Filter products using the single Category object
        products = Product.objects.filter(category=category)
        
        # Pass both the QuerySet of products and the single category object to the template
        return render(request, 'category.html', {'products': products, 'category': category})
    
    except Category.DoesNotExist:
        # 4. Handle the specific case where the category is not found
        messages.error(request, f"The category '{category_name}' does not exist.")
        return redirect('home')
    # Note: If Product is missing a 'category' field or the field name is wrong, 
    # you might still need to handle a FieldError, but the Category issue is solved.
    
    
def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {'categories': categories})

    
def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None,instance=current_user) 
        if user_form.is_valid():
            user_form.save()
            
            login(request, current_user)
            messages.success(request, "Your profile was successfully updated!")
            
            return redirect('home')
        return render(request, 'update_user.html', {'form': user_form})
    
    else:
        messages.warning(request, "You need to be logged in to update your profile.")
        return redirect('login')
    
    
def update_password(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        # did they fill out the form?
        if request.method == 'POST':
            form = UpdatePasswordForm(user=current_user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password was successfully updated!")
                # login(request, current_user)
                return redirect('login')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                return redirect('update_password')
        else:
            form = UpdatePasswordForm(user=current_user)
        return render(request, 'update_password.html', {'form': form})
    
    
def update_info(request):
    if request.user.is_authenticated:
        #Get current user 
        current_user = Profile.objects.get(user__id=request.user.id)
        # Get Original User Form
        form = UpdateInfoForm(request.POST or None,instance=current_user) 
        # Get current User's shipping address
        # shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        shipping_user = ShippingAddress.objects.filter(user=request.user).first()
        # Get User's Shipping Form
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        
        if form.is_valid() or shipping_form.is_valid():
            # Save original form
            form.save()
            # Save shipping form
            shipping_form.save()
            messages.success(request, "Your info was successfully updated!")
                
            return redirect('home')
        return render(request, 'update_info.html', {'form': form, 'shipping_form': shipping_form})
        
    else:
        messages.warning(request, "You need to be logged in to update your info.")
        return redirect('home')
    
    
def search(request):
    if request.method == 'POST':
        search = request.POST.get('searched', '').strip()
        
        if search:
            searched_products = Product.objects.filter(Q(name__icontains=search) | Q(description__icontains=search))
            
            if not searched_products:
                messages.warning(request, 'That product does not exist.')
                return render(request, 'search.html', {})
            else:
                return render(request, 'search.html', {'products': searched_products, 'search': search})
    
        else:
            # This handles the case where the user pressed "Search" with an empty box
            messages.info(request, "Please enter a search term.")
            return render(request, 'search.html', {})
    else:
        return render(request, 'search.html', {})