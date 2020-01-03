from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.conf import settings
from django.template.loader import render_to_string
from django import forms

import os
import shutil
import zipfile
import glob
import gdal
import re
import time

from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import sys
import subprocess
import sqlite3
from django.utils.crypto import get_random_string

#EEMS Dependencies. pip install from wheels:
    # numpy+MKL (numpy-1.11.3+mkl-cp27-cp27m-win32.whl)
    # netCDF4 (netCDF4-1.2.6-cp27-cp27m-win32.whl after upgrading pip)
    # scipy (scipy-0.18.1-cp27-cp27m-win32.whl)
    # matplotlib (just pip install. No wheel)
    # Also need to add the following lines to activate.bat if running this app from a virtual environment:
        #set TCL_LIBRARY=C:\Python27\ArcGIS10.3\tcl\tcl8.5
        #set TK_LIBRARY=C:\Python27\ArcGIS10.3\tcl\tk8.5
    # GDAL for projecting

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from EEMSCvt20To30 import *
from Convert_GDB_to_NetCDF import *
from MPilotOnlineWorker import *
import numpy

import fileinput

from tasks import *

from rasterstats import zonal_stats
from rasterstats import point_query
import rasterio
import netCDF4
from osgeo import ogr
from osgeo import osr
import glob

from celery.result import AsyncResult

# Generic logout page for wrappers
def w_logged_out(request):
    return render(request, 'wrapper_logged_out.html')


def index(request):

    # Custom Templates for subdomains (e.g., cec.eemsonline.org)
    subdomain = request.get_host().split(".")[0]
    # For Development
    #subdomain = "cnps"

    # EEMS Wrappers requiring custom views/custom login. Redirect to custom view.
    if subdomain == "cnps":
        # if accessed using a model link, store the model id as a session variable.
        request.session['filters'] = request.GET.copy()
        return redirect(ipa)

    # EEMS Wrappers not requiring custom view/custom login
    # subdomain: ["html template name", "Project Name"]
    subdomain_template_map = {
        "cec": ["cec", "CEC"],
        "ssn": ["ssn", ("Fisher")],
    }

    if subdomain in subdomain_template_map:
        hostname_for_link = "http://" + subdomain + "." + settings.HOSTNAME_FOR_LINK
        template = subdomain_template_map[subdomain][0] + ".html"
        filters = {'project': subdomain_template_map[subdomain][1]}
    else:
        hostname_for_link = "http://" + settings.HOSTNAME_FOR_LINK
        template = "index.html"
        # Get any filters passed in through the query string. #copy() makes the request object mutable.
        filters = request.GET.copy()

    # Get a json file of all the EEMS commands
    eems_rqst_dict = {}
    eems_rqst_dict["action"] = 'GetAllCmdInfo'
    my_mpilot_worker = MPilotWorker()
    eems_available_commands_json = my_mpilot_worker.HandleRqst(eems_rqst_dict)
    json.dumps(eems_available_commands_json)

    # Pull model request (link) out of the filters (handled differently). If no model request, default to the first model in the query.
    initial_eems_model_id = filters.pop("model", ['first'])[0]

    # GET all available EEMS Models for Dropdown.
    eems_online_models = {}

    if filters:
        # Filter out IPA models
        query = "SELECT ID, NAME, EXTENT_GCS, SHORT_DESCRIPTION, PROJECT FROM EEMS_ONLINE_MODELS WHERE OWNER = 'CBI' AND STATUS = 1 AND PROJECT <> 'IPA' AND "
        filter_count = 0
        for k, v in filters.iteritems():
            if filter_count > 0:
                query += " AND "
            if isinstance(v, tuple):
                query += k + " in " + str(v) + " COLLATE NOCASE"
            else:
                query += k + " = '" + v + "' COLLATE NOCASE"
            filter_count += 1
    else:
        # No filters or user got here from a link (show linked model as well as CBI models).
        # Filter out IPA models
        query = "SELECT ID, NAME, EXTENT_GCS, SHORT_DESCRIPTION, PROJECT FROM EEMS_ONLINE_MODELS WHERE OWNER = 'CBI' AND PROJECT <> 'IPA' AND STATUS = 1 OR ID = '%s'" % initial_eems_model_id

    cursor = connection.cursor()
    cursor.execute(query)

    initial_eems_model = []

    for row in cursor:
        # Get info required to initialize the starting model (ID, NAME, EXTENT)
        if initial_eems_model_id == "first" and len(initial_eems_model) == 0:
            initial_eems_model = [[str(row[0]), [row[1], row[2]]]]
        elif row[0] == initial_eems_model_id:
            initial_eems_model = [[str(row[0]), [row[1], row[2]]]]
        # GET all EEMS Models (meeting filter criteria) for Dropdown list.
        eems_online_models[str(row[0])] = []
        eems_online_models[str(row[0])].append([row[1], row[2], row[3], row[4]])

    initial_eems_model_json = json.dumps(initial_eems_model)
    eems_online_models_json = json.dumps(eems_online_models)

    context = {
        # 'eems_available_commands_dict': eems_available_commands,
        'initial_eems_model_json': initial_eems_model_json,
        'eems_online_models_json': eems_online_models_json,
        'eems_available_commands_json': eems_available_commands_json,
        'hostname_for_link': hostname_for_link
    }

    return render(request, template, context)


