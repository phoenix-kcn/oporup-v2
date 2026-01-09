from store.models import Product, Profile

class Cart():
    def __init__(self, request):
        self.session = request.session
        # Get the reqest
        self.request = request
        # Get the current session key if it exists
        cart = self.session.get('session_key')
        
        # If the user is new, No session key! Create one!
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
            
        # Make sure cart is avaliable on all pages of site
        self.cart = cart
    
    
    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = str(quantity)
        
        
        if product_id in self.cart:
            # INCREMENT: Add the new quantity to the existing one
            self.cart[product_id] += int(product_qty)
        else:
            # self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = int(product_qty)
            
        self.session.modified = True
        
        if self.request.user.is_authenticated:
            # Get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            
            current_user.update(old_cart=str(carty))
            
    def db_add(self, product, quantity):
        product_id = str(product)
        product_qty = str(quantity)
        
        
        if product_id in self.cart:
            # INCREMENT: Add the new quantity to the existing one
            self.cart[product_id] += int(product_qty)
        else:
            # self.cart[product_id] = {'price': str(product.price)}
            self.cart[product_id] = int(product_qty)
            
        self.session.modified = True
        
        if self.request.user.is_authenticated:
            # Get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            
            current_user.update(old_cart=str(carty))        
    
    def __len__(self):
        return len(self.cart)
    
    def get_products(self):
        # Get ids from cart
        product_ids = self.cart.keys()
        #Use ids to lookup products in Database model
        products = Product.objects.filter(id__in=product_ids)
        
        return products
    
    def get_quantities(self):
        quantities = self.cart
        return quantities
    
    
    def update(self, product_id, quantity):
        product_id = str(product_id)
        product_qty = str(quantity)
        
        # Get cart
        ourcart = self.cart
        # Update cart/Dictonary
        ourcart[product_id] = int(product_qty)
        
        self.session.modified = True
        
        thing = self.cart
        return thing
    
    
    def delete(self, product):
        product_id = str(product)
        
        if product_id in self.cart:
            del self.cart[product_id]
            
        self.session.modified = True
        
        # Deal with logged in user!!!
        if self.request.user.is_authenticated:
            # Get the current user profile
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            
            current_user.update(old_cart=str(carty))  
        
    def cart_total(self):
        # Get product ids
        product_ids = self.cart.keys()
        # Lookup those keys in our products database model
        products = Product.objects.filter(id__in=product_ids)
        # Get quantities
        quantities = self.cart
        # Start counting at 0
        total = 0
        for key, value in quantities.items():
            # key = product id
            # value = quantity
            for product in products:
                if product.id == int(key):
                    if product.on_sale:
                        total += product.sale_price * value
                    else:
                        total += product.price * value
        return total