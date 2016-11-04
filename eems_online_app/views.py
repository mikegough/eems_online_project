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
try:
   import cPickle as pickle
except:
   import pickle

@csrf_exempt
def index(request):

        eems_online_models=[]
        # Connect to the database
        cursor = connection.cursor()
        # Retreive EEMS data from Database
        #query="SELECT MODEL FROM EEMS_ONLINE_MODELS;"
        #cursor.execute(query)
        #for row in cursor:
        #    eems_online_model.append = row[0]
        #print (eems_model_models)

        # ToDo: Get EEMS Commands from eems?
        # Command: Form inputs
        eems_available_commands = {}
        eems_available_commands["Union"] = ''
        eems_available_commands["Weighted Union"] = "Each child <Input Text Field>"
        eems_available_commands["Selected Union"] = "Select the <Dropdown (Truest/Falsest)> <Input Text Field>"

        template = 'index.html'
        context = {
            'eems_available_commands_dict': eems_available_commands
        }

        return render(request, template, context)

@csrf_exempt
def load_eems(request):

        #  For user uploaded EEMS file

        #  User passes back a serialized EEMS command file.
        # eems_command_file = open(r'F:\Projects2\EEMS_Online\tasks\web_applications\eems_online_django\eems_online_project\eems_online_app\static\eems\command_files\CA_Site_Sensitivity.eem')
        # eems_commands = eems_command_file.read()

        eems_model_id = get_random_string(length=32)
        eems_model_name = request.POST.get('eems_filename').split('.')[0]
        eems_file_contents = request.POST.get('eems_file_contents')

        # ToDo: Create EEMS program from EEMS file + Pickle that.

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
    eems_model = request.POST.get('eems_model')
    eems_operator_changes_string = request.POST.get('eems_operator_changes_string')

    print eems_model
    print eems_operator_changes_string

    return HttpResponse("1")
