
from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import EmailField
# Create your models here.


# return email instead of username here
def get_email(self):
    return self.email

User.add_to_class("__str__", get_email)


TYPE = (
    ("4", "custom"),
    ("3", "premium"),
    ("2", "standard"),
    ("1", "basic"),
    ('FREE','free'),
)


class Consumers(models.Model):
    user = models.ForeignKey(User,related_name="userstatus",on_delete=models.CASCADE)
    accountType = models.CharField(max_length=50,choices=TYPE,default='FREE')
    basic_credits = models.IntegerField(default=100)
    premium_credits = models.IntegerField(default=0)
    durations = models.IntegerField(default=30)
    acessOnseo = models.BooleanField(default=False)
    acessOngen = models.BooleanField(default=True)
    basic_image_count = models.IntegerField(default=0)
    premium_image_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.user.email


class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    basic_credits = models.IntegerField(default=100)
    premium_credits = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now=True)

    def product_price(self):
        return "{0:.2f}".format(self.price/100)

    def __str__(self):
        return self.name

class VerifyCode(models.Model):
    email = models.EmailField(max_length=254)
    code = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.email