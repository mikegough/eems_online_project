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

import ogr
import osr
import numpy as np
import netCDF4

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

#  For 2.0 -> 3.0 converter
import MPilotProgram as mpprog
import MPilotFramework as mpf
import MPilotParse as mpp
from collections import OrderedDict
import os
import re
import copy as cp

from MPilotOnlineWorker import *

try:
   import cPickle as pickle
except:
   import pickle

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
        print query;
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
    query="SELECT EXTENT, EPSG FROM EEMS_ONLINE_MODELS where ID = '%s'" % (eems_model_id)
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
        shutil.copyfile(original_mpt_file,mpt_file_copy)

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
        "error_code": error_code ,
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
        "auth_code" : auth_code,
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
                if ".eem" in file_name:
                    mpt_file = upload_dir + "/" + file_name.replace(".eem", ".mpt").replace("\\","/")
                    print mpt_file
                    cv = Converter(file_copy,mpt_file,None,None,False)
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

        return HttpResponse("Model uploaded successsfully")

def getEPSGFromNCfile(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as nc:
        wkt = nc.variables['crs'].getncattr('crs_wkt')
        srs = osr.SpatialReference()
        srs.ImportFromWkt(wkt)
        epsg = srs.GetAttrValue("AUTHORITY", 1)
        return int(epsg)

def getWktFromNCFile(ncfile):
  with netCDF4.Dataset(ncfile, 'r') as nc:
    return nc.variables['crs'].getncattr('crs_wkt')

def getExtentFromNCFile(ncfile, coords=['lat','lon']):
  with netCDF4.Dataset(ncfile, 'r') as nc:
    # had to rearange order. NetCDF Flipped?
    y_min = np.amin(nc.variables[coords[0]])
    y_max = np.amax(nc.variables[coords[0]])
    x_min = np.amin(nc.variables[coords[1]])
    x_max = np.amax(nc.variables[coords[1]])
    return [x_min, x_max, y_min, y_max]

def getExtentInDifferentCRS(extent=False, wkt=False, proj4=False, epsg=False, to_epsg=False):
  s_srs = osr.SpatialReference()
  if wkt:
    s_srs.ImportFromWkt(wkt)
  elif proj4:
    s_srs.ImportFromProj4(proj4)
  elif epsg:
    s_srs.ImportFromEPSG(epsg)
  else: # no reprojection to do
    return extent
  t_srs = osr.SpatialReference()
  t_srs.ImportFromEPSG(to_epsg) # we want lat-lon
  transform = osr.CoordinateTransformation(s_srs, t_srs)
  ring = ogr.Geometry(ogr.wkbLinearRing)
  for x in range(2):
    for y in range(2):
      ring.AddPoint(extent[x], extent[2+y])
  poly = ogr.Geometry(ogr.wkbPolygon)
  poly.AddGeometry(ring)
  poly.Transform(transform)
  return(poly.GetEnvelope())

def rasterize(infile, outfile, pixel_size):

  fill = -9999. # nodata value
  # We assume a single layer, and that all features have the same fields.
  # So we use feature 0 as a pattern for the fields to transcribe.

  # Fields we don't want to turn into netcdf variables:
  exclude = ['Shape_Length', 'Shape_Area']

  # Need to map gdal types to numpy types, but not sure how to
  # use the library commands to do this. Right now, all I have is reals:
  npTypes = {2: np.float32, 0:np.int, 4:np.int}
  ps = pixel_size # shorthand

  c = ogr.Open(infile)
  src = c.GetLayer(0)
  x_min, x_max, y_min, y_max = src.GetExtent()
  rows = int((y_max - y_min) / ps)
  cols = int((x_max - x_min) / ps)

  # create an in-memory workspace
  # might need to do this per-field if we have other data types
  buf = gdal.GetDriverByName('MEM').Create('', cols, rows, 1, gdal.GDT_Float32)
  wkt = src.GetSpatialRef().ExportToWkt()
  buf.SetProjection(wkt)
  # Going north-to-south
  # buf.SetGeoTransform((x_min, ps, 0, y_min, 0, ps))
  buf.SetGeoTransform((x_min, ps, 0, y_max, 0, -ps))
  band = buf.GetRasterBand(1)
  band.SetNoDataValue(fill)

  # make netcdf vars for each field
  featureDefn = src.GetLayerDefn()
  with netCDF4.Dataset(outfile, 'w') as nc:
    nc.createDimension('y', rows)
    nc.createDimension('x', cols)
    nc.createVariable('y', np.double, ['y'])
    nc.createVariable('x', np.double, ['x'])
    # For CF-compliant projection info
    nc.createVariable('crs', np.int32, [])
    nc.variables['crs'].setncattr('crs_wkt', wkt)

    for fieldIndex in range(featureDefn.GetFieldCount()):
      fieldDefn = featureDefn.GetFieldDefn(fieldIndex)
      fieldName = fieldDefn.GetNameRef()
      if fieldName in exclude:
        continue
      type = fieldDefn.GetType()
      npType = npTypes[type]
      nc.createVariable(fieldName, npType, ['y', 'x'], fill_value=fill)

    # Now we've created all the vars, we write them. If we did this
    # in the above loop, we'd switch the netCDF driver between define
    # and write modes, which takes a lot of time
    # Going north-to-south
    # nc.variables['y'][:] = [(y_min + ps/2.) + ps * i for i in range(rows)]
    nc.variables['y'][:] = [(y_max - ps/2.) - ps * i for i in range(rows)]
    nc.variables['x'][:] = [(x_min + ps/2.) + ps * i for i in range(cols)]
    for fieldIndex in range(featureDefn.GetFieldCount()):
      fieldName = featureDefn.GetFieldDefn(fieldIndex).GetNameRef()
      if fieldName in exclude:
        continue
      band.Fill(fill) # Don't know whether this is necessary
      err = gdal.RasterizeLayer(buf, [1], src,
        options=["ATTRIBUTE=%s" % fieldName])
      nc.variables[fieldName][:] = band.ReadAsArray()

@csrf_exempt
def load_eems_user_model(request):

    # Reference only. Not being used.

    #  For user uploaded EEMS file

    #  User passes back a serialized EEMS command file.
    eems_model_id = get_random_string(length=32)
    eems_model_name = request.POST.get('eems_filename').split('.')[0]
    eems_file_contents = request.POST.get('eems_file_contents')

    # Pickle the EEMS file contents. Return the pickled representation of the object as a bytes object
    pdata = pickle.dumps(eems_file_contents, pickle.HIGHEST_PROTOCOL)

    # Connect to the database
    cursor = connection.cursor()

    # Load EEMS data into database (model as binary)
    cursor.execute("insert into EEMS_USER_MODELS (ID, NAME, MODEL) values (%s,%s,%s)", (eems_model_id, eems_model_name, sqlite3.Binary(pdata)))

    # Retreive EEMS data from Database
    query="SELECT MODEL FROM EEMS_USER_MODELS where ID = '%s'" % (eems_model_id)

    cursor.execute(query)
    for row in cursor:
        eems_model_contents = pickle.loads(str(row[0]))
    print (eems_model_contents)

    # ToDO: Convert EEMS file to JSON

    # ToDO: Get list of available EEMS commands from MPilot EEMS

    # ToDO: Create New PNG files from EEMS output

    # ToDo: Get List of available actions from EEMS

    context = {
        "eems_model_id" : eems_model_id,
    }

    return HttpResponse(json.dumps(context))


class Converter(object):

    def __init__(
        self,
        inFNm,                 # input script filepath
        outFNm,                # output script filepath
        newInDataFNm=None,     # script's input file data path; None == no change
        newOutDataFNm=None,    # script's output file data path; None == no change
        writeDataOutput=True,   # suppresses script writing results to file
        deleteVars=['CSVID'],  # empty for no deletes
        ):

        if inFNm == outFNm:
          raise Exception('Input and output file names must be different')

        # Initialize variables
        self.inFNm = inFNm
        self.outFNm = outFNm
        self.newInDataFNm = newInDataFNm
        self.newOutDataFNm = newOutDataFNm
        self.writeDataOutput = writeDataOutput
        self.deleteVars = deleteVars

        self.outScript = None

        with open(inFNm,'r') as inF: self.inScript = inF.read()

        # Quick check to see if handling an EEMS 2 or an EEMS 3 script
        if self._Validate20Input():
            self.scriptType = 2
        else:
            self.scriptType = 3

        self.cmds20 = None

        self.mpFw = mpf.MPilotFramework([
                'MPilotEEMSBasicLib',
                'MPilotEEMSFuzzyLogicLib',
                'MPilotEEMSNC4IO',
                ])

        # Global lookup table for command substitution

        self.cmdLU = {
            'READ':{'newNm':'EEMSRead','warning':None},
            'READMULTI':{'newNm':'','warning':'Converting to Reads'},
            'CVTTOFUZZY':{'newNm':'CvtToFuzzy','warning':None},
            'CVTTOFUZZYCURVE':{'newNm':'CvtToFuzzyCurve','warning':None},
            'CVTTOFUZZYCAT':{'newNm':'CvtToFuzzyCat','warning':None},
            'MEANTOMID':{'newNm':'MeanToMid','warning':None},
            'COPYFIELD':{'newNm':'Copy','warning':None},
            'NOT':{'newNm':'FuzzyNot','warning':None},
            'OR':{'newNm':'FuzzyOr','warning':None},
            'AND':{'newNm':'FuzzyAnd','warning':None},
            'EMDSAND':{'newNm':None,'warning':'Not supported in EEMS 3.0'},
            'ORNEG':{'newNm':'FuzzyAnd','warning':None},
            'XOR':{'newNm':'FuzzyXOr','warning':None},
            'SUM':{'newNm':'Sum','warning':None},
            'MULT':{'newNm':'Multiply','warning':None},
            'DIVIDE':{'newNm':'ADividedByB','warning':None},
            'MIN':{'newNm':'Minimum','warning':None},
            'MAX':{'newNm':'Maximum','warning':None},
            'MEAN':{'newNm':'Mean','warning':None},
            'UNION':{'newNm':'FuzzyUnion','warning':None},
            'DIF':{'newNm':'AMinusB','warning':None},
            'SELECTEDUNION':{'newNm':'FuzzySelectedUnion','warning':None},
            'WTDUNION':{'newNm':'FuzzyWeightedUnion','warning':None},
            'WTDEMDSAND':{'newNm':'','warning':None},
            'WTDMEAN':{'newNm':'WeightedMean','warning':None},
            'WTDSUM':{'newNm':'WeightedSum','warning':None},
            # 'CALLEXTERN':{'newNm':'','warning':None},
            'SCORERANGEBENEFIT':{'newNm':'ScoreRangeBenefit','warning':None},
            'SCORERANGECOST':{'newNm':'ScoreRangeCost','warning':None},
            }

        # Used to determine of any directly read variable is fuzzy
        self.fuzzy30Ops = [
            'FuzzyNot',
            'FuzzyOr',
            'FuzzyAnd',
            'FuzzyXOr',
            'FuzzyUnion',
            'FuzzySelectedUnion',
            'FuzzyWeightedUnion',
            ]

    # def __init__(...)

    def _Validate20Input(self):

        # Only validates that the would-be 2.0 files has
        # either a valid READ or a READMULTI command

        is20 = False

        if re.search(r'^READ\(',self.inScript) or \
          re.search(r'^READMULTI\(',self.inScript) or \
          re.search(r'\nREAD\(',self.inScript) or \
          re.search(r'\nREADMULTI\(',self.inScript):

          return True

        else:

          return False

        # if re.search(r'^READ\(',script) or ... else

    # def _Validate20Input(self,inFNm):

    def _Parse20CmdToParams(self,mptCmdStruct):

        # mptCmdStruct is a dict:
        # 'lineNo': the command's line within the input file
        # 'rawCmdStr': the command string as it appeared in the input
        #    file, comments, line breaks, and all
        # 'cleanCmdStr': the command string stripped of all its
        #    comments, line breaks, and all

        # strip white space
        cmdStr = re.sub('\s+','',mptCmdStruct['cleanCmdStr'])

        # parse the command string into result, command name, and parameters
        exprParse = re.match(r'\s*([^\s]+.*=){0,1}\s*([^\s]+.*)\s*\(\s*(.*)\s*\)',cmdStr)

        if not exprParse or len(exprParse.groups()) != 3:
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid command format.\n',
                    'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                    'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr'])),
                    )

        parsedCmd = OrderedDict()

        # Every command must have a result
        if exprParse.groups()[0] is None:
            parsedCmd['rsltNm'] = 'NeedsName'
        else:
            parsedCmd['rsltNm'] = re.sub(r'\s*=\s*','',exprParse.groups()[0].strip())

        if (not re.match(r'^[a-zA-Z0-9\-\_]+$',parsedCmd['rsltNm']) and
            not re.match(r'^\[[a-zA-Z0-9\-\_,]+\]$',parsedCmd['rsltNm'])
            ):
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid result name in command.\n',
                    'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                    'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr'])),
                )

        parsedCmd['cmd'] = exprParse.groups()[1].strip()

        # Parse out the parameters
        paramStr = exprParse.groups()[2]
        paramPairs = []
        while paramStr != '':
            paramPairMatchObj = re.match(r'\s*([^=]*=\s*\[[^\[]*\])\s*,*\s*(.*)',paramStr)
            if paramPairMatchObj:
                paramPairs.append(paramPairMatchObj.groups()[0])
                paramStr = paramPairMatchObj.groups()[1]
            else:
                paramPairMatchObj = re.match(r'\s*([^=,]*=\s*[^,]*)\s*,*\s*(.*)',paramStr)
                if paramPairMatchObj:
                    paramPairs.append(paramPairMatchObj.groups()[0])
                    paramStr = paramPairMatchObj.groups()[1]
                else:
                    raise Exception(
                        '{}{}{}{}{}'.format(
                            '\n********************ERROR********************\n',
                            'Invalid parameter specification.\n',
                            'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                            'Section of command: {}\n'.format(paramStr),
                            'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr']),
                            )
                        )

            # if paramPair:...else:

        # while paramStr != '':

        parsedCmd['params'] = OrderedDict()
        for paramPair in paramPairs:

            paramTokens = re.split(r'\s*=\s*',paramPair)

            paramTokens[0] = paramTokens[0].strip()
            paramTokens[1] = paramTokens[1].strip()

            paramTokens[1] = re.sub(r'\s*\[\s*','[',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*\]\s*',']',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*,\s*',',',paramTokens[1])

            if (len(paramTokens) != 2
                or paramTokens[0] == ''
                or paramTokens[1] == ''
                or paramTokens[0] in parsedCmd
                ):

                raise Exception(
                    '{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Invalid parameter specification. Line number {}\n'.format(mptCmdStruct['lineNo']),
                        'Parameter specification: {}\n'.format(paramPair),
                        'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr']),
                        )
                    )

            parsedCmd['params'][paramTokens[0]] = paramTokens[1]

        return parsedCmd

    # def _Parse20CmdToParams(self,mptCmdStruct):

    def _Parse20FileToCmds(self):

        cmds20 = []
        mptCmdStructstartLineNo = 0

        cmdLine = ''      # buffer to build command from lines of input file
        inParens = False  # whether or not parsing is within parentheses
        parenCnt = 0      # count of parenthesis levels
        inLineCnt = 0     # line number of input file for error messages.

        rawCmd = ''
        cleanCmd = ''

        # Parse the file into commands

        with open(self.inFNm,'rU') as inF:
            for inLine in inF:

                inLineCnt +=1

                cleanLine = re.sub('#.*$','',inLine)
                cleanLine = re.sub('\s+','',cleanLine)

                # Only start gathering a command where
                # a command starts
                if rawCmd == '':
                    if cleanLine == '':
                        continue
                    else:
                        mptCmdStructstartLineNum = inLineCnt

                rawCmd += inLine

                for charNdx in range(len(cleanLine)):
                    cleanCmd += cleanLine[charNdx]
                    if cleanLine[charNdx] == '(':
                        inParens = True
                        parenCnt += 1
                    elif cleanLine[charNdx] == ')':
                        parenCnt -= 1

                    if parenCnt < 0:
                        raise Exception(
                            '{}{}{}{}'.format(
                                '\n********************ERROR********************\n',
                                'Unmatched right paren *)*\n',
                                '  input: {}, line {}:\n'.format(self.inFNm,inLineCnt),
                                '  {}\n'.format(inLine),
                                )
                            )
                    if inParens and parenCnt == 0:
                        if charNdx < (len(cleanLine)-1):
                            raise Exception(
                                '{}{}{}{}'.format(
                                    '\n********************ERROR********************\n',
                                    'Extraneous characters beyond end of command\n',
                                    '  Input: {}, line {}:\n'.format(self.inFNm,inLineCnt),
                                    '  {}\n'.format(inLine),
                                    )
                                )

                        else:

                            mptCmdStructTmp = ({
                                'cmdFileNm':self.inFNm,
                                'lineNo':mptCmdStructstartLineNum,
                                'rawCmdStr':rawCmd,
                                'cleanCmdStr':cleanCmd,
                                })

                            # self._Parse20CmdToParams(mptCmdStructTmp)
                            cmds20.append(cp.deepcopy(self._Parse20CmdToParams(mptCmdStructTmp)))

                            rawCmd = ''
                            cleanCmd = ''
                            inParens = False
                            parenCnt = 0

                # for charNdx in range(len(cleanLine)):
            # for line in inF:
        # with open(self.inFNm,'rU') as inF:

        if cleanCmd != '':
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Incomplete command in file\n',
                    '  input: {}, line {}:\n'.format(self.inFNm,mptCmdStructstartLineNum),
                    '  {}\n'.format(rawCmd),
                    )
                )

        # Replace READMULTI first, adding to commands

        for cmd in cmds20:

            if cmd['cmd'] == 'READMULTI':

                inFldNms = cmd['params']['InFieldNames'].replace('[','').replace(']','').split(',')
                for inFldNm in cmd['params']['InFieldNames']:
                    newCmd = cp.deepcopy(cmd)
                    newCmd['cmd'] = 'READ'
                    del(newCmd['params']['InFieldNames'])
                    newCmd['params']['InFieldName'] = inFldNm
                    cmds20.append(newCmd)

            # if cmd['cmd'] == 'READMULTI':
        # for cmd in cmds20:

        # This gives us a list of valid 2.0 commands for conversion
        self.cmds20 = cmds20

    # def _Parse20FileToCmds(self):

    def _Turn20CmdsInto30(self):

        # This will make destructive changes to the 2.0 commands

        # Then fix the result name for read
        # Snag a filename and fieldname for the output

        if self.newInDataFNm is not None:
            DimensionFileName = self.newInDataFNm
        else:
            DimensionFileName = None

        DimensionFieldName = None

        for cmd in self.cmds20:

            if cmd['cmd'] == 'READ':
                if 'NewFieldName' in cmd['params']:
                    cmd['rsltNm'] =  cmd['params']['NewFieldName']
                    del(cmd['params']['NewFieldName'])
                else:
                    cmd['rsltNm'] =  cmd['params']['InFieldName']

                if DimensionFileName is None:
                    DimensionFileName = cmd['params']['InFileName']
                if DimensionFieldName is None:
                    DimensionFieldName = cmd['params']['InFieldName']

            # if cmd['cmd'] == 'READ':
        # for cmd in cmds20:

        # Convert to dictionary, easier to fix all that needs fixing
        self.cmds20 = OrderedDict(zip([cmd['rsltNm'] for cmd in self.cmds20],self.cmds20))

        # Delete unwanted commands
        for rsltNm in self.cmds20.keys():
            if rsltNm in self.deleteVars:
                del(self.cmds20[rsltNm])


        # If result is to be output, remove it from the 2.0 command and add it to outputs
        outputFNmsAndVars = {} # will have filename and list

        for cmdNdx,cmd in self.cmds20.items():

            if 'params' in cmd:
                if 'OutFileName' in cmd['params']:
                    if cmd['params']['OutFileName'] not in outputFNmsAndVars:
                        outputFNmsAndVars[cmd['params']['OutFileName']] = [cmd['rsltNm']]
                    else:
                        outputFNmsAndVars[cmd['params']['OutFileName']].append(cmd['rsltNm'])
                    del cmd['params']['OutFileName']

            if cmd['cmd'] in self.cmdLU:
                if self.cmdLU[cmd['cmd']] is None:
                    raise Exception(
                        '{}{}{}'.format(
                            '\n********************ERROR********************\n',
                            'EEMS 2.0 command: {}'.format(cmd['cmd']),
                            self.cmdLU['cmd']['warning']
                            )
                    )
                else:
                    cmd['cmd'] = self.cmdLU[cmd['cmd']]['newNm']

        # for cmdNdx,cmd in self.cmds20.items():

        # Now create the output commands


        if self.writeDataOutput:
            outCnt = 0

            if self.newOutDataFNm is None:

                for fNm,vNms in outputFNmsAndVars.items():
                    newCmd = OrderedDict()
                    newCmd['rsltNm'] = 'output{}'.format(outCnt)
                    outCnt = outCnt + 1
                    newCmd['cmd'] = 'EEMSWrite'
                    newCmd['params'] = OrderedDict()
                    newCmd['params']['DimensionFileName'] = DimensionFileName
                    newCmd['params']['DimensionFieldName'] = DimensionFieldName
                    newCmd['params']['OutFileName'] = self.outFNm
                    newCmd['params']['OutFieldNames'] = '[{}]'.format(','.join(outputFNmsAndVars[fNm]))
                    self.cmds20[(newCmd['rsltNm'])] = newCmd
                # for fNm,vNms in outputFNmsAndVars:

            else:

                allVNms = []
                for fNm,vNms in outputFNmsAndVars.items():
                    allVNms = allVNms + vNms

                newCmd = OrderedDict()
                newCmd['rsltNm'] = 'output{}'.format(outCnt)
                outCnt = outCnt + 1
                newCmd['cmd'] = 'EEMSWrite'
                newCmd['params'] = OrderedDict()
                newCmd['params']['DimensionFileName'] = DimensionFileName
                newCmd['params']['DimensionFieldName'] = DimensionFieldName
                newCmd['params']['OutFileName'] = self.newOutDataFNm
                newCmd['params']['OutFieldNames'] = '[{}]'.format(','.join(allVNms))
                self.cmds20[(newCmd['rsltNm'])] = newCmd

            # if self.newOutDataFNm is None:

        # This makes sure that fuzzy values read in directly are tagged as fuzzy
        for cmd,cmdData in self.cmds20.items():

            if cmdData['cmd'] in self.fuzzy30Ops:

                tmpInFieldNames = []

                if 'InFieldName' in cmdData['params']:
                    tmpInFieldNames.append(cmdData['params']['InFieldName'])
                if 'InFieldNames' in cmdData['params']:
                    tmpInFieldNames = tmpInFieldNames + \
                      re.sub(r"\]","",re.sub(r"\[","",cmdData['params']['InFieldNames'])).split(',')

                # We have the names, now if they were initialized with READ,
                # we need to tag them as fuzzy.
                for inFldNm in tmpInFieldNames:
                    if self.cmds20[inFldNm]['cmd'] == 'EEMSRead':
                        self.cmds20[inFldNm]['params']['DataType'] = 'Fuzzy'


    # def _Prep20CmdsFor30(self)

    def _Convert20To30(self):

        self._Parse20FileToCmds()
        self._Turn20CmdsInto30()

        # Turn commands in to string
        self.outScript = ''
        for ndx,cmd in self.cmds20.items():

            params = []
            for paramNm,paramVal in cmd['params'].items():
                if self.newInDataFNm is not None and paramNm == 'InFileName':
                    params.append('{} = {}'.format(paramNm, self.newInDataFNm))
                else:
                    params.append('{} = {}'.format(paramNm, paramVal))

            self.outScript = '{}{} = {}(\n  {}\n  )\n'.format(
                self.outScript,
                cmd['rsltNm'],
                cmd['cmd'],
                ',\n  '.join(params)
                )

    # def _Convert20To30(self):

    def _DoSubsFor30(self):

        # Get parsed program
        self.cmds30 = mpp.ParseStringToCommands(self.inScript)

        # Remove unwanted variables
        for rsltNm in self.cmds30.keys():
            if rsltNm in self.deleteVars:
                del(self.cmds30[rsltNm])

        # Suppress or subsitute output path
        if not self.writeDataOutput:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSWrite':
                    del(self.cmds30['rsltNm'])
        elif self.newOutDataFNm is not None:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSWrite':
                    data['parsedCmd']['params']['OutFileName'] = self.newInDataFNm

        # Substitute input path
        if self.newInDataFNm is not None:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSRead':
                    data['parsedCmd']['params']['InFileName'] = self.newInDataFNm

        self.outScript = ''
        for rsltNm,data in self.cmds30.items():
            self.outScript = '{}{}\n'.format(
                self.outScript,
                self.mpFw.CreateFxnObject(data['parsedCmd']['cmd'],data).FormattedCmd()
                )

    # def _DoSubsFor30(self):

    def _VerifyAndWriteOutScript(self):

        with mpprog.MPilotProgram(
            mpf.MPilotFramework([
                'MPilotEEMSBasicLib',
                'MPilotEEMSFuzzyLogicLib',
                'MPilotEEMSNC4IO',
                ]),
            sourceProgStr = self.outScript
            ) as prog:

            pass

        with open(self.outFNm,'w') as outF:
            outF.write(self.outScript)

    # def _VerifyAndWriteOutScript(self):

    def ConvertScript(self):

        if self.scriptType == 2:
            self._Convert20To30()
        elif self.scriptType == 3:
            self._DoSubsFor30()
        else:
            raise Exception('Unknown script type: {}'.format(self.scriptType))

        self._VerifyAndWriteOutScript()

    # def ConvertFile(self):

# class Converter(object):

################################################################################
