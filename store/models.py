from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from imagekit.models import ImageSpecField 
from imagekit.processors import ResizeToFill
from PIL import Image


# Category Model
class  Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon_img = models.ImageField(upload_to='uploads/category_icons/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # 1. Save the instance first so the file is created on the filesystem
        super().save(*args, **kwargs)

        # 2. Open the image if it exists
        if self.icon_img:
            img_path = self.icon_img.path

            try:
                img = Image.open(img_path)

                # 3. Define the maximum size (e.g., 100x100 pixels for an icon)
                output_size = (50, 50)

                # 4. Resize if the image is larger than the output size
                if img.height > 50 or img.width > 50:
                    img.thumbnail(output_size)
                    img.save(img_path) # Overwrite the file with the smaller version
            except Exception as e:
                # Handle cases where the file might not be a valid image
                print(f"Error resizing image: {e}")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    

# Customer Model
class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Product Model
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000, default='', blank=True)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    image = models.ImageField(upload_to='uploads/products/')
    
    # Original high-res image
    image = models.ImageField(upload_to='uploads/products/')
    
    # NEW: Auto-generated thumbnail (300x300 pixels)
    image_thumbnail = ImageSpecField(source='image',
                                     processors=[ResizeToFill(300, 300)],
                                     format='JPEG',
                                     options={'quality': 60})

    #Adding sales status
    on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name


# Customer Order
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    order_date = models.DateField(default=datetime.datetime.now)
    phone = models.CharField(max_length=15, default='')
    address = models.CharField(max_length=200, default='', blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.product
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_modified = models.DateTimeField(User, auto_now=True)
    phone = models.CharField(max_length=15, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    zipcode = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    old_cart = models.CharField(max_length=400, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

# Create a user Profile by deault when a User is created
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        
# Automate the profile creation
post_save.connect(create_user_profile, sender=User)