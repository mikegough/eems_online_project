# MPilot is a framework designed to let programmers create tree-based
# workflow frameworks for users. This is the top level class used in
# the MPilot Framework.
#
# File Log:
# 2016.07.06 - tjs
#  Created _MPilotFxnParent

from collections import OrderedDict
import copy as cp

class _MPilotFxnParent(object):

    def __init__(self,mptCmdStruct = None):

        # self.mptCmdStruct contains information about the MPilot command
        # that is used to order commands, check command validity,
        # and provide detailed information in error messages.

        # The parameters that are used in executing the command
        
        self.execRslt = None
        self.fxnDesc = OrderedDict()
        self.fxnDesc['Name'] = self.__class__.__name__
        self._SetFxnDesc()

        if mptCmdStruct is None:
            
            self.mptCmdStruct = {
                'cmdFileNm':None,
                'lineNo':None,
                'rawCmdStr':None,
                'cleanCmdStr':None,
                'parsedCmd':None
                }

            self.mptCmdStruct['parsedCmd'] = {}
            self.mptCmdStruct['parsedCmd']['params'] = {}
                
        else:
            
            self.mptCmdStruct = cp.deepcopy(mptCmdStruct)
            self._ValidateStrCmd()
            
        # if mptCmdStruct is None:

    # def __init__(...)

    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        raise Exception(
            '{}{}{}{}{}{}{}'.format(
                '\n********************ERROR********************\n',
                'Programming error:\n',
                '  Your program is using the inherited _MPilotFxnParent:_SetFxnDesc() method.',
                '  There should be a unique _SetFxnDesc() method for the defined MPilot command.',
                '  Check and correct the class definition of the MPilot command: {}\n'.format(self.fxnDesc['Name']),
                'File: {}  Line number: {}\n'.format(
                    self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                    ),
                'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

        ### Below is provided as example of how to code a function
        ### description. You should do this for each MPilot Command
        ### you create.

        self.fxnDesc['Name'] = 'PilotCmd'
        self.fxnDesc['ReqParams'] = {
            'InFileName':'File Name',   # for commands that read
            'InField':'Field Name',     # a field name or field name list
            'Other':'TypeOfArgumentVariable'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'PrecursorField':'Field Name', # a field name or field name list
            }
        
        self.fxnDesc['DisplayName'] = 'UserFriendlyName'
        self.fxnDesc['ShortDesc'] = 'QuickDescription'
        self.fxnDesc['ReturnType'] = 'TypeOfReturnVariable'

    # _SetFxnDesc(self):

    def _ValidateStrCmd(self):
        # Assumes syntax of parsed command is valid
        # Right now, does not check result name

        cmdParams = self.mptCmdStruct['parsedCmd']['params']

        reqParamsSet = set(self.fxnDesc['ReqParams'])
        optParamSet = set(self.fxnDesc['OptParams'])
        inParamsSet = set(cmdParams.keys())
        
        # are all required params there?
        if not reqParamsSet.issubset(inParamsSet):
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Missing input parameter(s):\n  {}\n'.format(
                        ' '.join(reqParamsSet - inParamsSet)
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

        # are all of the params either optional or required?
        if not inParamsSet.issubset(set.union(reqParamsSet,optParamSet)):
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid input parameter(s):\n  {}\n'.format(
                        ' '.join(inParamsSet - set.union(reqParamsSet,optParamSet))
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

        # Is the result name a valid field name
        self._ValidateParamType(self.mptCmdStruct['parsedCmd']['rsltNm'],'Field Name')
        
        # Are the all the params of the correct type?
        # loop through the allowed parameter
        descParams = cp.deepcopy(self.fxnDesc['ReqParams'])
        descParams.update(self.fxnDesc['OptParams'])

        for descParamNm,descParamType in descParams.items():

            # if the param was not in the input params,
            # don't worry about it
            if descParamNm not in inParamsSet: 
                continue
            
            # param type spec can be list, if not make it a
            # list for ease of coding this
            if not isinstance(descParamType,list):
                descParamType = [descParamType]

            # loop through the valid param types
            paramIsValid = False
            for pType in descParamType:
                if  self._IsParamType(cmdParams[descParamNm],pType):
                    paramIsValid = True
                    break
            # for pType in paramType:
                
            # determine if the param is one the valid types

            if not paramIsValid:
                raise Exception(
                    '{}{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Invalid parameter value:\n',
                        '  Parameter name: {}\n  Should be one of:\n    {}\n  Value is:{}\n'.format(
                            descParamNm,
                            '\n    '.join(descParamType),
                            cmdParams[descParamNm]
                            ),
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                        ),
                    )
                
    # def _ValidateStrCmd():
    # Functions to test individual file types

    def _ValidateParamExists(self,paramNm):

        if not self.ParamExists(paramNm):
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Trying to acces invalid parameter:\n',
                    '  Parameter name: {}\n'.format(
                        paramNm
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

    # def _ValidateParamExists(self,paramNm):

    def _ValidateParamType(self,param,paramType):

        if not self._IsParamType(param,paramType):
            
            print param,paramType
            
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Input parameter has invalid type:\n',
                    'Value: {}  Is not: {}\n'.format(
                        param,
                        paramType
                        ),
                    
                    # 'Parameter name: {}  Should be: {}  Is: {}\n'.format(
                    #     'InVals',
                    #     self.fxnDesc['ReqParams']['InVals'],
                    #     pCmd['params']['InVals'],
                    #     ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

    # def _ValidateParamType(self,param,paramType):
        
    def _ValidateListLen(self,paramNm,minLen,maxLen=float('inf')):

        listLen = len(self.ParamByNm('InFieldNames').replace('[','').replace(']','').split(','))
        
        if not minLen <= listLen <= maxLen:
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Parameter list has invalid length:\n',
                    'Parameter name: {}  Should be: {} <= Length <= {}  Length is {}.\n'.format(
                        paramNm,
                        minLen,
                        maxLen,
                        len(myLst)
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )
            
    # def _ValidateListLen(self,myLst,minLen,maxLen=float('inf')):

    def _ValidateEqualListLens(self,paramNms):
        
        listLen = -1
        for paramNm in paramNms:
            pListLen = len(self.ParamByNm(paramNm).replace('[','').replace(']','').split(','))
            if listLen < 0:
                listLen = pListLen
            elif pListLen != listLen:
                raise Exception(
                    '{}{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'List parameters do not have identical lengths:\n',
                        '  These parameters must have identical lengths:\n    {}\n'.format(
                            '\n    '.join(paramNms)
                            ),
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],
                            self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )
            
    # def _ValidateEqualListLens(self,paramNms):
    
    def _ValidateParamListItemsUnique(self,paramNm):

        inLst = self.ValFromParamByNm('RawValues')
        
        if not isinstance(inLst,list): return
        
        if len(set(inLst)) != len(inLst):
            raise Exception(
                '{}{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'List parameter does not have unique entries:\n',
                    '   Parameter name: {}\n'.format(
                        paramNm,
                        ),
                    '   Parameter values:\n    {}\n'.format(
                        '\n    '.join([float(x) for x in inLst]),
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

        
    # def _ValidateEqualListLens(self,paramNms):

    def _ParamToList(self,paramNm):
        
        rtrn = [] # empty list if the param does not exist in the cmd
        if self.ParamByNm(paramNm) is not None:
            rtrn = self.ParamByNm(paramNm).replace('[','').replace(']','').split(',')

        return rtrn
    
    # def _ParamToList(self,paramNm):
        
    def _IsParamType(self,inStr,inType):
        
        raise Exception(
            '{}{}{}{}{}{}{}'.format(
                '\n********************ERROR********************\n',
                'Programming error:\n',
                '  Your program is using the inherited _MPilotFxnParent:_IsParamType() method.',
                '  There should be a unique _IsParamType() method for the defined MPilot command.',
                '  Check and correct the class definition of the MPilot command: {}\n'.format(self.fxnDesc['Name']),
                'File: {}  Line number: {}\n'.format(
                    self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                    ),
                'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )
    
    # def _IsParamType(self,inStr,inType):
                    
    def __enter__(self):
        return(self)

    def __exit__(self,exc_type,exc_value,traceback):
        if exc_type is not None:
            print exc_type, exc_value, traceback

    ## Public methods

    def InitFromParsedCmd(self,parsedCmd):
        
        self.mptCmdStruct['parsedCmd'] = cp.deepcopy(parsedCmd)
        self.InitRawCmdFromParsedCmd()
        self.InitCleanCmdFromParsedCmd()
        
    # def InitFromParsedCmd(self,parsedCmd):
    
    def ParamTypesFromParam(self,paramNm):

        if paramNm in self.fxnDesc['ReqParams']:
            return self.fxnDesc['ReqParams'][paramNm]
        elif paramNm in self.fxnDesc['OptParams']:
            return self.fxnDesc['OptParams'][paramNm]
        else:
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Illegal parameter:  {}\n'.format(paramNm),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

    # def ParamTypesFromParam(self,paramNm):
    
    def SetRsltNm(self,nm): self.mptCmdStruct['parsedCmd']['rsltNm'] = nm

    def SetParam(self,paramNm,value):
        self.mptCmdStruct['parsedCmd']['params'][paramNm] = cp.deepcopy(value)

    def SetCmdFileNm(self,nm): self.mptCmdStruct['cmdFileNm'] = nm
        
    def SetLinNo(self,num): self.mptCmdStruct['LineNo'] = nm
        
    def SetRawCmdStr(self,cmdStr): self.mptCmdStruct['rawCmdStr'] = cmdStr
        
    def SetCleanCmdStr(self,cmdStr): self.mptCmdStruct['cleanCmdStr'] = cmdStr
        
    # MPilot Function description access
    def ParamExists(self,nm):
        
        rtrn = False
        if self.mptCmdStruct is not None:
            if 'parsedCmd' in self.mptCmdStruct:
                rtrn = nm in self.mptCmdStruct['parsedCmd']['params']
        return rtrn
    
    def RsltNm(self): return self.mptCmdStruct['parsedCmd']['rsltNm']
    
    def FxnNm(self): return self.fxnDesc['Name']

    def FxnReqParams(self): return self.fxnDesc['ReqParams']
    
    def FxnOptParams(self): return self.fxnDesc['OptParams']
        
    def FxnDisplayName(self): return self.fxnDesc['DisplayName']
        
    def FxnShortDesc(self): return self.fxnDesc['ShortDesc']
        
    def FxnReturnType(self): return self.fxnDesc['ReturnType']
        
    def FxnDesc(self): return self.fxnDesc
        
    def FormattedFxnDesc(self):

        rtrnStr = ''
        if 'Name' in self.fxnDesc:
            rtrnStr = '{}{}: {}\n'.format(rtrnStr,'Function Name',self.fxnDesc['Name'])
        if 'DisplayName' in self.fxnDesc:
            rtrnStr = '{}  {}: {}\n'.format(rtrnStr,'Display Name',self.fxnDesc['DisplayName'])
        if 'ShortDesc' in self.fxnDesc:
            rtrnStr = '{}  {}: {}\n'.format(rtrnStr,'Description',self.fxnDesc['ShortDesc'])
        if 'ReturnType' in self.fxnDesc:
            rtrnStr = '{}  {}: {}\n'.format(rtrnStr,'Return Type',self.fxnDesc['ReturnType'])
        if 'InputType' in self.fxnDesc:
            rtrnStr = '{}  {}: {}\n'.format(rtrnStr,'Input Type',self.fxnDesc['InputType'])
        if 'ReqParams' in self.fxnDesc:
            rtrnStr = '{}  Required Paramaters and data types:\n'.format(rtrnStr)
            for argKey,argVal in self.fxnDesc['ReqParams'].items():
                rtrnStr = '{}    {}: {}\n'.format(rtrnStr,argKey,argVal)
        if 'OptParams' in self.fxnDesc:
            rtrnStr = '{}  Optional Paramaters and data types:\n'.format(rtrnStr)
            for argKey,argVal in self.fxnDesc['OptParams'].items():
                rtrnStr = '{}    {}: {}\n'.format(rtrnStr,argKey,argVal)

        return rtrnStr
        
    # def FxnDescStr(self):

    # Object item access

    def StrCmd(self): return self.mptCmdStruct
        
    def CmdFileNm(self): return self.mptCmdStruct['cmdFileNm']
        
    def LineNo(self): return self.mptCmdStruct['lineNo']
        
    def RawCmdStr(self): return self.mptCmdStruct['rawCmdStr']
        
    def CleanCmdStr(self): return self.mptCmdStruct['cleanCmdStr']
        
    def ParsedCmd(self): return self.mptCmdStruct['parsedCmd']

    def FormattedCmd(self):
        
        rtrnStr = '{} = {}(\n'.format(
            self.ParsedCmd()['rsltNm'],
            self.ParsedCmd()['cmd']
            )
        rtrnStr = '{}{}\n)'.format(
            rtrnStr,
            ',\n'.join(
                ['    {} = {}'.format(pNm,pVal) for pNm,pVal in self.ParsedCmd()['params'].items()]
                )
            )

        return rtrnStr

    # def FormattedCmd(self):
        
    def InitRawCmdFromParsedCmd(self):
        newCmdStr = '{} = {}(\n  '.format(
            self.mptCmdStruct['parsedCmd']['rsltNm'],
            self.fxnDesc['Name']
            )

        paramLines = ['{} = {}'.format(k,v) for k,v in self.mptCmdStruct['parsedCmd']['params'].items()]
        newCmdStr = '{}{}'.format(newCmdStr,',\n  '.join(paramLines))
        newCmdStr = '{}\n)'.format(newCmdStr)
        self.SetRawCmdStr(newCmdStr)
        
    def InitCleanCmdFromParsedCmd(self):
        newCmdStr = '{} = {}(\n  '.format(
            self.mptCmdStruct['parsedCmd']['rsltNm'],
            self.fxnDesc['Name']
            )

        paramLines = ['{} = {}'.format(k,v) for k,v in self.mptCmdStruct['parsedCmd']['params'].items()]
        newCmdStr = '{}{}'.format(newCmdStr,',\n  '.join(paramLines))
        newCmdStr = '{}\n)'.format(newCmdStr)
        self.SetCleanCmdStr(newCmdStr)
        
    def RsltNm(self):
        if self.mptCmdStruct['parsedCmd'] is not None:
            return self.mptCmdStruct['parsedCmd']['rsltNm']
        else:
            return None
        
    def Params(self):
        if self.mptCmdStruct['parsedCmd'] is not None:
            return self.mptCmdStruct['parsedCmd']['params']
        else:
            return None
        
    def ParamByNm(self, paramNm):
        rtrn = None
        if self.mptCmdStruct['parsedCmd'] is not None:
            if paramNm in self.mptCmdStruct['parsedCmd']['params']:
                rtrn = self.mptCmdStruct['parsedCmd']['params'][paramNm]
        return rtrn

    # Get some other things
    def ExecRslt(self):
        return self.execRslt

    def DependencyNms(self):
        # Parse out the dependency names from the self.mptCmdStruct
        # and return them
        return None

    # Execute the command
    def Exec(self,executedObjects):
        # This is where the the execution string gets built
        # and executed. The results are added to executedObjects.
        # executedObjects is a dictionary, each entry is a data layer.
        # Depending on how the implementde MPilot framework is
        # designed, executedObjects may contain numpy arrays (masked
        # arrays recommended), as well as data descriptors.
        #
        # Any data checking needs to be done here.

        # Throw an error if this method is not implemented in descendent
        raise Exception(
            '{}{}{}{}{}{}{}'.format(
                '\n********************ERROR********************\n',
                'Programming error:\n',
                '  Your program is using the inherited _MPilotFxnParent:Exec() method.',
                '  There should be a unique Exec() method for the defined MPilot command.',
                '  Check and correct the class definition of the MPilot command: {}\n'.format(self.fxnDesc['Name']),
                'File: {}  Line number: {}\n'.format(
                    self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                    ),
                'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

        ### Below is to give you an idea of what to do. i.e. calculate
        ### something and add it to the data.
        
        self.execRslt = None # Do a calculation
        if updateProgData:
            executedObjects[self.RsltNm()] = self.execRslt
            
    # def Exec(self,executedObjects,updateProgData=True):

# class PilotFxnSpec(object):
    