# Custom wrapper for CNPS. Requires Login. See /cnps_login/ in urls.py for custom login template
@login_required(login_url='/w_cnps_login/')
def ipa(request):

    subdomain = "cnps"
    project_filters = ("IPA")

    hostname_for_link = "https://" + subdomain + "." + settings.HOSTNAME_FOR_LINK
    template = "cnps.html"

    # Get a json file of all the EEMS commands
    eems_rqst_dict = {}
    eems_rqst_dict["action"] = 'GetAllCmdInfo'
    my_mpilot_worker = MPilotWorker()
    eems_available_commands_json = my_mpilot_worker.HandleRqst(eems_rqst_dict)
    json.dumps(eems_available_commands_json)

    filters = {}
    filters['project'] = project_filters

    # Determine the initial model to show.
    # Check for a model link e.g. (http://127.0.0.1:8000/?model=bK7AzCZSqBJaKz8ty1nH8AuJhVKXYn0m)
    try:
        link_id = request.session.get('filters')["model"]
        initial_eems_model_id = link_id
        initial_tab = "model"
    except:
        link_id = False
        initial_eems_model_id = filters.pop("model", ['first'])[0]
        initial_tab = "home"

    eems_online_models = {}

    query = "SELECT ID, NAME, EXTENT_GCS, SHORT_DESCRIPTION, PROJECT FROM EEMS_ONLINE_MODELS WHERE OWNER = 'CBI' AND STATUS = 1 AND "
    filter_count = 0
    for k, v in filters.iteritems():
        if filter_count > 0:
            query += " AND "
        if isinstance(v, tuple):
            query += k + " in " + str(v) + " COLLATE NOCASE"
        else:
            query += k + " = '" + v + "' COLLATE NOCASE"
        filter_count += 1
    if link_id:
        query += " OR ID = '%s'" % link_id

    cursor = connection.cursor()
    cursor.execute(query)

    initial_eems_model = []

    for row in cursor:
        # Get info required to initialize the starting model (ID, NAME, EXTENT)
        if initial_eems_model_id == "first" and len(initial_eems_model) == 0:
            initial_eems_model = [[str(row[0]), [row[1], row[2]]]]
        elif row[0] == initial_eems_model_id:
            initial_eems_model = [[str(row[0]), [row[1], row[2]]]]
        # GET all EEMS Models (meeting filter criteria) for Dropdown list.
        eems_online_models[str(row[0])] = []
        eems_online_models[str(row[0])].append([row[1], row[2], row[3], row[4]])

    initial_eems_model_json = json.dumps(initial_eems_model)
    eems_online_models_json=json.dumps(eems_online_models)

    context = {
        'initial_eems_model_json': initial_eems_model_json,
        'initial_tab': initial_tab,
        'eems_online_models_json': eems_online_models_json,
        'eems_available_commands_json': eems_available_commands_json,
        'hostname_for_link': hostname_for_link
    }

    return render(request, template, context)


@csrf_exempt
def get_additional_info(request):

    subdomain = request.get_host().split(".")[0]
    if subdomain == "cnps":
        hostname_for_link = "cnps.eemsonline.org"
    else:
        hostname_for_link = settings.HOSTNAME_FOR_LINK

    eems_model_id = request.POST.get('eems_model_id')

    print eems_model_id

    cursor = connection.cursor()

    query="SELECT NAME, AUTHOR, CREATION_DATE, LONG_DESCRIPTION, PROJECT, ID FROM EEMS_ONLINE_MODELS where ID = '%s'" % (eems_model_id)

    cursor.execute(query)

    for row in cursor:
        name = row[0]
        author = row[1]
        creation_date = row[2]
        long_description = row[3]
        project = row[4]
        id = row[5]

    model_url = hostname_for_link + "?model=" + id

    context = {
        "name": name,
        "author": author,
        "creation_date": creation_date,
        "long_description": long_description,
        "project": project,
        "model_url": model_url,
    }

    return HttpResponse(json.dumps(context))


