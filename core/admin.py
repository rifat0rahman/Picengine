from .models import Consumers,ImageCount, Product,SeoImage
from django.contrib import admin



# admin.model admin for showing data in the admin panel
class ConsumersAdmin(admin.ModelAdmin):
    list_display = ['user','accountType','created']
    search_fields = ['user__email','user__username']
    list_filter = ['accountType','created']

admin.site.register(Consumers,ConsumersAdmin)
admin.site.register(ImageCount)
admin.site.register(Product)
admin.site.register(SeoImage)