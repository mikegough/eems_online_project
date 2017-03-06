from django.conf.urls import url
from eems_online_app.views import index, load_eems_user_model, run_eems, download, link, login, upload, upload_form, get_additional_info, upload_files

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^home$', index, name='index'),
    url(r'^load_eems_user_model$', load_eems_user_model, name='load_eems_user_model'),
    url(r'^run_eems$', run_eems, name='run_eems'),
    url(r'^download$', download, name='download'),
    url(r'^link$', link, name='link'),
    url(r'^login$', login, name='login'),
    url(r'^upload$',upload, name='upload'),
    url(r'^upload_files$',upload_files, name='upload_files'),
    url(r'^upload_form$',upload_form, name='upload_form'),
    url(r'^get_additional_info$', get_additional_info, name='get_additional_info'),
]

