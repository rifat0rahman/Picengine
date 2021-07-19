
from django.contrib.auth.backends import RemoteUserBackend
from django.shortcuts import render
from rest_framework import response, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.auth.models import User
from stripe.api_resources import plan
from stripe.api_resources.checkout import session
from stripe.six import reraise
from . serializers import SeoImageSerializer, UserSerializer, ConsumersSerializer,ImageCountSerializer
from .models import Consumers,ImageCount,Product,SeoImage
from rest_framework import status 
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from rest_framework.decorators import api_view, renderer_classes
from django.http import HttpResponse
import json
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import datetime
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY
#Stripe

@api_view(["GET","POST"])
def create_payment(request,id):
    if request.method == 'POST':
        product = Product.objects.get(id=id)
        YOUR_DOMAIN = "https://picengine.netlify.app/"
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': product.price,
                        'product_data': {
                            'name': product.name,
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                "product_id": product.id
            },
            mode='payment',
            success_url=YOUR_DOMAIN + 'profile/',
            cancel_url=YOUR_DOMAIN + 'deshboard/',
        )
        return JsonResponse({'id': checkout_session.id},status=200)

    return Response({'data':'data'})


def landing(request,id):
    product = Product.objects.get(id=id)
    context = {
        'STRIPE_PUBLIC_KEY':settings.STRIPE_PUBLIC_KEY,
        'product':product,
    }
    return render(request,'landing.html',context)



@csrf_exempt
def my_webhook_view(request):
    payload = request.body
    event = None
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
                payload,sig_header,settings.STRIPE_WEBHOOK_SECRET
            )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object # contains a stripe.PaymentIntent
        # Then define and call a method to handle the successful payment intent.
        # handle_payment_intent_succeeded(payment_intent)
    elif event.type == 'payment_method.attached':
        payment_method = event.data.object # contains a stripe.PaymentMethod
        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event.type))

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_email = session["customer_details"]["email"]
        plan_id = session['metadata']['product_id']
        print(session)
        user = User.objects.filter(email=customer_email)
        if len(user):
            consumers = Consumers.objects.get(user=user[0])
            consumers.accountType = plan_id
            consumers.acessOngen = True
            consumers.acessOnseo = True
            consumers.save()

    return HttpResponse(status=200)






@api_view(['GET'])
def home(request):
    endpoints = {
        'login': 'http://127.0.0.1:8000/login',
        'registration':'http://127.0.0.1:8000/register',
        'users': 'http://127.0.0.1:8000/users',
        'consumers': 'http://127.0.0.1:8000/consumers',
        'logout': 'http://127.0.0.1:8000/logout',
        'imagecount': 'http://127.0.0.1:8000/image-count',

    }
    return Response({"endpionts": endpoints})


@api_view(['POST'])
def registration(request):
    if request.method == 'POST':
        data = request.data
        username = data['username']
        email=data['email']
        password=data['password1']
        password2 = data['password2']

        if len(password) < 6:
            return Response({'status': 'password must be up to 6 latters'}, 
                            status=status.HTTP_404_NOT_FOUND)
        if password != password2:
            return Response({'status': 'password should be same'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        if User.objects.filter(username=username):
            return Response({'status': 'username has been used, try another one'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        if User.objects.filter(email=email):
            return Response({'status': 'email has been used try another one'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = User.objects.create(
            username=username,
            email=email,
            password=password
        )

        user.save()
        # login user auto
        consumers = Consumers.objects.create(user=user)
        consumers.save()
        imagecount = ImageCount.objects.create(user=user)
        imagecount.save()
        seoimages = SeoImage.objects.create(user=user)
        seoimages.save()
        print('user created')

        return Response({'user':user.email})


@api_view(['POST'])
def logins(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.data['email'])
            log = authenticate(username=user.username,password=request.data['password'])
            if log is not None:
                login(request,log)

            return Response({'status':user.email}, status=200)

        except:
            return Response({'status': 'Email or Password is incorrect'},status=status.HTTP_406_NOT_ACCEPTABLE)
        


@api_view(['GET'])
def users(request):
    users = User.objects.all()
    serializers = UserSerializer(users, many=True)
    return Response(serializers.data, status=200)


@api_view(['GET'])
def consumers(request):
    consumers = Consumers.objects.all()
    serializers = ConsumersSerializer(consumers, many=True)
    return Response(serializers.data, status=200)

@api_view(['POST'])
def logOut(request):
    logout(request)
    return Response({'logout':'logout'})

@api_view(['GET','POST'])
def images_count(request):
    if request.method == 'POST':
        user = User.objects.get(email=request.data['token'])
        consumer = Consumers.objects.get(user=user)
        Count = ImageCount.objects.get(user=user)
        seo = SeoImage.objects.get(user=user)

        period = 31
        day_added = datetime.timedelta(days=period)
        sesson_ex = consumer.updated.date() + day_added

        current_time = datetime.datetime.now().date()

        if sesson_ex <= current_time:
            consumer.accountType = 'FREE'
            consumer.acessOngen = False
            consumer.acessOnseo = False
            consumer.save()
      
        # print(consumer.updated.date())
        if consumer.accountType == 'FREE':
            if Count.image_processed < 100:
                Count.image_processed +=1
            else:
                consumer.acessOngen = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)
        if consumer.accountType == '1':
            if Count.image_processed <= 1000:
                Count.image_processed +=1
            elif Count.image_processed > 1000 and seo.count > 50:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOngen = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        if consumer.accountType == '2':
            if Count.image_processed <= 5000:
                Count.image_processed +=1
            elif Count.image_processed > 5000 and seo.count > 100:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOngen = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        if consumer.accountType == '3':
            if Count.image_processed <= 12000:
                Count.image_processed +=1
            elif Count.image_processed > 12000 and seo.count >200:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOngen = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)
    
        Count.save()
        return Response(status=200)

    images = ImageCount.objects.all()
    serializers = ImageCountSerializer(images, many=True)
    return Response(serializers.data, status=200)

@api_view(['GET','POST'])
def seoimages(request):
    if request.method == 'POST':
        user = User.objects.get(email=request.data['token'])
        consumer = Consumers.objects.get(user=user)
        Count = ImageCount.objects.get(user=user)
        seo = SeoImage.objects.get(user=user)

        period = 31
        day_added = datetime.timedelta(days=period)
        sesson_ex = consumer.updated.date() + day_added

        current_time = datetime.datetime.now().date()

        if sesson_ex <= current_time:
            consumer.accountType = 'FREE'
            consumer.acessOngen = False
            consumer.acessOnseo = False
            consumer.save()

        if consumer.accountType == 'FREE':
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        if consumer.accountType == '1':
            if Count.image_processed <=50:
                Count.image_processed +=1
            elif Count.image_processed > 1000 and seo.count > 50:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOnseo = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        if consumer.accountType == '2':
            if Count.image_processed <= 50:
                Count.image_processed +=1
            elif Count.image_processed > 5000 and seo.count > 100:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOnseo = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        if consumer.accountType == '3':
            if Count.image_processed <= 200:
                Count.image_processed +=1
            elif Count.image_processed > 12000 and seo.count >200:
                consumer.accountType = 'FREE'
                consumer.save()
            else:
                consumer.acessOnseo = False
                consumer.save()
                return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A PLAN'},status=status.HTTP_406_NOT_ACCEPTABLE)

        Count.save()
        return Response(status=200)


    images = SeoImage.objects.all()
    serializers = SeoImageSerializer(images,many=True)

    return Response(serializers.data,status=200)
