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

from EEMSCvt20To30 import *
from Convert_GDB_to_NetCDF import *
from MPilotOnlineWorker import *

import fileinput

@csrf_exempt
def index(request):

        # Get a json file of all the EEMS commands
        eems_rqst_dict = {}
        eems_rqst_dict["action"] = 'GetAllCmdInfo'
        my_mpilot_worker = MPilotWorker()
        eems_available_commands_json = my_mpilot_worker.HandleRqst("none", "none", eems_rqst_dict, "none", "none", "none", "none", False, False, True)

        json.dumps(eems_available_commands_json)

        # Get initial EEMS model (default to ID=1)
        initial_eems_model_id = request.GET.get('model', 1)

        query = "SELECT ID, NAME, EXTENT_GCS FROM EEMS_ONLINE_MODELS where ID = '%s'" % (initial_eems_model_id)

        cursor = connection.cursor()
        cursor.execute(query)

        initial_eems_model=[]

        for row in cursor:
            initial_eems_model.append([str(row[0]),[row[1], row[2]]])

        initial_eems_model_json = json.dumps(initial_eems_model)

        # GET all available EEMS Models
        eems_online_models = {}
        query = "SELECT ID, NAME, EXTENT_GCS, SHORT_DESCRIPTION FROM EEMS_ONLINE_MODELS where OWNER = 'CBI' or ID = '%s'" % (initial_eems_model_id)
        print query
        cursor.execute(query)
        for row in cursor:
            eems_online_models[str(row[0])]=[]
            eems_online_models[str(row[0])].append([row[1], row[2], row[3]])

        eems_online_models_json=json.dumps(eems_online_models)

        template = 'index.html'
        hostname_for_link = settings.HOSTNAME_FOR_LINK
        context = {
            #'eems_available_commands_dict': eems_available_commands,
            'initial_eems_model_json': initial_eems_model_json,
            'eems_online_models_json': eems_online_models_json,
            'eems_available_commands_json': eems_available_commands_json,
            'hostname_for_link': hostname_for_link
        }

        return render(request, template, context)

