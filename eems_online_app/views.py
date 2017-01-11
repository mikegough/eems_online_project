from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

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



from MPilotOnlineWorker import *

try:
   import cPickle as pickle
except:
   import pickle

@csrf_exempt
def index(request):

        # Get initial EEMS model (default to ID=1)
        initial_eems_model = request.GET.get('model', 1)

        query="SELECT ID, NAME, JSON_FILE_NAME, EXTENT FROM EEMS_ONLINE_MODELS where ID = '%s'" % (initial_eems_model)

        cursor = connection.cursor()
        cursor.execute(query)

        initial_eems_model=[]

        for row in cursor:
            initial_eems_model.append([str(row[0]),[row[1], row[2], row[3]]])

        initial_eems_model_json = json.dumps(initial_eems_model)

        # GET all available EEMS Models
        eems_online_models={}
        query="SELECT ID, NAME, JSON_FILE_NAME, EXTENT FROM EEMS_ONLINE_MODELS"
        cursor.execute(query)
        for row in cursor:
            eems_online_models[str(row[0])]=[]
            eems_online_models[str(row[0])].append([row[1], row[2], row[3]])

        eems_online_models_json=json.dumps(eems_online_models)

        # ToDo: Get EEMS Commands from eems

        template = 'index.html'
        context = {
            #'eems_available_commands_dict': eems_available_commands,
            'initial_eems_model_json': initial_eems_model_json,
            'eems_online_models_json': eems_online_models_json,
        }

        return render(request, template, context)

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

@csrf_exempt
def run_eems(request):

    eems_model_id = request.POST.get('eems_model_id')
    eems_model_modified_id = request.POST.get('eems_model_modified_id')
    eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
    eems_operator_changes_dict = json.loads(eems_operator_changes_string)

    print json.dumps(eems_operator_changes_dict,indent=2)

    print eems_model_modified_id

    cursor = connection.cursor()

    # If this is the first run, make a copy of the model and store it in the user models database with a unique ID.
    if eems_model_modified_id == '':
        eems_model_modified_id = get_random_string(length=32)

        query = "SELECT NAME, MODEL FROM EEMS_ONLINE_MODELS where id = '%s'" % eems_model_id
        cursor.execute(query)
        for row in cursor:
            eems_model_name = row[0]
            eems_model = row[1]

        pdata = pickle.dumps(eems_model, pickle.HIGHEST_PROTOCOL)

        cursor.execute("insert into EEMS_USER_MODELS (ID, NAME, MODEL) values (%s,%s,%s)", (eems_model_modified_id, eems_model_name, sqlite3.Binary(pdata)))

    # Get the current state of the model out of the database
    query = "SELECT MODEL FROM EEMS_USER_MODELS where ID = '%s'" % eems_model_modified_id

    cursor.execute(query)
    for row in cursor:
        modified_eems_model = pickle.loads(str(row[0]))

    src_program_name = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/eemssrc/model.mpt'.format(eems_model_id)
    output_base_dir = settings.BASE_DIR + '/eems_online_app/static/eems/models/{}/'.format(eems_model_id)

    my_mpilot_worker = MPilotWorker()
    my_mpilot_worker.HandleRqst('1', src_program_name, eems_operator_changes_string, output_base_dir, True, True, True)

    # ToDo: Apply changes in the eems_operator_changes_dict to the EEMS model stored in modified_eems_model
    # ToDo: Run EEMS on the new model
    # ToDo: Create PNGs stored in folder that matches the user id.

    # ToDo: Over-write the model in the EEMS_USER_MODELS Database.

    #print modified_eems_model

    return HttpResponse(eems_model_modified_id)