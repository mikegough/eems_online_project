from django.conf.urls import url
from eems_online_app.views import index, load_eems_user_model, run_eems, download

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^load_eems_user_model$', load_eems_user_model, name='load_eems_user_model'),
    url(r'^run_eems$', run_eems, name='run_eems'),
    url(r'^download$', download, name='download'),
]

