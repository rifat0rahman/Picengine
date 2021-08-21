
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
    path('seoimages',views.seoimages,name='image-count'),
    # STRIPE
    path('create-checkout-session/<str:id>',views.create_payment,name="stripe"),
    path('<str:id>/landing',views.landing,name="landing"),
    path('webhook/stripe',views.my_webhook_view,name="stripe_webhook"),

    # email sending
    path('send_email',views.send_email),
    path('contact_us',views.contact_us),

    # email and password changing
    path('change_password',views.change_password,name='change_password'),
    path('change_email',views.change_email,name="change_email"),
    path('create_account',views.create_account,name="create_account"),
    path('update_email',views.update_email,name="update_email"),
    path('change_name',views.change_name,name="change_name"),
    path('license',views.license,name="license"),

    # forget password
    path('forget_password',views.forget_password,name="forget_password"),
    path('forget_verify',views.forget_verify,name="forget_verify"),
    path('forget_email',views.forget_email,name="forget_email"),
    
    # create license
    path('create_license/<number>',views.create_license,name='create_license')
]




