
from django.db import models
from django.contrib.auth.models import  User
# Create your models here.

TYPE = (
    ("3", "premium"),
    ("2", "standard"),
    ("1", "basic"),
    ('FREE','free'),
)

class Consumers(models.Model):
    user = models.ForeignKey(User,related_name="userstatus",on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    accountType = models.CharField(max_length=50,choices=TYPE,default='FREE')
    acessOnseo = models.BooleanField(default=False)
    acessOngen = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.user.email

class ImageCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_processed = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return self.user.email

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now=True)

    def product_price(self):
        return "{0:.2f}".format(self.price/100)

    def __str__(self):
        return self.name

class SeoImage(models.Model):
    user = models.ForeignKey(User,related_name='user_seo', on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)