@csrf_exempt
def get_additional_info(request):

    eems_model_id = request.POST.get('eems_model_id')

    print eems_model_id

    cursor = connection.cursor()

    query="SELECT NAME, AUTHOR, CREATION_DATE, LONG_DESCRIPTION FROM EEMS_ONLINE_MODELS where ID = '%s'" % (eems_model_id)

    cursor.execute(query)

    for row in cursor:
        name = row[0]
        author = row[1]
        creation_date = row[2]
        long_description = row[3]

    context = {
        "name": name,
        "author": author,
        "creation_date": creation_date,
        "long_description": long_description,
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

    original_mpt_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/model.mpt'.format(eems_model_id)

    # Get the extent of the original EEMS model. Used to project PNG in GDAL.
    cursor = connection.cursor()
    query = "SELECT EXTENT, EPSG FROM EEMS_ONLINE_MODELS where ID = '%s'" % (eems_model_id)
    cursor.execute(query)
    for row in cursor:
            extent = row[0]
            epsg = str(row[1])
    extent_list = extent.replace('[','').replace(']','').split(',')
    extent_for_gdal = extent_list[1] + " " + extent_list[2] + " " + extent_list[3] + " " + extent_list[0]
    print "Extent: " + extent_for_gdal
    print "EPSG: " + epsg

    # If this is the first run, create the user output directories.
    if eems_model_modified_id == '':
        eems_model_modified_id = get_random_string(length=32)

        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s' % eems_model_modified_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/data' % eems_model_modified_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/eemssrc' % eems_model_modified_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/histogram' % eems_model_modified_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/overlay' % eems_model_modified_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/tree' % eems_model_modified_id)

        # Copy the mpt file to the user output directory
        mpt_file_copy = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/model.mpt'.format(eems_model_modified_id)
        shutil.copyfile(original_mpt_file, mpt_file_copy)

    else:
        mpt_file_copy = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/model.mpt'.format(eems_model_modified_id)

    output_base_dir = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/'.format(eems_model_modified_id)
    output_netcdf = output_base_dir + '/data/results.nc'

    print mpt_file_copy
    print eems_operator_changes_dict
    print output_base_dir
    print extent_for_gdal
    print epsg


    # Send model information to MPilot to run EEMS.
    try:
        my_mpilot_worker = MPilotWorker()
        my_mpilot_worker.HandleRqst(eems_model_modified_id, mpt_file_copy, eems_operator_changes_dict, output_base_dir, extent_for_gdal, epsg, map_quality, True, False, True)
        error_code = 0
        error_message = None
        if not download:
            os.remove(output_netcdf)

    except Exception as e:
        error_code = 1
        error_message = str(e)

    context={
        "eems_model_modified_id": eems_model_modified_id,
        "error_code": error_code,
        "error_message": error_message
    }

    return HttpResponse(json.dumps(context))

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
    eems_meemse_tree_json = json.loads(my_mpilot_worker.HandleRqst(1, eems_model_modified_src_program, eems_rqst_dict, "none", "none", "none", "none", True, False, True)[1:-1])
    print eems_meemse_tree_json

    eems_meemse_tree_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/tree/meemse_tree.json'.format(eems_model_modified_id)
    with open(eems_meemse_tree_file, 'w') as outfile:
        json.dump(eems_meemse_tree_json, outfile, indent=3)

    cursor = connection.cursor()

    query = "SELECT NAME, EXTENT, EXTENT_GCS, EPSG FROM EEMS_ONLINE_MODELS where id = '%s'" % eems_model_id
    cursor.execute(query)
    for row in cursor:
        eems_model_name = row[0]
        eems_extent = str(row[1])
        eems_extent_gcs = str(row[2])
        epsg = str(row[3])

    eems_model_name_user = eems_model_name.replace(" (Modified)", "") + " (Modified)"
    user = "USER"
    author = "USER"
    short_description = "User modified version of <a title='click to access the original model' href=?model=" + eems_model_id + ">" + eems_model_name + "</a>."
    long_description = "This model is a user modified version of the original " + eems_model_name + " model, created on " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M") + ". To access the original model, click the link below.<p><a title='click to access the original model' href=?model=" + str(eems_model_id) + ">" + eems_model_name + "</a>"
    todays_date = time.strftime("%d/%m/%Y")

    cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, EXTENT, EXTENT_GCS, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE, EPSG)  values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_modified_id, eems_model_name_user, eems_extent, eems_extent_gcs, user, short_description, long_description, author, todays_date, epsg))

    return HttpResponse(eems_model_modified_id)


@csrf_exempt
def login(request):

    auth_code = request.GET.get('auth')
    print auth_code

    context = {
        "auth_code": auth_code,
    }

    template = "login.html"
    return render(request, template, context)

@csrf_exempt
def upload(request):

        password = settings.UPLOAD_PASS
        username = settings.UPLOAD_USERNAME

        user_password = request.POST.get('password')
        user_username = request.POST.get('username')

        if user_password == password and user_username == username:
            print "Password verified"
            return render(request, "upload.html", {"username":username})
        else:
            return redirect(reverse(login)+"?auth=0")

class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

@csrf_exempt
def upload_files(request):

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
    return HttpResponse(upload_id)

