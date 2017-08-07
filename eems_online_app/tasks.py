from __future__ import absolute_import

from celery import shared_task

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

from EEMSCvt20To30 import *
from Convert_GDB_to_NetCDF import *
from MPilotOnlineWorker import *

import datetime
from pytz import timezone
import traceback

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def upload_form_celery(upload_id, owner, eems_model_name, author, creation_date, short_description, long_description, resolution, project, username):

        # Files have been uploaded. Process user data and form fields. Run EEMS.

        cursor = connection.cursor()
        eems_model_id = upload_id
        upload_datetime = datetime.datetime.now(timezone('US/Pacific')).isoformat()

        def insert_pre_error(error_msg, traceback):
            error = "********************ERROR********************\n\n" + error_msg
            #traceback = traceback.format_exc().splitlines()[-1]
            cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE, PROJECT, USER, STATUS, LOG, UPLOAD_DATETIME) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_id, eems_model_name, owner, short_description, long_description, author, creation_date, project, username, 0, error + "\n\n" + str(traceback), upload_datetime))
            sys.exit(1)

        try:
            image_overlay_size = "24,32"
            upload_dir = settings.BASE_DIR + '/eems_online_app/static/eems/uploads/%s' % upload_id

            print "Upload dir: " + upload_dir

            mpt_file = glob.glob(upload_dir + "/*.mpt")[0]
            mpt_file = mpt_file.replace("\\","/")

        except IndexError:
            error = "There was an error with the eems to mpt file conversion.\n\nPlease make sure to upload a valid eems command file with a .eem extension (for EEMS 2.0 files) or a .mpt extesion (for EEMS 3.0 files)"
            insert_pre_error(error, traceback.format_exc())

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

            print "Converting FGDB feature class to NetCDF"
            rasterize(FGDB_file, netCDF_file, resolution)

        # Else look for NC
        except:

            try:
                netCDF_file = glob.glob(upload_dir + "/*.nc")[0]
                netCDF_file = netCDF_file.replace("\\","/")
                netCDF_file_name = os.path.basename(netCDF_file)

            except:
                error = "There was a problem with the dataset you uploaded.\n\nPlease uploaded a valid zipped folder containing a geodatabase with a single feature class, or a valid NetCDF file."
                #exc_type, exc_value, exc_traceback = sys.exc_info()
                #insert_pre_error(error, exc_traceback.tb_lineno, traceback)
                insert_pre_error(error, traceback.format_exc())


        try:
            input_epsg = getEPSGFromNCfile(netCDF_file)

        except:
            # Assume GCS WGS84 if no crs in the netCDF file.
            input_epsg = 4326

        try:
            # Get the Extent from the NetCDF file (try y,x first)
            extent_input_crs = getExtentFromNCFile(netCDF_file, ['y', 'x'])

        except:

            try:
                extent_input_crs = getExtentFromNCFile(netCDF_file, ['lat', 'lon'])
            except:
                error = "There was a problem extracting the coordinate system information from the dataset you uploaded.\n\nPlease uploaded a NetCDF file with a x,y or lat,lon variables, or a feature class with the coordinate system properly defined."
                insert_pre_error(error, traceback.format_exc())

        try:
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

            output_base_dir = settings.BASE_DIR + '/eems_online_app/static/eems/models/%s/' % eems_model_id

        except:
            error = "There was a problem getting the extent from dataset you uploaded.\n\nPlease make sure the dataset you upload is in a standard coordinate reference system."
            insert_pre_error(error, traceback.format_exc())

        try:

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
            my_mpilot_worker.HandleRqst(rqst={"action": "RunProg"}, id=eems_model_id, srcProgNm=mpt_file_copy, outputBaseDir=output_base_dir, extent=extent_for_gdal, epsg=str(input_epsg), map_quality=image_overlay_size, doFileLoad=True, rqstIsJSON=False, reset=True)

            success_message = "Succeeded at " + upload_datetime

            cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, EPSG, EXTENT, EXTENT_GCS, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE, PROJECT, USER, STATUS, LOG, UPLOAD_DATETIME) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_id, eems_model_name, str(input_epsg), extent_input_crs_insert, extent_gcs_insert, owner, short_description, long_description, author, creation_date, project, username, 1, success_message, upload_datetime))

            # Create the MEEMSE tree
            eems_meemse_tree_json = json.loads(my_mpilot_worker.HandleRqst(id=eems_model_id, srcProgNm=mpt_file_copy,rqst={"action" : "GetMEEMSETrees"}, doFileLoad=True, rqstIsJSON=False, reset=True)[1:-1])
            eems_meemse_tree_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/tree/meemse_tree.json'.format(eems_model_id)
            with open(eems_meemse_tree_file, 'w') as outfile:
                json.dump(eems_meemse_tree_json, outfile, indent=3)

            shutil.rmtree(upload_dir)

            return 1

        except Exception, e:

            # Insert the error into the database.
            cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, EPSG, EXTENT, EXTENT_GCS, OWNER, SHORT_DESCRIPTION, LONG_DESCRIPTION, AUTHOR, CREATION_DATE, PROJECT, USER, STATUS, LOG, UPLOAD_DATETIME) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (eems_model_id, eems_model_name, str(input_epsg), extent_input_crs_insert, extent_gcs_insert, owner, short_description, long_description, author, creation_date, project, username, 0, str(e), upload_datetime))
            #shutil.rmtree(upload_dir)
            shutil.rmtree(output_base_dir)
            print "There was an error running EEMS."
            print e
            return e

