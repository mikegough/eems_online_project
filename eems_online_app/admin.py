from django.contrib import admin
from models import EemsOnlineModels
from django.contrib.auth.models import Permission
admin.site.register(Permission)
admin.autodiscover()

# Register your models here.
class EEMSAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    list_filter = ('owner', 'user', 'author', 'project', 'status')
    list_display = ('id', 'upload_datetime', 'name', 'project', 'user', 'status', 'log')
    ordering = ('upload_datetime',)
    def get_queryset(self, request):
        query = super(EEMSAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return query
        else:
            return query.filter(user=request.user.username)
admin.site.register(EemsOnlineModels, EEMSAdmin)
