from __future__ import division
import MPilotEEMSFxnParent as mpefp
import numpy as np
import copy as cp

# Conversion to fuzzy operations

class CvtToFuzzy(mpefp._MPilotEEMSFxnParent):
    
    def __init__(self,mptCmdStruct=None):
        
        super(CvtToFuzzy, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        # description of command for validation and info display

        self.fxnDesc['DisplayName'] = 'Convert to Fuzzy'
        self.fxnDesc['ShortDesc'] = 'Converts input values into fuzzy values using linear interpolation'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name'
            }
        self.fxnDesc['OptParams'] = {
            'TrueThreshold':'Float',
            'FalseThreshold':'Float',
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'Direction':'Any',
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        inFldNm = self.ParamByNm('InFieldName')
        inObj = executedObjects[inFldNm]
        
        self._ValidateProgDataType(
            inFldNm,
            inObj,
            [
                'Float',
                'Positive Float',
                'Integer',
                'Positive Integer',
                'Fuzzy'
                ]
            )

        self._ValidateIsDataLayer(inObj)
        
        inArr = inObj.ExecRslt()

        if 'Direction' in self.Params():
            if self.ParamByNm('Direction') not in ['LowToHigh','HighToLow']:
                raise Exception(
                    '{}{}{}{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Invalid Direction specified in command:\n',
                        '  Direction must be one of:\n',
                        '    LowToHigh\n',
                        '    HighToLow\n',
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],
                            self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

        # if 'Direction' in self.Params():

        if 'FalseThreshold' in self.Params():
            falseThresh = self.ParamByNm('FalseThreshold')
        elif 'Direction' in self.Params():
            if self.ParamByNm('Direction') in ['LowToHigh']:
                falseThresh =  inArr.min()
            elif self.ParamByNm('Direction') in ['HighToLow']:
                falseThresh =  inArr.max()
                
        if 'TrueThreshold' in self.Params():
            trueThresh = self.ParamByNm('TrueThreshold')
        elif 'Direction' in self.Params():
            if self.ParamByNm('Direction') in ['LowToHigh']:
                trueThresh =  inArr.max()
            elif self.ParamByNm('Direction') in ['HighToLow']:
                trueThresh =  inArr.min()

        if trueThresh == falseThresh:
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'True and False must not be equal:\n',
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

        x1 = float(trueThresh)
        x2 = float(falseThresh)
        y1 = self.fuzzyMax
        y2 = self.fuzzyMin

        # linear conversion
        self.execRslt = (inArr - x1) * (y2-y1)/(x2-x1) + y1
        
        # bring back values to fuzzy limits
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class CvtToFuzzy(mpefp._MPilotEEMSFxnParent):

class CvtToFuzzyCat(mpefp._MPilotEEMSFxnParent):
    
    def __init__(self,mptCmdStruct=None):
        
        super(CvtToFuzzyCat, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        # description of command for validation and info display

        self.fxnDesc['DisplayName'] = 'Convert to Fuzzy by Category'
        self.fxnDesc['ShortDesc'] = 'Converts integer input values into fuzzy based on user specification.'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name',
            'RawValues':['Integer List'],
            'FuzzyValues':['Fuzzy Value List'],
            'DefaultFuzzyValue':'Fuzzy Value',
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        inFldNm = self.ParamByNm('InFieldName')
        inObj = executedObjects[inFldNm]
        
        # Result starts with a copy of the first input field, then add the rest
        # and divide by the number of them
        
        self._ValidateIsDataLayer(inObj)
        self._ValidateProgDataType(
            inFldNm,
            inObj,
            [
                'Integer',
                'Positive Integer',
                ]
            )

        self._ValidateEqualListLens(['FuzzyValues','RawValues'])
        self._ValidateParamListItemsUnique('RawValues')
            
        inArr = inObj.ExecRslt()
        
        self.execRslt = np.ma.empty(
            inArr.shape,
            dtype=float
            )

        self.execRslt.data[:] = float(self.ParamByNm('DefaultFuzzyValue'))

        fuzzyVals = self.ValFromParamByNm('FuzzyValues')
        rawVals = self.ValFromParamByNm('RawValues')
        
        for rawVal,fuzzyVal in zip(rawVals,fuzzyVals):
            np.place(self.execRslt.data,inArr.data == rawVal,fuzzyVal)

        self.execRslt.mask = cp.deepcopy(inArr.mask)

        # bring back values to fuzzy limits
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class CvtToFuzzyCat(mpefp._MPilotEEMSFxnParent):

class CvtToFuzzyCurve(mpefp._MPilotEEMSFxnParent):
   
    def __init__(self,mptCmdStruct=None):
        
        super(CvtToFuzzyCurve, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        # description of command for validation and info display

        self.fxnDesc['DisplayName'] = 'Convert to Fuzzy Curve'
        self.fxnDesc['ShortDesc'] = 'Converts input values into fuzzy based on user-defined curve.'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name',
            'RawValues':['Float List'],
            'FuzzyValues':['Fuzzy Value List'],
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        inFldNm = self.ParamByNm('InFieldName')
        inObj = executedObjects[inFldNm]
        
        # Result starts with a copy of the first input field, then add the rest
        # and divide by the number of them
        
        self._ValidateIsDataLayer(inObj)
        self._ValidateProgDataType(
            inFldNm,
            inObj,
            [
                'Float',
                'Positive Float',
                'Integer',
                'Positive Integer',
            ]
            )
        self._ValidateEqualListLens(['FuzzyValues','RawValues'])
        self._ValidateParamListItemsUnique('RawValues')
            
        inArr = inObj.ExecRslt()

        self.execRslt = np.ma.empty(
            inArr.shape,
            dtype=float
            )

        fuzzyVals = self.ValFromParamByNm('FuzzyValues')
        rawVals = self.ValFromParamByNm('RawValues')

        zippedPoints = sorted(zip(rawVals,fuzzyVals))

        # Set the fuzzy values corresponding to the raw values less
        # than the lowest raw value to the corresponding fuzzy value
        np.place(self.execRslt.data,inArr <= zippedPoints[0][0],zippedPoints[0][1])

        # Iterate over the line segments that approximate the curve
        # and assign fuzzy values.
        for ndx in range(1,len(zippedPoints)):

            # Linear equation formula for line segment
            m = (zippedPoints[ndx][1] - zippedPoints[ndx-1][1]) / \
            (zippedPoints[ndx][0] - zippedPoints[ndx-1][0])
            
            b = zippedPoints[ndx-1][1] - m * zippedPoints[ndx-1][0]

            whereNdxs = np.where(
                np.logical_and(
                    inArr.data > zippedPoints[ndx-1][0],
                    inArr.data <= zippedPoints[ndx][0]
                    )
                )

            self.execRslt.data[whereNdxs] = m * inArr.data[whereNdxs] + b
            
        # Set the fuzzy values corresponding to the raw values greater
        # than the highest raw value to the corresponding fuzzy value
        np.place(self.execRslt.data,inArr > zippedPoints[-1][0],zippedPoints[-1][1])
        
        self.execRslt.mask = cp.deepcopy(inArr.mask)

        # bring back values to fuzzy limits
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):

# class CvtToFuzzyCurve(mpefp._MPilotEEMSFxnParent):

# Fuzzy logic operations

class FuzzyUnion(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyUnion, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        self.fxnDesc['DisplayName'] = 'Fuzzy Union'
        self.fxnDesc['ShortDesc'] = 'Takes the fuzzy Union (mean) of fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name','Field Name List']
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        self._ValidateListLen('InFldNms',1)
        fldNms = self._ParamToList('InFieldNames')
        
        # Result starts with a copy of the first input field, then add the rest
        # and divide by the number of them
        
        self._ValidateProgDataType(fldNms[0],executedObjects[fldNms[0]],'Fuzzy')
        self.execRslt = cp.deepcopy(executedObjects[fldNms[0]].ExecRslt())
        
        for fldNm in fldNms[1:]:
            self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
            self.execRslt += executedObjects[fldNm].ExecRslt()

        self.execRslt = self.execRslt / float(len(fldNms))
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class FuzzyUnion(mpefp._MPilotEEMSFxnParent):    

class FuzzyWeightedUnion(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyWeightedUnion, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        self.fxnDesc['DisplayName'] = 'Fuzzy Weighted Union'
        self.fxnDesc['ShortDesc'] = 'Takes the weighted fuzzy Union (mean) of fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name List'],
            'Weights':['Float List']            
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):
    
    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        self._ValidateListLen('InFldNms',1)
        self._ValidateEqualListLens(['InFieldNames','Weights'])
        
        fldNms = self._ParamToList('InFieldNames')
        wts = self.ValFromParamByNm('Weights')
        
        # Result starts with a copy of the first input field, then add the rest
        # and divide by the number of them
        
        self._ValidateProgDataType(fldNms[0],executedObjects[fldNms[0]],'Fuzzy')
        self.execRslt = cp.deepcopy(executedObjects[fldNms[0]].ExecRslt()) * wts[0]
        
        for wt,fldNm in zip(wts,fldNms)[1:]:
            self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
            self.execRslt += executedObjects[fldNm].ExecRslt() * wt

        self.execRslt = self.execRslt / sum(wts)
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class FuzzyWeightedUnion(mpefp._MPilotEEMSFxnParent):    

class FuzzySelectedUnion(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzySelectedUnion, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        self.fxnDesc['DisplayName'] = 'Fuzzy Selected Union'
        self.fxnDesc['ShortDesc'] = 'Takes the fuzzy Union (mean) of N Truest or Falsest fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'

        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name','Field Name List'],
            'TruestOrFalsest':'Truest Or Falsest',
            'NumberToConsider':'Positive Integer'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def Exec(self,executedObjects):
        # executedObjects is a dictionary of executed MPilot function objects
        
        fldNms = self._ParamToList('InFieldNames')
        numToCnsdr = self.ValFromParamByNm('NumberToConsider')
        
        if len(fldNms) < numToCnsdr:
            raise Exception(
                '{}{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Number of InFieldNames must be greater than or equal to NumberToConsider:\n',
                    'Number of InFieldNames: {}  NumberToConsider: {}\n'.format(
                        len(fldNms),
                        numToCnsdr,
                        ),
                    'File: {}  Line number: {}\n'.format(
                        self.mptCmdStruct['cmdFileNm'],
                        self.mptCmdStruct['lineNo']
                        ),
                    'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                ),
            )

        # Create a stacked array with layers from input arrays, sort it, and use
        # that to calculate fuzzy xor. There is no np.ma.stacked, so the masks have
        # to be handled separately from the data. Note we are building the maximal
        # mask from all the inputs before broadcasting it to the size of the stacked
        # array. There are some issues with getting stackedArr to be writable. The
        # below code works.

        tmpMask = executedObjects[fldNms[0]].ExecRslt().mask
        for fldNm in fldNms[1:]:
            tmpMask = np.logical_or(tmpMask,executedObjects[fldNm].ExecRslt().mask)

        stackedArr = np.ma.array(
            np.stack([executedObjects[fldNm].ExecRslt().data for fldNm in fldNms]),
            mask = cp.deepcopy(
                np.broadcast_to(
                    tmpMask,
                    [len(fldNms)]+list(executedObjects[fldNm].ExecRslt().shape)
                    )
                )
            )
            
        stackedArr.sort(axis=0,kind='heapsort')

        if self.ValFromParamByNm('TruestOrFalsest') == 'Truest':
            self.execRslt = np.ma.mean(stackedArr[-numToCnsdr:],axis=0)
        else:
            self.execRslt = np.ma.mean(stackedArr[0:numToCnsdr],axis=0)
            
        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class FuzzySelectedUnion(mpefp._MPilotEEMSFxnParent):

class FuzzyOr(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyOr, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):

        self.fxnDesc['DisplayName'] = 'Fuzzy Or'
        self.fxnDesc['ShortDesc'] = 'Takes the fuzzy Or (maximum) of fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name','Field Name List']
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def Exec(self,executedObjects):

        self._ValidateListLen('InFldNms',1)
        fldNms = self._ParamToList('InFieldNames')
        
        # Traverse inputs and take maximum
        self._ValidateProgDataType(fldNms[0],executedObjects[fldNms[0]],'Fuzzy')
        self.execRslt = cp.deepcopy(executedObjects[fldNms[0]].ExecRslt())
        
        for fldNm in fldNms[1:]:
            self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
            self.execRslt = np.ma.maximum(self.execRslt,executedObjects[fldNm].ExecRslt())

        self.execRslt = self.execRslt
        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):

