
# imports from django
from django.db.models.fields import EmailField
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
# import from rest framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# imports from my app
from . serializers import UserSerializer, ConsumersSerializer
from .models import Consumers, Product, VerifyCode, License


# imports from stripe
import stripe

# core python
import datetime


# stripe key
stripe.api_key = settings.STRIPE_SECRET_KEY


# stripe setup here
@api_view(["GET", "POST"])
def create_payment(request, id):
    if request.method == 'POST':
        YOUR_DOMAIN = "https://picengine.io/"  # frontend url

        product = Product.objects.get(id=id)
        price = product.price
        name = product.name

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': price,
                        'product_data': {
                            'name': name,
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                "product_id": product.id
            },
            mode='payment',
            success_url=YOUR_DOMAIN + 'deshboard/',
            cancel_url=YOUR_DOMAIN + 'cancel/',
        )
        return JsonResponse({'id': checkout_session.id}, status=200)

    return Response({'data': 'data'})


# backend pricing page
def landing(request, id):
    product = Product.objects.get(id=id)

    context = {
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
        'product': product,
    }
    return render(request, 'landing.html', context)



# stripe webhooks, for tracking the pyment flow
@csrf_exempt
def my_webhook_view(request):
    payload = request.body
    event = None
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object

    elif event.type == 'payment_method.attached':
        payment_method = event.data.object

    else:
        print('Unhandled event type {}'.format(event.type))

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_email = session["customer_details"]["email"]

        plan_id = session['metadata']['product_id']

        user = User.objects.filter(email=customer_email)
        product = Product.objects.get(id=plan_id)

        if len(user):
            consumers = Consumers.objects.get(user=user[0])
            consumers.accountType = plan_id
            consumers.basic_credits = product.basic_credits
            consumers.premium_credits = product.premium_credits
            consumers.acessOnseo = True
            consumers.save()

    return HttpResponse(status=200)


# home page
@api_view(['GET'])
def home(request):
    endpoints = {
        'login': 'restricted',
    }
    return Response({"endpionts": endpoints})


# register api logic
@api_view(['POST'])
def registration(request):
    if request.method == 'POST':
        data = request.data
        username = data['email']
        email = data['email']
        password = data['password1']
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

        print('hello')
        verify_account(email)
        return Response({'user': 'done'}, status=200)


#________________________________forget_password__________________________#

