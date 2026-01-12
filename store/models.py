from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from imagekit.models import ImageSpecField 
from imagekit.processors import ResizeToFill
from PIL import Image
from django.core.files.base import ContentFile
import os
from io import BytesIO

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon_img = models.ImageField(upload_to='uploads/category_icons/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # 1. Detect if the image has changed
        is_new_image = False
        
        if self.pk:
            try:
                old_obj = Category.objects.get(pk=self.pk)
                # Compare the new image object against the old one
                if old_obj.icon_img != self.icon_img:
                    is_new_image = True
            except Category.DoesNotExist:
                pass # Object is new, so it doesn't exist in DB yet
        else:
            # No primary key means this is a new object
            is_new_image = True

        # 2. Only resize if there is an image AND it is new
        if self.icon_img and is_new_image:
            img = Image.open(self.icon_img)

            if img.height > 320 or img.width > 460:
                output_size = (460, 320)
                img.thumbnail(output_size)

                buffer = BytesIO()
                # Maintain original format or fallback to JPEG
                img_format = img.format if img.format else 'JPEG'
                img.save(buffer, format=img_format)

                # 3. Use os.path.basename to get just the filename (fixes path duplication bugs)
                file_name = os.path.basename(self.icon_img.name)
                
                # Save the new resized file
                self.icon_img.save(file_name, ContentFile(buffer.getvalue()), save=False)

        # 4. Call the parent save method
        super().save(*args, **kwargs)

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