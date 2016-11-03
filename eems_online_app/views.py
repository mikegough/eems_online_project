from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import sys
import subprocess
from textblob import TextBlob
import bitarray
import sqlite3
import time
from django.utils.crypto import get_random_string
try:
   import cPickle as pickle
except:
   import pickle

@csrf_exempt
def index(request):

        template = 'index.html'
        context = {
            'name': 'eems'
        }

        return render(request, template, context)

@csrf_exempt
def load_eems(request):

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
        cursor.execute("insert into EEMS (ID, NAME, MODEL) values (%s,%s,%s)", (eems_model_id, eems_model_name, sqlite3.Binary(pdata)))

        # Retreive EEMS data from Database
        query="SELECT MODEL FROM EEMS where ID = '%s'" % (eems_model_id)

        print query
        cursor.execute(query)
        for row in cursor:
            eems_model_contents = pickle.loads(str(row[0]))
        print (eems_model_contents)


        # ToDO: Convert EEMS file to JSON

        # ToDO: Get list of available EEMS commands from MPilot EEMS

        # ToDO Create New PNG files from EEMS output

        eems_available_actions = {}
        eems_available_actions["Add a Node"] = {}
        eems_available_actions["Delete a Node"] = {}

        eems_available_commands = {}
        eems_available_commands["read"] = {}
        eems_available_commands["read"]["optional_args"] = {}
        eems_available_commands["read"]["required_args"] = {}
        eems_available_commands["read"]["required_args"]["input_field"] = ["Input Name", "Text"]
        eems_available_commands["read"]["required_args"]["output_field"] = ["Output Name", "Text"]


        context = {
            "eems_model_id" : eems_model_id,
            "eems_available_actions": eems_available_actions,
            "eems_available_commands": eems_available_commands
        }

        return HttpResponse(json.dumps(context))

def modify_eems(request):

    return HttpResponse("1")

