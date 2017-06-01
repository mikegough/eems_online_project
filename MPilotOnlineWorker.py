#!/opt/local/bin/python

import MPilotProgram as mpprog
import MPilotFramework as mpf
import MPilotParseMetadata as mppm
import json
import os
import uuid # to make a unique file name
import time # sleep for lock timing
from collections import OrderedDict
import re

class MPilotWorker(mpprog.MPilotProgram):

    # The big idea behind this is that we want to be stateless.
    # Between receiving commands for an MPilot instance. Every time
    # this class is used, it will load a string representation
    # of an existing model (unless it creates a new one), execute
    # the action the caller wants executed, and return the string
    # representation including any modifications made.

    def __init__(self):
        
        self.mpFramework = mpf.MPilotFramework([
            'MPilotEEMSBasicLib',
            'MPilotEEMSFuzzyLogicLib',
            'MPilotEEMSNC4IO',
            'MPilotEEMSOnlineGraphicsLib',
            ])

        self.unorderedMPCmds = OrderedDict()
        self.orderedMPCmds = None
        self.rslts = {}
        
        # Intializing without input file because we'll build the
        # EEMS program one command at a time.
        
        # A set of functions used to get function info
        self.refFxnObjs = OrderedDict() # will not be executed
        for fxnNm in self.mpFramework.FxnNames():
            self.refFxnObjs[fxnNm] = self.mpFramework.CreateFxnObject(fxnNm)
        
    # def __init__(self):

    def _CreateAndAddMptCmd(self,parsedCmd):

        # print json.dumps(parsedCmd,indent=2)
        
        if self.RsltNmExists(parsedCmd['rsltNm']):
            raise Exception('duplicate command')

        newMptCmd = self.mpFramework.CreateFxnObject(parsedCmd['cmd'])
        newMptCmd.InitFromParsedCmd(parsedCmd)

        # print newMptCmd.DataType()

        self.AddCmd(newMptCmd)
        return self.ProgAsText()        

    # def _CreateAndAddMptCmd(self,parsedCmd):

    def _AddOutputDataCmd(self,rsltNms):
        
        # Saving model results 
        
        # find a valid input field in order to grab a file
        # and variable for dimensions
        for cmdNm,cmd in self.UnorderedCmds().items():
            if cmd.FxnNm() == 'EEMSRead':
                dimFileNm = cmd.ArgByNm('InFileName')
                dimFieldNm = cmd.ArgByNm('InFieldName')

        parsedCmd = {}
        parsedCmd['rsltNm'] = '{}_OutputDone'.format(self.id)
        parsedCmd['cmd'] = 'EEMSWrite'
        parsedCmd['arguments'] = {
            'OutFieldNames':'[{}]'.format(','.join(rsltNms)),
            'OutFileName':'../eems/models/{}/data/nc/Results.nc'.format(self.id),
            'OutFileName':'{}.nc'.format('Tst'),
            'DimensionFileName': dimFileNm,
            'DimensionFieldName':dimFieldNm
            }

        self._CreateAndAddMptCmd(parsedCmd)

    # def _AddOutputDataCmd(self):

    def _AddOutputLayerCmds(self,rsltNms):

        # Save each node's data to a graphic
        for rsltNm in rsltNms:
            parsedCmd = {}
            
            parsedCmd['rsltNm'] = '{}_RenderDone'.format(rsltNm)
            parsedCmd['cmd'] = 'RenderLayer'
            parsedCmd['arguments'] = {
                'InFieldName':rsltNm,
                'OutFileName':'../eems/models/{}/overlay/png/{}.png'.format(self.id,rsltNm)
                }

            self._CreateAndAddMptCmd(parsedCmd)
            # Add _legend to OutFileName (vertical legend)
            
    # def _AddOutputLayerCmds(self)

    def _AddOutputDistributionCmds(self,rsltNms):

        # Save each node's data to a graphic
        for rsltNm in rsltNms:
            parsedCmd = {}
            parsedCmd['rsltNm'] = '{}_{}_HistoDist'.format('Tst',rsltNm)
            parsedCmd['cmd'] = 'HistoDist'
            parsedCmd['arguments'] = {
                'InFieldName':rsltNm,
                'OutFileName':'../eems/models/{}/histogram/png/{}.png'.format(self.id,rsltNm)
                }

            self._CreateAndAddMptCmd(parsedCmd)
            
    # def _AddOutputLayerCmds(self)

    def _DelOutputDataCmd(self):

        for cmdNm,cmd in self.UnorderedCmds().items():
            if cmd.FxnNm() == 'EEMSWrite':
                self.DelCmdByRsltNm(cmdNm)
        
    # def _DelOutputDataCmd(self):
        
    def _DelOutputLayerCmds(self):

        for cmdNm,cmd in self.UnorderedCmds().items():
            if cmd.FxnNm() == 'RenderLayer':
                self.DelCmdByRsltNm(cmdNm)
        
    # def _DelOutputLayerCmds(self,rsltNms):

    def _DelOutputDistributionCmds(self):
        
        for cmdNm,cmd in self.UnorderedCmds().items():
            if cmd.FxnNm() == 'HistoDist':
                self.DelCmdByRsltNm(cmdNm)        
        
    # def _DelOutputDistributionCmds(self,rsltNms):
        
    def _RunProg(self):

        # first we save the mpt script represented by
        # the mpt program:

        with open('../eems/models/{}/eemssrc/model.mpt'.format(self.id),'w') as outF:
            outF.write(self.ProgAsText())

        # Since we want to produce an outputfile as well
        # as a map image and a distribution 
        # for each node in the model, we need
        # to add commands to do that to the program before
        # we run it, and remove the commands after the run.

        rsltNms = self.UnorderedCmds().keys()
        
        self._AddOutputDataCmd(rsltNms)
        self._AddOutputLayerCmds(rsltNms)
        self._AddOutputDistributionCmds(rsltNms)

        # Run it with output
        self.Run()

        # Delete those temporary output commands

        self._DelOutputDataCmd()
        self._DelOutputLayerCmds()
        self._DelOutputDistributionCmds()

        return self.ProgAsText()
    
    # def _RunProg(self):

    def _ProcessCmds(self,rqstCmds):
        
        for rqstCmd in rqstCmds:
            self._ProcessRqst(rqstCmd)
            
        return self.ProgAsText()
    
    # def _ProcessCmds(self,rqstCmds):

    def _CreateProg(self):
        
        return self.ProgAsText()

    # def _CreateProg(self):
        
    def _MakeMEEMSESubtree(self,rsltNm):

        mptCmd = self.CmdByNm(rsltNm)
        cmdData = OrderedDict()
        meemseSubtree = OrderedDict()
        
        meemseSubtree['id'] = rsltNm
        meemseSubtree['name'] = rsltNm
        meemseSubtree['data'] = OrderedDict()
        
        meemseSubtree['data']['arguments'] = []
        if mptCmd.Args() is not None:
            for argNm in mptCmd.Args():
                if argNm == 'Metadata': continue
                meemseSubtree['data']['arguments'].append(
                    '{}:{}'.format(
                        argNm,
                        re.sub(r'(.*)\]$',r'\1',re.sub(r'^\[(.*)$',r'\1',mptCmd.ArgByNm(argNm)))
                        )
                    )

            if 'Metadata' in mptCmd.Args():
                meemseSubtree['data']['Metadata'] = (
                    mppm.ParseMetadata(mptCmd.ArgByNm('Metadata'))
                    )
                    
                
        
        meemseSubtree['data']['is_fuzzy'] = False
        if mptCmd.FxnReturnType() == 'Fuzzy':
            meemseSubtree['data']['is_fuzzy'] = True
        elif mptCmd.ArgByNm('DataType') == 'Fuzzy':
            meemseSubtree['data']['is_fuzzy'] = True
            
        meemseSubtree['data']['raw_operation'] = mptCmd.FxnNm()
        meemseSubtree['data']['short_desc'] = mptCmd.FxnShortDesc()
        meemseSubtree['data']['operation'] = mptCmd.FxnDisplayName()
        meemseSubtree['data']['full_mptCmd'] = mptCmd.CleanCmdStr()

        if mptCmd.DependencyNms() != []:
            meemseSubtree['children'] = []
            for childRsltNm in mptCmd.DependencyNms():
                meemseSubtree['children'].append(self._MakeMEEMSESubtree(childRsltNm))

        return meemseSubtree
        
    # def _MakeMEEMSENodeDef(self,cmdNm):

    def _MakeMEEMSETrees(self):

        meemseTrees = []
        
        for rsltNm,lvl in self.CmdTree():
            if lvl == 0:
                meemseTrees.append(self._MakeMEEMSESubtree(rsltNm))

        return meemseTrees
            
    def _UpdateCmd(self,parsedCmd):
        
        if not self.RsltNmExists(parsedCmd['rsltNm']):
            raise Exception('missing command')
        self.DelCmdByRsltNm(parsedCmd['rsltNm'])
        self._CreateAndAddMptCmd(parsedCmd)
        
        return self.ProgAsText()
    
    # def _UpdateCmd(self):

    def _GetParsedCmd(self,rsltNm):
        
        if not self.RsltNmExists(rsltNm):
            raise Exception('missing command')
        
        return self.CmdByNm(rsltNm).ParsedCmd()
        
    # def _GetParsedCmd():
        
    def _DelCmd(self,rsltNm):
        
        if not self.RsltNmExists(rsltNm):
            raise Exception('missing command')
        self.DelCmdByRsltNm(rsltNm)
        
        return self.ProgAsText()
            
    # def _DelCmd(self):

    def _GetCmdNms(self):
        
        return self.mpFramework.FxnNms()

    # def _GetCmdNms(self):

    def _GetCmdInfo(self,cmdNm):
            
        return self.refFxnObjs[cmdNm].FxnDesc()

    # def _GetMCmdDesc(self,cmdNm):

    def _GetFormattedCmdInfo(self,fxnNm):
        
        return self.refFxnObjs[fxnNm].FormattedFxnDesc()
            
    # def _GetCmdInfo(self,fxnNm):

    def _GetAllCmdInfo(self):
        
        return self.mpFramework.GetAllFxnClassInfo()

    # def _GetAllCmdInfo(self):

    def _GetAllFormattedCmdInfo(self):
        
        return self.mpFramework.GetAllFormattedFxnClassInfo()

    # def _GetAllCmdInfo(self):

    def _ProcessRqst(self,rqst):

        if rqst['action'] ==   'ProcessCmds':             rtrn = self._ProcessCmds(rqst['cmds'])
        elif rqst['action'] == 'CreateProg':              rtrn = self._CreateProg()
        elif rqst['action'] == 'AddCmd':                  rtrn = self._CreateAndAddMptCmd(rqst['cmd'])
        elif rqst['action'] == 'UpdateCmd':               rtrn = self._UpdateCmd(rqst['cmd'])
        elif rqst['action'] == 'DelCmd':                  rtrn = self._DelCmd(rqst['rsltNm'])
        elif rqst['action'] == 'RunProg':                 rtrn = self._RunProg()
        elif rqst['action'] == 'GetMEEMSETrees':          rtrn = self._MakeMEEMSETrees()
        elif rqst['action'] == 'GetParsedCmd':            rtrn = self._GetParsedCmd(rqst['rsltNm'])
        elif rqst['action'] == 'GetCmdNms':               rtrn = self._GetCmdNms()
        elif rqst['action'] == 'GetCmdInfo':              rtrn = self._GetCmdInfo(rqst['cmdNm'])
        elif rqst['action'] == 'GetFormattedCmdInfo':     rtrn = self._GetFormattedCmdInfo(rqst['cmdNm'])
        elif rqst['action'] == 'GetAllCmdInfo':           rtrn = self._GetAllCmdInfo()
        elif rqst['action'] == 'GetAllFormattedCmdInfo':  rtrn = self._GetAllFormattedCmdInfo()
        elif rqst['action'] == 'GetLineCmdTree':          rtrn = self.CmdTreeWithLines()
        else: raise Exception('illegal request')

        return rtrn
        
    # def _ProcessRqst(self,rqst):
    
    def HandleRqst(
        self,
        rqst,
        id = None,
        outputBaseDir = None,
        extent = None,
        epsg = None,
        map_quality = None,
        srcProgNm = None,
        doFileLoad=False,
        rqstIsJSON=False,
        reset=True
        ):

        self.outputBaseDir = outputBaseDir
        self.id = id
        self.extent = extent
        self.epsg = epsg
        self.map_quality = map_quality

        rtrn = None

        if rqstIsJSON: rqst = json.loads(rqst)

        if os.path.isfile(srcProgNm) and doFileLoad:
            self.LoadMptFile(srcProgNm)
        # elif rqst['action'] != 'CreateProg':
        #     raise Exception('missing source program')

        rtrn = self._ProcessRqst(rqst)
        
        if srcProgNm is not None:
            with open(srcProgNm,'w') as outF:
                outF.write(self.ProgAsText())
            
        if reset:
            self._ClearCmds() # resets this program so it has no commands
            self.id = None
        
        return json.dumps(rtrn)

    # def HandleRqst(self,jsonRqst):

# class MPilotWorker(mpprog.MPilotProgram):