@csrf_exempt
def run_eems(request):

    eems_model_id = request.POST.get('eems_model_id')
    eems_model_modified_id = request.POST.get('eems_model_modified_id')
    eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
    eems_operator_changes_dict = json.loads(eems_operator_changes_string)
    eems_operator_changes_dict["cmds"].append({"action": "RunProg"})

    #if the user is downloading, don't delete the netCDF file until it's been zipped up.
    download = int(request.POST.get('download'))

    map_quality = request.POST.get('map_quality')
    print map_quality

    print "Original Model ID: " + eems_model_id
    print "Modified Model ID: " + eems_model_modified_id
    print "Changes: " + json.dumps(eems_operator_changes_dict, indent=2)

    task_id = run_eems_celery.delay(eems_model_id, eems_model_modified_id, eems_operator_changes_string, eems_operator_changes_dict, download, map_quality)

    return HttpResponse(task_id)


@csrf_exempt
def check_eems_model_run_status(request):

    task_id = request.POST.get('eems_model_run_task_id')
    state = run_eems_celery.AsyncResult(task_id).state

    print state

    if state == "PENDING":
        return HttpResponse(state)

    else:
        # Get the output from the run_eems_celery task (model run ID and error status).
        results = run_eems_celery.AsyncResult(task_id).get()
        return HttpResponse(results)


@csrf_exempt
def download(request):
    eems_model_modified_id = request.POST.get('eems_model_modified_id')
    print "Preparing file for download: " + eems_model_modified_id
    base_dir = settings.BASE_DIR + "/eems_online_app/static/eems/models"
    dir_name = base_dir + os.sep + eems_model_modified_id
    zip_name = base_dir + os.sep + "zip" + os.sep + "EEMS_Online_Model_Results_" + eems_model_modified_id

    output_netcdf = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/data/results.nc'.format(eems_model_modified_id)

    try:
        shutil.make_archive(zip_name, 'zip', dir_name)
        current_dir = os.getcwd()
        print current_dir
        return_message = "File is ready for download"
    except:
        current_dir = os.getcwd()
        print current_dir
        return_message = "Error. Please try again."

    os.remove(output_netcdf)
    return HttpResponse(return_message)

@csrf_exempt
def link(request):

    eems_model_id = request.POST.get('eems_model_id')
    eems_model_modified_id = request.POST.get('eems_model_modified_id')

    eems_model_modified_src_program = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/model.mpt'.format(eems_model_modified_id)

    # Get a json file of all the EEMS commands
    eems_rqst_dict = {}
    eems_rqst_dict["action"] = 'GetMEEMSETrees'
    my_mpilot_worker = MPilotWorker()
    eems_meemse_tree_json = json.loads(my_mpilot_worker.HandleRqst(rqst=eems_rqst_dict,id=1,srcProgNm=eems_model_modified_src_program,doFileLoad=True, rqstIsJSON=False, reset=True)[1:-1])
    print eems_meemse_tree_json

    eems_meemse_tree_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/tree/meemse_tree.json'.format(eems_model_modified_id)
    with open(eems_meemse_tree_file, 'w') as outfile:
        json.dump(eems_meemse_tree_json, outfile, indent=3)

    cursor = connection.cursor()

    query = "SELECT NAME, EXTENT, EXTENT_GCS, EPSG, PROJECT FROM EEMS_ONLINE_MODELS where id = '%s'" % eems_model_id
    cursor.execute(query)
    for row in cursor:
        eems_model_name = row[0]
        eems_extent = str(row[1])
        eems_extent_gcs = str(row[2])
        epsg = str(row[3])
        project = str(row[4])

    eems_model_name_user = eems_model_name.replace(" (Modified)", "") + " (Modified)"
    user = "USER"
    author = "USER"
    short_description = "User modified version of <a title='click to access the original model' href=?model=" + eems_model_id + ">" + eems_model_name + "</a>."
    long_description = "This model is a user modified version of the original " + eems_model_name + " model, created on " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M") + ". To access the original model, click the link below.<p><a title='click to access the original model' href=?model=" + str(eems_model_id) + ">" + eems_model_name + "</a>"
    todays_date = time.strftime("%d/%m/%Y")

    cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, EXTENT, EXTENT_GCS, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE, EPSG, PROJECT)  values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_modified_id, eems_model_name_user, eems_extent, eems_extent_gcs, user, short_description, long_description, author, todays_date, epsg, project))

    return HttpResponse(eems_model_modified_id)


