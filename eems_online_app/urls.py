from django.conf.urls import url
from eems_online_app.views import index, load_eems

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^load_eems$', load_eems, name='load_eems'),
]

