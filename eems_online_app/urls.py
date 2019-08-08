from django.conf.urls import url
from eems_online_app.views import *
#index, load_eems_user_model, run_eems, download, link, login, upload, upload_form, get_additional_info, upload_files

from django.conf.urls import include
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', index, name='index'),
    #url(r'^home$', index, name='index'),

    # Wrapper Authentication Functions
    # CNPS
    url(r'^w_cnps_login/$', auth_views.login, {'template_name': 'admin/cnps/login.html'}, name='login'),
    url(r'^w_cnps_auth$', w_cnps_auth, name='w_cnps_auth'),

    url(r'^w_logout$', auth_views.logout, {'next_page': '/w_logged_out'}),
    url(r'^w_logged_out/$', w_logged_out, name='w_logged_out'),

    url(r'^run_eems$', run_eems, name='run_eems'),
    url(r'^download$', download, name='download'),
    url(r'^link$', link, name='link'),
    #url(r'^login$', login, name='login'),
    url(r'^login/$', RedirectView.as_view(url='upload'), name='upload'),
    url(r'^login/upload$', upload, name='upload'),
    url(r'^upload_files$', upload_files, name='upload_files'),
    url(r'^upload_form$', upload_form, name='upload_form'),
    url(r'^get_additional_info$', get_additional_info, name='get_additional_info'),
    #url(r'^login/$', RedirectView.as_view(url='/admin')),
    url(r'logout/$', auth_views.logout, {'next_page': '/logged_out'}),
    url(r'^logged_out/$', logged_out, name='logged_out'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^check_eems_status', check_eems_status, name='check_eems_status'),
    url(r'^check_eems_model_run_status', check_eems_model_run_status, name='check_eems_model_run_status'),
    url(r'^get_raster_data', get_raster_data, name='get_raster_data'),
]

#admin.site.index_template = 'upload.html'
admin.autodiscover()

admin.site.site_header = 'EEMS Online'

