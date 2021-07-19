from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.fields import CharField
from . models import Consumers,ImageCount,SeoImage

#user serializser
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email')

class ConsumersSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.email')
    class Meta:
        model = Consumers
        fields = ('id','paid','accountType','created',
                'updated','user','acessOngen','acessOnseo')

class ImageCountSerializer(serializers.ModelSerializer):
    # for showing the email as a field
    user = serializers.CharField(source='user.email')
    class Meta:
        model = ImageCount
        fields = ('id','image_processed','updated','user')

class SeoImageSerializer(serializers.ModelSerializer):
    # for showing the email as a field
    user = serializers.CharField(source='user.email')
    class Meta:
        model = SeoImage
        fields = ('id','count','created','user')