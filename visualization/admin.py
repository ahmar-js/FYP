from django.contrib import admin

from .models import MyFileModel

class MyFileModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'file', 'uploaded_at']

admin.site.register(MyFileModel, MyFileModelAdmin)