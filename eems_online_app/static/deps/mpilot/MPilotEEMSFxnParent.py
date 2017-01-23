# The Environmental Evaluation Modeling System, or EEMS allows users to
# build tree-based models that perform mathematical and logic operations.
# The intent is for these models to serve as decision support models
# for environmental planning. However, EEMS is well suited to applications
# in other disciplines.
#
# Because some EEMS functions are designed to work on values with a
# certain type (e.g. fuzzy values which usually have a numeric range
# between 0 and 1 or between -1 and 1), MPilot libraries for EEMS include
# type checking, and data layers are tagged with a type. The EEMS parent
# class, defined in this file, includes functions for validating data
# types defined by EEMS.
#
# EEMS was originally implemented as a standalone framework, but is now
# implemented using the MPilot framework. For more information about EEMS:
#
# http://http://consbio.org/products/tools/environmental-evaluation-modeling-system-eems
#
# Sheehan, T. and Gough, M. (2016) A platform-independent fuzzy logic
#    modeling framework for evironmental decision support. Ecological
#    Informatics. 34:92-101
#
# File Log:
# 2016.07.06 - tjs
#  Created _MPilotEEMSParent

import MPilotFxnParent as mpfp
import re
import numpy as np
import copy as cp

class _MPilotEEMSFxnParent(mpfp._MPilotFxnParent):

    def __init__(
        self,
        mptCmdStruct=None,
        dataType=None,
        isDataLayer=False
        ):

        self.fuzzyMin = -1.0
        self.fuzzyMax = 1.0
        self.dataType = dataType
        self.isDataLayer = isDataLayer
        super(_MPilotEEMSFxnParent, self).__init__(mptCmdStruct)

    # def __init__(self,mptCmdStruct=None):

    def _ValidateProgDataType(self,paramNm,paramDatum,tgtTypes):

        if not isinstance(tgtTypes,list): tgtTypes = [tgtTypes]

        if paramDatum.DataType() not in tgtTypes:
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Parameter list has invalid type:\n',
                    'Parameter name: {}  Should be one of: {}  Is: {}\n'.format(
                        paramNm,
                        tgtTypes,
                        paramDatum.DataType(),
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                        
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

    # def _ValidateProgDataType(self,paramNm,parmDatum,type2):

    def _ValidateIsDataLayer(self,mpObject):

        if not mpObject.IsDataLayer():
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Object required to be data layer is not a data layer:\n',
                    '  Object name: {}\n'.format(
                        mpObject.RsltNm(),
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

    # def _ValidateProgDataType(self,paramNm,parmDatum,type2):

    def InitFromParsedCmd(self,parsedCmd):
        
        self.mptCmdStruct['parsedCmd'] = cp.deepcopy(parsedCmd)
        self.InitRawCmdFromParsedCmd()
        self.InitCleanCmdFromParsedCmd()
        if 'DataType' in parsedCmd['params']:
            self.dataType = parsedCmd['params']['DataType']
        if 'IsDataLayer' in parsedCmd['params']:
            self.isDataLayer = parsedCmd['params']['IsDataLayer']
        
    # def InitFromParsedCmd(self,parsedCmd):

    def ValFromParamByNm(self,paramNm):

        # Return an actual value (be that a single value or a list)
        # of a parameter. Parameters are read as strings, so this
        # converts that string into what it is supposed be. Right
        # now, it only does conversion on variables that are numeric.
        # If there is an option for what the parameter can be, it
        # finds the most restrictive (e.g. integer instead of float)
        # definition for the parameter and does the conversion based
        # on that.

        rtrn = None
        param = self.ParamByNm(paramNm)

        if param is None: return None

        # Get the legal param types for this parameter
        if paramNm in self.fxnDesc['ReqParams']:
            legalParamTypes = self.fxnDesc['ReqParams'][paramNm]
        elif paramNm in self.fxnDesc['OptParams']:
            legalParamTypes = self.fxnDesc['OptParams'][paramNm]
        else:
            raise Exception(
                '{}{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Programming error:\n',
                    '  Cannot find description of paramter: {}'.format(paramNm),
                    '  Check and correct the class definition of the MPilot command: {}\n'.format(
                        self.fxnDesc['Name']
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

        # if paramNm self.fxnDesc['ReqParams']:

        # From the choices it is allowed to be, find out
        # the most restrictive type that fits. Note,
        # order of checking matters here.

        paramType = None
        
        if not isinstance(legalParamTypes, list):
            
            paramType = legalParamTypes
            
        else:

            for simplestParamType in [
                'Positive Integer',
                'Integer',
                'Positive Integer List',
                'Integer List',
                'Float',
                'Positive Float',
                'Fuzzy Value',
                'Fuzzy',
                'Float List',
                'Positive Float List',
                'Fuzzy Value List',
                ]:

                # Check the options for this parameter
                if simplestParamType in legalParamTypes:
                    # is it this?
                    if self._IsParamType(param,simplestParamType):
                        paramType = simplestParamType
                        break

        # if not isinstance(paramTypes, list):

        if paramType is None:
            raise Exception(
                '{}{}{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Illegal parameter value(s): \n'.format(legalParamTypes),
                    '  Parameter name: {}\n'.format(paramNm),
                    '  Must be (one of): {}\n'.format(legalParamTypes),
                    '  Value is: {}\n'.format(param),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    )
                )

        # List of the paramter values in string form
        paramVals = param.replace('[','').replace(']','').split(',')

        # Convert the string(s) into value(s)
        if paramType in [
            'Integer',
            'Positive Integer',
            'Integer List',
            'Positive Integer List',
            ]:
            rtrn = [int(x) for x in paramVals]
        elif paramType in [
            'Float',
            'Positive Float',
            'Fuzzy Value',
            'Float List',
            'Positive Float List',
            'Fuzzy Value List',
            ]:
            rtrn = [float(x) for x in paramVals]
        elif paramType in [
            'Truest Or Falsest'
            ]:
            if (param == '-1' or
                re.match(r'^[Ff][Aa][Ll][Ss][Ee][Ss][Tt]$',param)
                ):
                rtrn = ['Falsest']
            elif (param == '1' or
                re.match(r'^[Tt][Rr][Uu][Ee][Ss][Tt]$',param)
                ):
                rtrn = ['Truest']
            else:
                raise Exception(
                    'Programming error. Truest Or Falsest has value: {}\n'.format(inStr))

        else: # No conversion required
            rtrn = paramVals
        # if paramType in [...] elif...else
            
        # Convert to single value is type is not list
        if paramType.find('List') < 0:
            rtrn = rtrn[0]

        return rtrn

    # def ValFromParamByNm(self,paramNm):

    # Used to check validity of mptCmdStruct argument types
    def _IsParamType(self,inStr,inType):

        if re.match(r'.+ List$',inType):
            theType = inType.replace(' List','',1)
            if not re.match(r'\[.*\]',inStr): return False
            theStr = inStr.replace('[','').replace(']','')
        else:
            theStr = inStr
            theType = inType
            
        theStrs = theStr.split(',')
        if len(theStrs) == 0: return False

        for theStr in theStrs:
            if theType == 'Any':
                pass
            elif theType == 'File Name':
                if not re.match(r'([a-zA-Z]:[\\/]){0,1}[\w\\/\.\- ~]*\w+\s*$',theStr):
                    return False
            elif theType == 'Field Name':
                if not re.match(r'^[a-zA-Z][-\w]*$',theStr):
                    return False
            elif theType == 'Integer':
                if not re.match(r'^[+-]{0,1}[0-9]+$',theStr):
                    return False
            elif theType == 'Positive Integer':
                if not re.match(r'^[+]{0,1}^[0-9]$',theStr):
                    return False
                else:
                    if int(theStr) < 1:
                        return False
            elif theType == 'Float':
                if not re.match(r'^[+-]{0,1}([0-9]+\.*[0-9]*)$|(^[+-]{0,1}\.[0-9]+)$',theStr):
                    return False
            elif theType == 'Positive Float':
                if not re.match(r'^[+]{0,1}([0-9]+\.*[0-9]*)$|(^[+-]{0,1}\.[0-9]+)$',theStr):
                    return False
            elif theType == 'Fuzzy Value':
                if not re.match(r'^[+-]{0,1}([0-9]+\.*[0-9]*)$|(^[+-]{0,1}\.[0-9]+)$',theStr):
                    return False
                if not self.fuzzyMin <= float(theStr) <= self.fuzzyMax:
                    return False
            elif theType == 'Truest Or Falsest':
                if not (inStr == '-1' or
                    inStr == '1' or
                    re.match(r'^[Tt][Rr][Uu][Ee][Ss][Tt]$',inStr) or
                    re.match(r'^[Ff][Aa][Ll][Ss][Ee][Ss][Tt]$',inStr)):
                    return False                
            elif theType == 'Boolean':
                if not (inStr == 'True' or inStr == 'False'):
                    return False                
            elif theType == 'Data Type Desc':
                if not theStr in [
                    'Any',
                    'File Name',
                    'Field Name',
                    'Integer',
                    'Positive Integer',
                    'Float',
                    'Positive Float',
                    'Fuzzy Value',
                    'Fuzzy',
                    ]:
                    return False
            else:
                raise Exception(
                    '{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Class definition error.\n',
                        'Illegal parameter type in function descriptions: {}'.format(inType)
                        )
                    )
        # for theStr in theStrs:

        return True
    
    # def _IsParamType(self,inStr,type):

    def _InsureFuzzy(self,arr):
        
        # numpy has a function to do things in place. numpy.ma doesn't
        np.place(arr.data, arr.data > self.fuzzyMax, self.fuzzyMax)
        np.place(arr.data, arr.data < self.fuzzyMin, self.fuzzyMin)
        if isinstance(arr.mask,list):
            np.place(arr.data, arr.mask, arr.fill_value)
        
    # def _InsureFuzzy(self,arr):

    def _IsValidParamType(self,paramStr,paramTypes):

        rtrn = False
        if not isinstance(paramTypes,list): paramTypes = [paramTypes]
            
        for pType in paramTypes:
            if self._IsParamType(paramStr,pType):
                rtrn = True
                break
            
        return rtrn
    
    # def _IsValidParamType(self,paramStr,paramTypes):

    def SetParam(self,paramNm,value):
        
        # value must be string
        if paramNm in self.fxnDesc['ReqParams']:
            legalParamTypes = self.fxnDesc['ReqParams'][paramNm]
        elif paramNm in self.fxnDesc['OptParams']:
            legalParamTypes = self.fxnDesc['OptParams'][paramNm]
        else:
            raise Exception(
                '{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Trying to set non-existend parameter:\n',
                    '  Parameter: {}  Value: {}'.format(paramNm,value),
                    ),
                )

        if not isinstance(legalParamTypes,list): legalParamTypes = [legalParamTypes]

        if not self._IsValidParamType(value,legalParamTypes):
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid value for parameter:\n',
                    '  Parameter: {}  Value: {}'.format(paramNm,value),
                    '  Value must be one of:\n    {}'.format('\n    '.join(legalParamTypes)),
                    ),
                )

        self.mptCmdStruct['parsedCmd']['params'][paramNm] = cp.deepcopy(value)
        
    # def SetParam(self,paramNm,value):
        
    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldNames')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def DataType(self): return self.dataType
        
    def IsDataLayer(self): return self.isDataLayer

# class _MPilotEEMSParent(mpfp.MPilotFxnParent):
