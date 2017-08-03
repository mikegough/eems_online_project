from django.contrib import admin
from .models import EemsOnlineModels

# Register your models here.
class EEMSAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload_datetime', 'name', 'user', 'status')
    ordering = ('upload_datetime',)

admin.site.register(EemsOnlineModels, EEMSAdmin)