# class FuzzyOr(mpefp._MPilotEEMSFxnParent):

class FuzzyAnd(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyAnd, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'Fuzzy And'
        self.fxnDesc['ShortDesc'] = 'Takes the fuzzy And (minimum) of fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name','Field Name List']
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def Exec(self,executedObjects):

        self._ValidateListLen('InFldNms',1)
        fldNms = self._ParamToList('InFieldNames')
        
        # Traverse inputs and take maximum
        self._ValidateProgDataType(fldNms[0],executedObjects[fldNms[0]],'Fuzzy')
        self.execRslt = cp.deepcopy(executedObjects[fldNms[0]].ExecRslt())

        for fldNm in fldNms[1:]:
            self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
            self.execRslt = np.ma.minimum(self.execRslt,executedObjects[fldNm].ExecRslt())

        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class FuzzyAnd(mpefp._MPilotEEMSFxnParent):

class FuzzyXOr(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyXOr, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'Fuzzy XOr'
        self.fxnDesc['ShortDesc'] = 'Computes Fuzzy XOr: Truest - (Truest - 2nd Truest) * (2nd Truest - full False)/(Truest - full False)'
        self.fxnDesc['ReturnType'] = 'Fuzzy'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldNames':['Field Name List']
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def Exec(self,executedObjects):

        self._ValidateListLen('InFieldNames',2)
        fldNms = self._ParamToList('InFieldNames')
        
        # Validate inputs
        for fldNm in fldNms:
            self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
        
        # Create a stacked array with layers from input arrays, sort it, and use
        # that to calculate fuzzy xor. There is no np.ma.stacked, so the masks have
        # to be handled separately from the data. Note we are building the maximal
        # mask from all the inputs before broadcasting it to the size of the stacked
        # array. There are some issues with getting stackedArr to be writable. The
        # below code works.

        tmpMask = executedObjects[fldNms[0]].ExecRslt().mask
        for fldNm in fldNms[1:]:
            tmpMask = np.logical_or(tmpMask,executedObjects[fldNm].ExecRslt().mask)
            
        stackedArr = np.ma.array(
            np.stack([executedObjects[fldNm].ExecRslt().data for fldNm in fldNms]),
            mask = cp.deepcopy(
                np.broadcast_to(
                    tmpMask,
                    [len(fldNms)]+list(executedObjects[fldNm].ExecRslt().shape)
                    )
                )
            )
            
        stackedArr.sort(axis=0,kind='heapsort')
        
        self.execRslt = np.ma.where(
            stackedArr[-1] <= self.fuzzyMin,
            self.fuzzyMin,
            stackedArr[-1] - \
                (stackedArr[-1] - stackedArr[-2]) * \
                (stackedArr[-2] - self.fuzzyMin) / \
                (stackedArr[-1] - self.fuzzyMin)
            )

        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):
    
# class FuzzyXOr(mpefp._MPilotEEMSFxnParent):

class FuzzyNot(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(FuzzyNot, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Fuzzy',
            isDataLayer = True
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'Fuzzy Not'
        self.fxnDesc['ShortDesc'] = 'Takes the fuzzy And (minimum) of fuzzy input variables'
        self.fxnDesc['ReturnType'] = 'Fuzzy'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
    
    # def DependencyNms(self):

    def Exec(self,executedObjects):

        self._ValidateListLen('InFldNms',1)
        fldNm = self._ParamToList('InFieldName')
        
        self._ValidateProgDataType(fldNm,executedObjects[fldNm],'Fuzzy')
        self.execRslt = -executedObjects[fldNm].ExecRslt()

        self._InsureFuzzy(self.execRslt)

        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):

# class FuzzyNot(mpefp._MPilotEEMSFxnParent):    
    