#@csrf_exempt
#def login(request):
#
#    auth_code = request.GET.get('auth')
#    print auth_code
#
#    context = {
#        "auth_code": auth_code,
#    }

#    template = "login.html"
#    return render(request, template, context)

def logged_out(request):
    return render(request, 'logged_out.html')

#@csrf_exempt
#@login_required
#def upload(request):
#
#        password = settings.UPLOAD_PASS
#        username = settings.UPLOAD_USERNAME
#
#        user_password = request.POST.get('password')
#        user_username = request.POST.get('username')
#
#
#        if user_password == password and user_username == username:
#            query = "SELECT DISTINCT PROJECT FROM EEMS_ONLINE_MODELS"
#
#            cursor = connection.cursor()
#            cursor.execute(query)
#
#            project_list = []
#            for row in cursor:
#                if row[0] != None:
#                    project_list.append(row[0])
#            project_list_json = json.dumps(project_list)
#            print "Password verified"
#            return render(request, "upload.html", {"username":username, "project_list":project_list})
#        else:
#            return redirect(reverse(login)+"?auth=0")


@csrf_exempt
# This is the secret to forcing the user to login to see this view.
@login_required(login_url='/admin/login/')
def upload(request):
        query = "SELECT DISTINCT PROJECT FROM EEMS_ONLINE_MODELS"
        username = request.user.username

        cursor = connection.cursor()
        cursor.execute(query)

        project_list = []
        for row in cursor:
            if row[0] != None:
                project_list.append(row[0])
        project_list_json = json.dumps(project_list)
        print "Password verified"
        return render(request, "upload.html", {"username": username, "project_list":project_list})

class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

@csrf_exempt
@login_required
def upload_files(request):

    # Check to see if this is a SSH upload
    try:
        ssh_dir_name = json.loads(request.body)["ssh_dir_name"]

    except:
        ssh_dir_name = False

    try:
        if ssh_dir_name:
            upload_id = ssh_dir_name
            upload_dir = settings.BASE_DIR + '/eems_online_app/static/eems/uploads/%s' % upload_id
            eems_command_file = glob.glob(upload_dir + "/*.eem")[0]
            eems_command_file_name = os.path.basename(eems_command_file)
            if eems_command_file:
                extension = "." + eems_command_file.split(".")[-1]
                mpt_file = upload_dir + "/" + eems_command_file_name.replace(extension, ".mpt").replace("\\", "/")
                cv = Converter(eems_command_file, mpt_file, None, None, False)
                cv.ConvertScript()

        else:
            user = request.user.username
            upload_id = get_random_string(length=32)
            # Make an upload directory
            upload_dir = settings.BASE_DIR + '/eems_online_app/static/eems/uploads/%s' % upload_id
            os.mkdir(upload_dir)

            # Copy user files to upload directory (data + eems command file)
            if request.method == 'POST':
                form = FileUploadForm(files=request.FILES)
                if form.is_valid():
                    print 'valid form'
                    files = request.FILES.getlist('file')
                    for f in files:
                        file_name = f.name
                        file_copy = upload_dir + "/" + file_name
                        with open(file_copy, 'wb+') as destination:
                            for chunk in f.chunks():
                                destination.write(chunk)
                        #Convert .eem file to .mpt file.
                        if file_name.endswith((".eem", ".eems", ".EEM", ".EEMS")):
                            extension = "." + file_name.split(".")[-1]
                            mpt_file = upload_dir + "/" + file_name.replace(extension, ".mpt").replace("\\", "/")
                            print mpt_file
                            cv = Converter(file_copy, mpt_file, None, None, False)
                            cv.ConvertScript()
                else:
                    print 'invalid form'
                    print form.errors

        # Return directory name
        context = {
            "status": 1,
            "upload_id": upload_id
        }

        return HttpResponse(json.dumps(context))

    except Exception, e:

        upload_datetime = datetime.datetime.now(timezone('US/Pacific')).isoformat()
        error = str(e).replace("\n", "<br />")

        # Don't have additional information at this point. AJAX request sends files, can't get project, model_name, etc.
        # Model Name must be empty string, not NULL, otherwise, server error when clicking model id on the admin page.
        cursor = connection.cursor()
        cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, USER, STATUS, LOG, UPLOAD_DATETIME) values (%s,%s,%s,%s,%s,%s)", (upload_id, "", user, 0, str(e), upload_datetime))

        context = {
            "status": 0,
            "upload_id": upload_id,
            "error_message": error
        }

        return HttpResponse(json.dumps(context))

