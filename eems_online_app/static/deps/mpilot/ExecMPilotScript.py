#!/opt/local/bin/python
import imp
import scipy
mpprog = imp.load_source('MPilotProgram', 'F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/eems_online_project/eems_online_app/static/deps/mpilot/MPilotProgram.py')
mpf = imp.load_source('MPilotFramework', 'F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/eems_online_project/eems_online_app/static/deps/mpilot/MPilotFramework.py')
mpp = imp.load_source('MPilotParse', 'F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/eems_online_project/eems_online_app/static/deps/mpilot/MPilotParse.py')
mpgl = imp.load_source('MPilotEEMSOnlineGraphicsLib', 'F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/eems_online_project/eems_online_app/static/deps/mpilot/MPilotEEMSOnlineGraphicsLib.py')
mpio = imp.load_source('MPilotEEMSNC4IO', 'F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/eems_online_project/eems_online_app/static/deps/mpilot/MPilotEEMSNC4IO.py')

#import MPilotProgram as mpprog
#import MPilotFramework as mpf
#import MPilotParse as mpp
from collections import OrderedDict
import numpy as np
import os
import sys

def UsageDie():
    print '{} InFName'.format(os.path.basename(sys.argv[0]))
    print
    print 'Run an MPilot program file\n'
    
    exit()
# def UsageDie():

def RunIt(inFNm):

    with mpprog.MPilotProgram(
        mpf.MPilotFramework([
            'MPilotEEMSBasicLib',
            'MPilotEEMSFuzzyLogicLib',
            ### Note which graphics lib ###
            'MPilotEEMSOnlineGraphicsLib',
            'MPilotEEMSNC4IO',
            ]),
            inFNm
        ) as prog:

        prog.Run()

# def CreateJSONFile(inFNm,outFNm)

if len(sys.argv) != 2: UsageDie()
RunIt(sys.argv[1])
