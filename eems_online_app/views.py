from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import os
import shutil
import gdal

from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import sys
import subprocess
import bitarray
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

from MPilotOnlineWorker import *

try:
   import cPickle as pickle
except:
   import pickle

@csrf_exempt
def index(request):

        # Get a json file of all the EEMS commands
        eems_rqst_dict = {}
        eems_rqst_dict["action"] = 'GetAllCmdInfo'
        my_mpilot_worker = MPilotWorker()
        eems_available_commands_json = my_mpilot_worker.HandleRqst("none", "none", eems_rqst_dict, "none", "none", False, False, True)

        json.dumps(eems_available_commands_json)

        # Get initial EEMS model (default to ID=1)
        initial_eems_model_id = request.GET.get('model', 1)

        query = "SELECT ID, NAME, JSON_FILE_NAME, EXTENT FROM EEMS_ONLINE_MODELS where ID = '%s'" % (initial_eems_model_id)

        cursor = connection.cursor()
        cursor.execute(query)

        initial_eems_model=[]

        for row in cursor:
            initial_eems_model.append([str(row[0]),[row[1], row[2], row[3]]])

        initial_eems_model_json = json.dumps(initial_eems_model)

        # GET all available EEMS Models
        eems_online_models = {}
        query = "SELECT ID, NAME, JSON_FILE_NAME, EXTENT FROM EEMS_ONLINE_MODELS where OWNER = 'CBI' or ID = '%s'" % (initial_eems_model_id)
        print query;
        cursor.execute(query)
        for row in cursor:
            eems_online_models[str(row[0])]=[]
            eems_online_models[str(row[0])].append([row[1], row[2], row[3]])

        eems_online_models_json=json.dumps(eems_online_models)

        template = 'index.html'
        context = {
            #'eems_available_commands_dict': eems_available_commands,
            'initial_eems_model_json': initial_eems_model_json,
            'eems_online_models_json': eems_online_models_json,
            'eems_available_commands_json': eems_available_commands_json,
        }

        return render(request, template, context)

@csrf_exempt
def run_eems(request):

    eems_model_id = request.POST.get('eems_model_id')
    eems_model_modified_id = request.POST.get('eems_model_modified_id')
    eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
    eems_operator_changes_dict = json.loads(eems_operator_changes_string)
    eems_operator_changes_dict["cmds"].append({"action": "RunProg"})

    print "Original Model ID: " + eems_model_id
    print "Modified Model ID: " + eems_model_modified_id
    print "Changes: " + json.dumps(eems_operator_changes_dict, indent=2)

    original_mpt_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/Model.mpt'.format(eems_model_id)

    # Get the extent of the original EEMS model. Used to project PNG in GDAL.
    cursor = connection.cursor()
    query="SELECT EXTENT FROM EEMS_ONLINE_MODELS where ID = '%s'" % (eems_model_id)
    cursor.execute(query)
    extent = cursor.fetchone()[0]
    extent_list = extent.replace('[','').replace(']','').split(' ')
    extent_for_gdal = extent_list[1] + " " + extent_list[2] + " " + extent_list[3] + " " + extent_list[0]
    print extent_for_gdal

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
        #mpt_file_copy = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/Model.mpt'.format(eems_model_modified_id)
        #shutil.copyfile(original_mpt_file,mpt_file_copy)

    output_base_dir = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/'.format(eems_model_modified_id)

    # Send model information to MPilot to run EEMS.
    my_mpilot_worker = MPilotWorker()
    my_mpilot_worker.HandleRqst(eems_model_modified_id, original_mpt_file, eems_operator_changes_dict, output_base_dir, extent_for_gdal, True, False, True)

    return HttpResponse(eems_model_modified_id)

@csrf_exempt
def download(request):
    eems_model_modified_id = request.POST.get('eems_model_modified_id')
    print "Preparing file for download: " + eems_model_modified_id
    base_dir = settings.BASE_DIR + "/eems_online_app/static/eems/models"
    dir_name = base_dir + os.sep + eems_model_modified_id
    zip_name = base_dir + os.sep + "zip" + os.sep + "EEMS_Online_Model_Results_" + eems_model_modified_id
    shutil.make_archive(zip_name, 'zip', dir_name)

    return HttpResponse("File is ready for download")

@csrf_exempt
def link(request):
    eems_model_id = request.POST.get('eems_model_id')
    eems_model_modified_id = request.POST.get('eems_model_modified_id')

    eems_model_modified_src_program = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/Model.mpt'.format(eems_model_modified_id)

    # Get a json file of all the EEMS commands
    eems_rqst_dict = {}
    eems_rqst_dict["action"] = 'GetMEEMSETrees'
    my_mpilot_worker = MPilotWorker()
    eems_meemse_tree_json = json.loads(my_mpilot_worker.HandleRqst(1, eems_model_modified_src_program, eems_rqst_dict, "none", "none", True, False, True)[1:-1])
    print eems_meemse_tree_json

    eems_meemse_tree_file = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/tree/meemse_tree.json'.format(eems_model_modified_id)
    with open(eems_meemse_tree_file, 'w') as outfile:
        json.dump(eems_meemse_tree_json, outfile)

    cursor = connection.cursor()

    query = "SELECT NAME, MODEL, JSON_FILE_NAME, EXTENT FROM EEMS_ONLINE_MODELS where id = '%s'" % eems_model_id
    cursor.execute(query)
    for row in cursor:
        eems_model_name = row[0]
        eems_model = row[1]
        eems_json_file_name = row[2]
        eems_extent = str(row[3])

    eems_model_name_user = eems_model_name.replace(" (Modified)", "") + " (Modified)"

    cursor.execute("insert into EEMS_ONLINE_MODELS (ID, NAME, MODEL, JSON_FILE_NAME, EXTENT, OWNER) values (%s,%s,%s,%s,%s,%s)", (eems_model_modified_id, eems_model_name_user, eems_model, eems_json_file_name, eems_extent, "USER"))

    return HttpResponse("Link is ready")


@csrf_exempt
def load_eems_user_model(request):

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