@csrf_exempt
@login_required
def upload_form(request):

    upload_id = str(request.POST.get('upload_id'))
    owner = "CBI"
    eems_model_name = request.POST.get('model_name')
    author = str(request.POST.get('model_author'))
    creation_date = str(request.POST.get('creation_date'))
    short_description = str(request.POST.get('short_description'))
    long_description = str(request.POST.get('long_description'))
    project = str(request.POST.get('project'))
    username = str(request.POST.get('username'))
    print username
    try:
        resolution = float(request.POST.get('resolution'))
    except:
        resolution = 1000

    upload_form_celery.delay(upload_id, owner, eems_model_name, author, creation_date, short_description, long_description, resolution, project, username)

    return HttpResponse(1)

@csrf_exempt
def check_eems_status(request):

    # Check the status field in the database. Front end will keep trying until the status is 1 (success) or 0 (error).
    upload_id = str(request.POST.get('upload_id'))
    cursor = connection.cursor()
    query = "select STATUS, LOG from EEMS_ONLINE_MODELS where ID = '%s'" % upload_id
    cursor.execute(query)

    try:
        # Can't call cursor.fetchone() twice. Second attempt will always be empty. Call once then parse.
        results = cursor.fetchone()
        status = results[0]
        log = results[1].replace("\n", "<br />").split("Traceback")[0] # Remove the exception before sending to the user.
        print log

    except:
        status = None
        log = None
        print "No database record yet. Front end will check again."

    context = {
            "status": status,
            "upload_id": upload_id,
            "error_message": log
       }

    return HttpResponse(json.dumps(context))

def logout(request):
    logout(request)

@csrf_exempt
def get_raster_data(request):

    wkt = request.POST.get('wkt')
    model_id = str(request.POST.get('model_id'))
    original_model_id = str(request.POST.get('original_model_id'))
    raster = glob.glob(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/data/results.nc' % model_id)[0]

    nc_dataset = netCDF4.Dataset(raster)
    nc_vars = nc_dataset.variables
    nc_var_keys = nc_vars.keys()
    vars_to_remove = ['lat', 'lon', 'x', 'y', 'crs']
    for var_to_remove in vars_to_remove:
        if var_to_remove in nc_var_keys:
            nc_var_keys.remove(var_to_remove)

    cursor = connection.cursor()
    query = "select EPSG from EEMS_ONLINE_MODELS where ID = '%s'" % original_model_id
    cursor.execute(query)
    dst_epsg = int(cursor.fetchone()[0])

    # Project WKT if not in GCS WGS84
    if dst_epsg != 4326:
         # Project WKT using ogr
        geom = ogr.CreateGeometryFromWkt(wkt)
        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)
        target = osr.SpatialReference()
        target.ImportFromEPSG(dst_epsg)
        transform = osr.CoordinateTransformation(source, target)
        geom.Transform(transform)
        wkt = geom.ExportToWkt()

    results = {}

    # Get values out of NetCDF file
    # NetCDF4 version
    try:
        lats = nc_dataset.variables['lat'][:]
        lons = nc_dataset.variables['lon'][:]
    except:
        lats = nc_dataset.variables['y'][:]
        lons = nc_dataset.variables['x'][:]

    lon_target = float(wkt.split("(")[1].split(" ")[0])
    lat_target = float(wkt.split("(")[1].split(" ")[1].replace(")", ""))

    lon_index = numpy.abs(lons - lon_target).argmin()
    lat_index = numpy.abs(lats - lat_target).argmin()

    for var in nc_var_keys:

        # Determine NoData value
        this_nc_var = nc_dataset.variables[var]
        if "_FillValue" in this_nc_var.ncattrs():
            no_data_val = getattr(this_nc_var, "_FillValue")
        elif "no_data_value" in this_nc_var.ncattrs():
            no_data_val = getattr(this_nc_var, "no_data_value")

        var_array = numpy.array(nc_dataset.variables[var])
        value = var_array[lat_index, lon_index]
        print var, value
        if value not in [no_data_val, 9999, -9999]:
            results[var] = round(value, 2)
        else:
            results[var] = "No Data"

     # rasterstats version. Does not work on Webfaction (probably because no GDAL netCDF support)
#    for var in nc_var_keys:
#        raster_with_var = r'file://NETCDF:%s:%s' % (raster, var)
#        with rasterio.open(raster_with_var) as src:
#            transform = src.transform
#            array = src.read(1)
#            value = point_query(wkt, array, affine=transform)[0]
#            results[var] = round(value, 2)

    return HttpResponse(json.dumps(results))

