from rest_framework import serializers
from django.contrib.auth.models import User
from . models import Consumers

#user serializser
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email','first_name')


class ConsumersSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.email')

    account_type = serializers.CharField(source='get_accountType_display')

    class Meta:
        model = Consumers
        fields = ('id','account_type','created',
                'updated','user','acessOngen','acessOnseo',
                'premium_image_count','basic_image_count',
                'basic_credits','premium_credits'
                )


            