@csrf_exempt
def upload_form(request):

        # Files have been uploaded. Process user data and form fields. Run EEMS.

        image_overlay_size = "24,32"

        upload_id = str(request.POST.get('upload_id'))
        owner = str(request.POST.get('owner'))
        eems_model_name = request.POST.get('model_name')
        author = str(request.POST.get('model_author'))
        creation_date = str(request.POST.get('creation_date'))
        #input_epsg = int(request.POST.get('epsg'))
        short_description = str(request.POST.get('short_description'))
        long_description = str(request.POST.get('long_description'))

        upload_dir = settings.BASE_DIR + '/eems_online_app/static/eems/uploads/%s' % upload_id

        print "Upload dir: " + upload_dir

        mpt_file = glob.glob(upload_dir + "/*.mpt")[0]
        mpt_file = mpt_file.replace("\\","/")

        # Try FGDB first
        try:
            #Unzip zipped GDB
            FGDB_zip = glob.glob(upload_dir + "/*.zip")[0]
            zip_ref = zipfile.ZipFile(FGDB_zip, 'r')
            zip_ref.extractall(upload_dir)
            zip_ref.close()

            FGDB_file = glob.glob(upload_dir + "/*.gdb")[0]
            FGDB_file = FGDB_file.replace("\\","/")

            netCDF_file_name = os.path.basename(FGDB_file).split(".")[0] + ".nc"
            netCDF_file = upload_dir + "/" + netCDF_file_name

            resolution = float(request.POST.get('resolution'))

            print "Converting FGDB feature class to NetCDF"
            rasterize(FGDB_file, netCDF_file, resolution)

        # Else look for NC
        except:
            netCDF_file = glob.glob(upload_dir + "/*.nc")[0]
            netCDF_file = netCDF_file.replace("\\","/")
            netCDF_file_name = os.path.basename(netCDF_file)

        input_epsg  = getEPSGFromNCfile(netCDF_file)

        # Get the Extent from the NetCDF file (try y,x first)
        try:
            extent_input_crs = getExtentFromNCFile(netCDF_file, ['y', 'x'])
        except:
            extent_input_crs = getExtentFromNCFile(netCDF_file, ['lat', 'lon'])

        # Restructure for database insert
        extent_input_crs_insert = str([[extent_input_crs[2],extent_input_crs[0]],[extent_input_crs[3],extent_input_crs[1]]])

        # Restructure for GDAL
        extent_for_gdal = str(extent_input_crs[0]) + " " + str(extent_input_crs[3]) + " " + str(extent_input_crs[1]) + " " + str(extent_input_crs[2])

        # Get Web Mercator Extent from input CRS
        extent_wm = getExtentInDifferentCRS(extent_input_crs,False,False,input_epsg,3857)
        #print "Extent WebMercator: ", extent_wm

        # Get GCS Extent from Web Mercator Extent
        extent_gcs = getExtentInDifferentCRS(extent_wm,False,False,3857,4326)
        extent_gcs_insert = str([[extent_gcs[2],extent_gcs[0]],[extent_gcs[3],extent_gcs[1]]])

        # Create a new record in the datatabase for the new model
        cursor = connection.cursor()
        query = "SELECT MAX(CAST(ID as integer)) from EEMS_ONLINE_MODELS where OWNER = 'CBI'"
        cursor.execute(query)
        max_id = cursor.fetchone()[0]
        eems_model_id =  str(int(max_id) + 1)

        cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, EPSG, EXTENT, EXTENT_GCS, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_id, eems_model_name, str(input_epsg), extent_input_crs_insert, extent_gcs_insert, owner, short_description, long_description, author, creation_date))

        output_base_dir = settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/' % eems_model_id

        # Make new directories
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s' % eems_model_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/data' % eems_model_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/eemssrc' % eems_model_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/histogram' % eems_model_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/overlay' % eems_model_id)
        os.mkdir(settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/tree' % eems_model_id)

        # Copy input files to new directory
        mpt_file_copy = settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/eemssrc/model.mpt' % (eems_model_id)

        shutil.copy(mpt_file, mpt_file_copy)

        netCDF_file_copy = settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/data/%s' % (eems_model_id, netCDF_file_name)
        shutil.copy(netCDF_file, netCDF_file_copy)

        # Open the mpt file and replace the path to the netCDF file.
        with open(mpt_file) as infile, open(mpt_file_copy, 'w') as outfile:
            for line in infile:
                if re.match("(.*)InFileName(.*)", line):
                    line = "    InFileName = " + netCDF_file_copy.replace("\\","/") + ",\n"
                    print line
                outfile.write(line)

        # Run EEMS to create the image overlays and the histograms
        my_mpilot_worker = MPilotWorker()
        my_mpilot_worker.HandleRqst(eems_model_id, mpt_file_copy, {"action": "RunProg"}, output_base_dir, extent_for_gdal, str(input_epsg), image_overlay_size, True, False, True)

        # Create the MEEMSE tree
        eems_meemse_tree_json = json.loads(my_mpilot_worker.HandleRqst(eems_model_id, mpt_file_copy,{"action" : "GetMEEMSETrees"} , "none", "none", "none", "none", True, False, True)[1:-1])
        eems_meemse_tree_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/tree/meemse_tree.json'.format(eems_model_id)
        with open(eems_meemse_tree_file, 'w') as outfile:
            json.dump(eems_meemse_tree_json, outfile, indent=3)

        shutil.rmtree(upload_dir)

        return HttpResponse("Model uploaded successfully")
