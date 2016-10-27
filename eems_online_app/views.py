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
try:
   import cPickle as pickle
except:
   import pickle

@csrf_exempt
def index(request):

    if request.method == 'POST':

        model_id = 'abc345'

        eems_command_file = open(r'F:\Projects2\EEMS_Online\tasks\web_applications\eems_online_django\eems_online_project\eems_online_app\static\eems\command_files\CA_Site_Sensitivity.eem')
        eems_commands = eems_command_file.read()

        # Get EEMS command changes
        eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
        eems_operator_changes_dict = json.loads(eems_operator_changes_string)
        #print (eems_operator_changes_dict)

        cursor = connection.cursor()

        model="eems model"

        ################## Bit array
        # create a new empty bitarray
        b = bitarray.bitarray()
        # load eems_commands
        b.fromstring(eems_commands)
        #cursor.execute("INSERT INTO EEMS(ID, MODEL) values (%s,%s)", (model_id, sqlite3.Binary(b.to01())))
        #cursor.execute("INSERT INTO EEMS(ID, MODEL) values (%s,%s)", (model_id, b.to01()))

        ############### TextBlob

        eems_TextBlob = TextBlob(eems_commands)
        #print (eems_TextBlob.tags)

        #cursor.execute("INSERT INTO EEMS(ID, MODEL) values (%s,%s)", (model_id, eems_TextBlob))

        ################## Pickle

        #Return the pickled representation of the object as a bytes object,
        pdata = pickle.dumps(eems_commands, pickle.HIGHEST_PROTOCOL)

        cursor.execute("insert into EEMS (ID, MODEL) values (%s,%s)", (model_id, sqlite3.Binary(pdata)))

        query="SELECT MODEL FROM EEMS where ID = '" + model_id + "';"
        cursor.execute(query)
        for row in cursor:
          data = pickle.loads(str(row[0]))

        print (data)

        #print str(pmodel_state).decode('utf-8')

        #print(pickle.loads(pmodel_state))


        #query="SELECT MODEL FROM EEMS where ID = '" + model_id + "';"
        #cursor.execute(query);
        model_state=cursor.fetchone()
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