@api_view(['POST'])
def forget_password(request):
    if request.method == 'POST':
        email = request.data['email']
        password1 = request.data['password1']
        password2 = request.data['password2']

        if len(password1) < 6:
            return Response({'status': 'password must be up to 6 latters'},
                            status=status.HTTP_404_NOT_FOUND)
        if password1 != password2:
            return Response({'status': 'password should be same'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = User.objects.get(email=email)
        user.set_password(password1)
        user.save()

        return Response({'status':'password changed , please login now!'})


@api_view(['POST'])
def forget_verify(request):
    email = request.data['email']
    code = request.data['code']
    try:
        verify = VerifyCode.objects.get(email=email,code=code)
        return Response({'status': email}, status=200)
    except:
        return Response({'status': 'wrong code,please try again'}, status=status.HTTP_406_NOT_ACCEPTABLE)





@api_view(['POST'])
def forget_email(request):
    if request.method == 'POST':
        code = get_random_string(length=6, allowed_chars='1234567890')
        email = request.data['email']
        user = None
        try:
            user = User.objects.get(email=email)
            account = VerifyCode.objects.filter(email=email)
            if len(account):
                account[0].code = code
                account[0].save()
            else:
                account = VerifyCode(email=email, code=code)
                account.save()
        except:
            return Response({'status': 'email does not exists'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # email things
        from_email = 'contact@picengine.io'
        subject = 'Your temporary password for PicEngine'
        body = f"<p>Hi {user.first_name},</p><p>We are sending you a temporary password to login. Please use it to login and change your password as soon as possible.</p><p>{code}</p><p>Let us know if you have any questions!</p><br><p>Thanks!</p><p>Team PicEngine</p>"

        send_mail(subject, body,'PicEngine <contact@picengine.io>', [email], html_message=body)

        return Response({'user': user.email})


#_____________________________forget_pasaword_______________________#



@api_view(['POST'])
def create_account(request):
    if request.method == 'POST':
        data = request.data
        email = data['email']
        name = data['name']
        username = email
        password = data['password']
        code = data['code']
        verify_email = VerifyCode.objects.get(email=email)

        stored_code = verify_email.code
        print(verify_email.code)
        print(code)
        if stored_code == code:
            user = User(
                first_name=name,
                username=username,
                email=email,
            )
            user.set_password(password)
            user.save()

            # login user auto
            consumers = Consumers.objects.create(user=user)
            consumers.save()

            # send email
            # email things
            from_email = 'contact@picengine.io'
            subject = 'Welcome to PicEngine'
            body = f"Hi {user.first_name},<p></p>We're thrilled you've taken the leap and signed up for our service.<p></p><p>Now that your account is active, please take a look at all the awesome tools and let us know if you have any questions.</p><p>We'll be sending you a couple of emails later this week, so be on the lookout!</p><p>We hope to see you reach your goals with us soon!</p><br><p>Cheers,</p><p>Team PicEngine</p>"

            if email:
                send_mail(subject, body,'PicEngine <contact@picengine.io>',
                          [email], html_message=body)
                print('mail sent')

            print('user created')

            return Response({'user': user.email})
        else:
            return Response({'status': 'wrong code,please correct this one'}, status=status.HTTP_406_NOT_ACCEPTABLE)


# change name

@api_view(['POST'])
def change_name(request):
    if request.method == 'POST':
        data = request.data
        name = data['name']
        email = data['email']

        user = User.objects.get(email=email)
        user.first_name = name
        user.save()

        return Response({'status': f'name has been changed to {name}'})


# send verify code
def verify_account(email):

    code = get_random_string(length=6, allowed_chars='1234567890')
    try:
        account = VerifyCode.objects.filter(email=email)
        if len(account):
            account[0].code = code
            account[0].save()
        else:
            verify_code = VerifyCode(email=email, code=code)
            verify_code.save()

        # email things
        from_email = 'contact@picengine.io'
        subject = 'PicEngine account activation'
        body = f"Hi there,<p></p>Thank you for signing up with us, we're excited to have you onboard. Please use this code to activate your account<p></p><br>{code}</b><br/><p>In-case you have any questions, please reply to this email and we, at PicEngine, will be happy to help you with all your queries. Also, if you did not initiate this request, you do not need to do anything.</p><br><p>Thanks,</p><p>Team PicEngine</p>"

        if email:
            send_mail(subject, body,'PicEngine <contact@picengine.io>', [email], html_message=body)
            print('mail sent')
        print(code)

        return Response({'done'})
    except:
        pass


# rifat123456

# change password (beta currently)
@api_view(['POST'])
def change_password(request):
    if request.method == 'POST':
        token = request.data['user']
        old_password = request.data['old_pass']
        new_pass1 = request.data['new_pass']
        new_pass2 = request.data['ag_new_pass']
        user = User.objects.get(email=token)

        if new_pass1 != new_pass2:
            return Response({'status': 'new passwords should match'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        if len(new_pass1) < 6:
            return Response({'status': 'passwords should be upto 6 latters'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        change = authenticate(username=user.username, password=old_password)
        if change is not None:
            print('password changes')
            user.set_password(new_pass1)
            user.save()

            return Response({'status': 'password has been changed!'}, status=200)
        else:
            return Response({'status': 'current password is wrong'}, status=status.HTTP_406_NOT_ACCEPTABLE)

# email changing view
@api_view(['POST'])
def change_email(request):
    if request.method == 'POST':
        email = request.data['email']
        new_email = request.data['new_email']
        user = User.objects.get(email=email)
        if_user = User.objects.filter(email=new_email)

        if len(if_user):
            return Response({'status': 'this email has been used,choose another one'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        verify_account(new_email)
        return Response(status=200)



@api_view(["POST"])
def update_email(request):
    if request.method == 'POST':
        email = request.data['email']
        new_email = request.data['new_email']
        user = User.objects.get(email=email)
        code = request.data['code']

        account = VerifyCode.objects.get(email=new_email)

        if account.code == code:
            user.email = new_email
            user.save()
            return Response({'status': 'email has been changed!', 'email': new_email}, status=200)
        else:
            return Response({'status': 'wrong code,please correct this one'}, status=status.HTTP_406_NOT_ACCEPTABLE)


# login api logic
@api_view(['POST'])
def logins(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.data['email'])

            log = authenticate(username=user.username,
                               password=request.data['password'])

            if log is not None:
                login(request, log)
                return Response({'status': user.email}, status=200)
            else:
                return Response({'status': 'Email or Password is incorrect'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        except:
            return Response({'status': 'Email or Password is incorrect'}, status=status.HTTP_406_NOT_ACCEPTABLE)


# users page
@api_view(['GET'])
def users(request):
    users = User.objects.all()
    serializers = UserSerializer(users, many=True)
    return Response(serializers.data, status=200)

# all of the details of the consumers(users)


@api_view(['GET'])
def consumers(request):
    consumers = Consumers.objects.all()
    serializers = ConsumersSerializer(consumers, many=True)
    return Response(serializers.data, status=200)


@api_view(['POST'])
def logOut(request):
    logout(request)
    return Response({'logout': 'logout'})



# every download is counting here,
@api_view(['POST'])
def images_count(request):
    if request.method == 'POST':

        user = User.objects.get(email=request.data['token'])
        consumer = Consumers.objects.get(user=user)
        license = None
        # expired time
        period = consumer.durations
        day_added = datetime.timedelta(days=period)
        sesson_ex = consumer.updated.date() + day_added
        current_time = datetime.datetime.now().date()

        if sesson_ex <= current_time:
            try:
                license = License.objects.get(user=user)
                if consumer.accountType == 'LTD standard':
                    consumer.basic_credits = license.basic_credits
                    consumer.premium_credits = license.premium_credits
                    consumer.basic_image_count = 0
                    consumer.premium_image_count = 0
                    consumer.durations = license.times
                    consumer.save()
            except:
                pass
            else:
                consumer.accountType = 'FREE'
                consumer.acessOngen = False
                consumer.acessOnseo = False
                consumer.basic_credits = 0
                consumer.premium_credits = 0
                consumer.basic_image_count = 0
                consumer.premium_image_count = 0
                consumer.save()

        # expired ends here

        # calculate the credits
        if consumer.basic_credits > 0:
            consumer.basic_credits -= 1
            consumer.basic_image_count += 1
            consumer.save()
        elif consumer.basic_credits <= 0 and consumer.premium_credits <= 0:
            consumer.acessOngen = False
            consumer.acessOnseo = False
            consumer.accountType = 'FREE'
            consumer.basic_image_count = 0
            consumer.premium_image_count = 0
            consumer.save()
        else:
            consumer.acessOngen = False
            consumer.save()
            return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A NEW PLAN'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        consumer.save()

        return Response(status=200)

    return Response(status=200)




@api_view(['POST'])
def seoimages(request):
    if request.method == 'POST':
        user = User.objects.get(email=request.data['token'])
        consumer = Consumers.objects.get(user=user)
        license = None

        # expired time
        period = consumer.durations
        day_added = datetime.timedelta(days=period)
        sesson_ex = consumer.updated.date() + day_added
        current_time = datetime.datetime.now().date()

        


        if sesson_ex <= current_time:
            try:
                license = License.objects.get(user=user)
                if consumer.accountType == 'LTD standard':
                    consumer.basic_credits = license.basic_credits
                    consumer.premium_credits = license.premium_credits
                    consumer.basic_image_count = 0
                    consumer.premium_image_count = 0
                    consumer.durations = license.times
                    consumer.save()
            except:
                pass
            else:
                consumer.accountType = 'FREE'
                consumer.acessOngen = False
                consumer.acessOnseo = False
                consumer.basic_credits = 0
                consumer.premium_credits = 0
                consumer.basic_image_count = 0
                consumer.premium_image_count = 0
                consumer.save()

        # expired ends here

        # calculate the credits
        if consumer.premium_credits > 0:
            consumer.premium_credits -= 1
            consumer.premium_image_count += 1
            consumer.save()
        elif consumer.basic_credits <= 0 and consumer.premium_credits <= 0:
            consumer.acessOngen = False
            consumer.acessOnseo = False
            consumer.accountType = 'FREE'
            consumer.basic_image_count = 0
            consumer.premium_image_count = 0
            consumer.save()
        else:
            consumer.acessOnseo = False
            consumer.save()
            return Response({'status': 'YOUR LIMIT IS FINISHED,BUY A NEW PLAN'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        consumer.save()

        return Response(status=200)

    return Response(status=200)




# email sending setup here
@api_view(['POST'])
def send_email(request):
    if request.method == 'POST':
        data = request.data

        name = data['name']
        address = data['email']

        details = data['details']
        # from_email = 

        subject = 'Custom Pricing Enquiry'
        body = f'</p> Hey PicEngine Team,<p><p>I am writing to inquire about custom pricing. I want to know how much it would be for my business and if there are any special deals available for people with a high number of processing.</p><p>My details are listed below:</p><p>Email:{address}</p><p>{details}</p><br><p>Thanks,</p><p>{name}</p>'

        if address:

             send_mail(subject, body,'PicEngine <contact@picengine.io>', [
                      'info@picengine.io'], html_message=body)

        return Response({'done'}, status=200)

    return Response(status=200)




# email sending setup here
@api_view(['POST'])
def send_email(request):
    if request.method == 'POST':
        data = request.data

        name = data['name']
        address = data['email']

        details = data['details']
        # from_email = 

        subject = 'Custom Pricing Enquiry'
        body = f'</p> Hey PicEngine Team,<p><p>I am writing to inquire about custom pricing. I want to know how much it would be for my business and if there are any special deals available for people with a high number of processing.</p><p>My details are listed below:</p><p>Email:{address}</p><p>{details}</p><br><p>Thanks,</p><p>{name}</p>'

        if address:

             send_mail(subject, body,'PicEngine <contact@picengine.io>', [
                      'info@picengine.io'], html_message=body)

        return Response({'done'}, status=200)

    return Response(status=200)

# help center
# email sending setup here
@api_view(['POST'])
def contact_us(request):
    if request.method == 'POST':
        data = request.data

        name = data['name']
        address = data['email']
        details = data['details']

        subject = data['subject']

        body = f'</p> Hey PicEngine Team,<p><p>I am writing to inquire an issue.</p><p>My details are listed below:</p><p>Email:{address}</p><p>{details}</p><br><p>Thanks,</p><p>{name}</p>'

        if address:

             send_mail(subject, body,'PicEngine <contact@picengine.io>', [
                      'info@picengine.io'], html_message=body)

        return Response({'done'}, status=200)

    return Response(status=200)







@api_view(['POST'])
def license(request):
    data = request.data
    email = data['email']
    license_code = data['license_code']

    try:
        user = User.objects.get(email=email)
        consumer = Consumers.objects.get(user=user)

        license = License.objects.get(license_code=license_code)
        license.user = user
        license.save()

        #set the consumers
        consumer.accountType = "5"
        consumer.basic_credits = license.basic_credits
        consumer.premium_credits = license.premium_credits
        consumer.durations = license.times
        consumer.basic_image_count = 0
        consumer.premium_image_count = 0
        consumer.acessOnseo = True
        consumer.acessOngen = True
        
        consumer.save()
        return Response({'status': 'License is activated. check the dashboard'}, status=200)
    except:
        return Response({'status': 'License code has expired'}, status=status.HTTP_406_NOT_ACCEPTABLE)






from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def create_license(request,number):
    for i in range(int(number)):
        license = License.objects.create()
        license.save()
    
    return redirect('/admin/core/license/')