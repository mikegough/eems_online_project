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

    if request.method == 'POST':

        model_id = 'abc345'

        #  User passes back a serialized EEMS command file.
        eems_command_file = open(r'F:\Projects2\EEMS_Online\tasks\web_applications\eems_online_django\eems_online_project\eems_online_app\static\eems\command_files\CA_Site_Sensitivity.eem')
        eems_commands = eems_command_file.read()

        # Get EEMS command changes
        eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
        eems_operator_changes_dict = json.loads(eems_operator_changes_string)
        #print (eems_operator_changes_dict)

        cursor = connection.cursor()

        # Return the pickled representation of the object as a bytes object,
        pdata = pickle.dumps(eems_commands, pickle.HIGHEST_PROTOCOL)

        # Insert command !!!
        #cursor.execute("insert into EEMS (ID, MODEL) values (%s,%s)", (model_id, sqlite3.Binary(pdata)))

        query="SELECT MODEL FROM EEMS where ID = '" + model_id + "';"
        cursor.execute(query)
        for row in cursor:
          data = pickle.loads(str(row[0]))
        print (data)

        #query="SELECT MODEL FROM EEMS where ID = '" + model_id + "';"
        #cursor.execute(query);
        #model_state=cursor.fetchone()
        #print (model_state)

        # ToDO Write changes to a new EEMS file

        # ToDO Run EEMS on new EEMS file

        # ToDO Create New PNG files from EEMS output

        # Necessary to return anything?
        return HttpResponse(json.dumps(eems_operator_changes_dict))

    else:
        template = 'index.html'
        context = {
            'name': 'eems'
        }

        return render(request, template, context)


@csrf_exempt
def load_eems(request):

        eems_model_id = get_random_string(length=32)
        eems_model_name = request.POST.get('eems_filename').split('.')[0]
        eems_file_contents = request.POST.get('eems_file_contents')

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


        # ToDO: Convert EEMS file to JSON and return to MEEMSE

        return HttpResponse(eems_model_contents)


