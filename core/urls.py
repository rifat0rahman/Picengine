
from os import name
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    path('register',views.registration,name='registration'),
    path('login',views.logins,name='login'),
    path('users',views.users,name='users'),
    path('consumers',views.consumers,name='consumers'),
    path('logout',views.logOut,name='logout'),
    path('image-count',views.images_count,name='image-count'),
    # STRIPE
    path('create-checkout-session/<str:id>',views.create_payment,name="stripe"),
    path('<str:id>/landing',views.landing,name="landing"),
    path('webhook/stripe',views.my_webhook_view,name="stripe_webhook"),
    path('seoimages',views.seoimages,name="seoimages")
]
