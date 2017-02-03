from django.conf.urls import url
from eems_online_app.views import index, load_eems_user_model, run_eems, download, link, upload_form, upload_submit, check_pass, get_additional_info

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^home$', index, name='index'),
    url(r'^load_eems_user_model$', load_eems_user_model, name='load_eems_user_model'),
    url(r'^run_eems$', run_eems, name='run_eems'),
    url(r'^download$', download, name='download'),
    url(r'^link$', link, name='link'),
    url(r'^upload$', upload_form, name='upload_form'),
    url(r'^upload_submit$', upload_submit, name='upload_submit'),
    url(r'^check_pass$', check_pass, name='check_pass'),
    url(r'^get_additional_info$', get_additional_info, name='get_additional_info'),
]

