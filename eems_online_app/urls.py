from django.conf.urls import url
from eems_online_app.views import index

urlpatterns = [
    url(r'^$', index, name='index'),
]

