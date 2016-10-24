from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def index(request):

    if request.method == 'POST':

        # Get EEMS command changes
        eems_operator_changes_string = request.POST.get('eems_operator_changes_string')
        eems_operator_changes_dict = json.loads(eems_operator_changes_string)

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

