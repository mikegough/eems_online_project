# EEMS I/O NetCDF Command classes for MPilot framework
#
# File Log:
# 2016.07.27 - tjs
#  First draft

import MPilotEEMSFxnParent as mpefp
import numpy as np
import netCDF4 as nc4
from scipy.io import netcdf
import copy as cp

class EEMSRead(mpefp._MPilotEEMSFxnParent):

    def __init__(
        self,
        mptCmdStruct=None,
        dataType='Float',
        isDataLayer=False
        ):

        self.mptCmdStruct = mptCmdStruct

        if mptCmdStruct is not None:
            if self.ParamByNm('DataType') is not None:
                dataType = self.ParamByNm('DataType')

        super(EEMSRead, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType=dataType,
            isDataLayer=True
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        self.fxnDesc['DisplayName'] = 'EEMSRead'
        self.fxnDesc['ShortDesc'] = 'Reads a variable from a file, converting floats to nearest int when necessary.'
        self.fxnDesc['ReturnType'] = ['Fuzzy','Float','Positive Float','Integer','Positive Integer']

        self.fxnDesc['ReqParams'] = {
            'InFileName':'File Name',
            'InFieldName':'Field Name'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'MissingValue':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'DataType':'Data Type Desc',
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):
    
    def Exec(self,executedObjects):
        
        with nc4.Dataset(self.ParamByNm('InFileName'),'r') as inDS:
            if self.ParamByNm('InFieldName') not in inDS.variables:
                raise Exception(
                    '{}{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Read failure for file: {}\n'.format(self.ParamByNm('InFileName')),
                        '  Variable not in file: {}\n'.format(self.ParamByNm('InFieldName')),
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],
                            self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

            inV = inDS.variables[self.ParamByNm('InFieldName')]
            
            if isinstance(inV[:],np.ma.core.MaskedArray):
                newMask = cp.deepcopy(inV[:].mask)
            else:
                newMask = False

            if self.dataType in ['Integer']:
                newDType = np.int
            elif self.dataType in ['Positive Integer']:
                newDType = np.uint
            else:
                newDType = np.float64

            if inV[:].dtype == np.float64 and newDType in [np.int,np.uint]:
                self.execRslt = np.ma.array(
                    inV[:].data + 0.5, # result rounds to nearest int
                    mask=newMask,
                    dtype=newDType,
                    )
            else:
                self.execRslt = np.ma.array(
                    cp.deepcopy(inV[:].data),
                    mask=newMask,
                    dtype=newDType
                    )

            # Check to make sure the data is valid and constrain fuzzy

            msg = None
            if self.dataType == 'Positive Integer':
                
                if inV[:].max() < 0.: msg = 'Positive Integer data has negative value'
                    
            elif self.dataType == 'Positive Float':
                
                if inV[:].max() < 0.: msg = 'Positive Float data has negative value'
                    
            elif self.dataType == 'Fuzzy':
                
                fzPad = 0.01 * (self.fuzzyMax - self.fuzzyMin)
                
                if inV[:].max() >  self.fuzzyMax + fzPad or \
                    inV[:].min() <  self.fuzzyMin - fzPad:

                    msg = '{}{}'.format(
                        'Fuzzy data outside of fuzzy range: {} {}\n'.format(
                            self.fuzzyMin,self.fuzzyMax
                            ),
                        'Minimum and maximum values: {}  {}\n'.format(
                            inV[:].min(),
                            inV[:].max()
                            )
                        )
                else:

                    self._InsureFuzzy(self.execRslt)

            # if self.dataType == 'Positive Integer':
            
            if msg is not None:
                raise Exception(
                    '{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Invalid data for data type: {}\n'.format(self.dataType),
                        '  {}\n'.format(msg),
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],
                            self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )

        
            self.execRslt.soften_mask()

            # Make the missing value missing
            if self.ParamExists('MissingValue'):
                if self.execRslt.mask.dtype in [int]:
                    missingVal = int(self.ValFromParamByNm('MissingValue'))                    
                else:
                    missingVal = float(self.ValFromParamByNm('MissingValue'))                    
                
                if isinstance(self.execRslt.mask,np.ndarray):
                    self.execRslt.mask = np.where(
                        self.execRslt.data == missingVal,
                        True,
                        inV[:].mask
                        )
                else:
                    self.execRslt.mask = np.ma.where(
                        self.execRslt == missingVal,
                        True,
                        False
                        )
                    
                # if isinstance(self.execRslt.mask,np.ndarray):
                
                self.execRslt.data[np.where(self.execRslt.mask)] = self.execRslt.fill_value
                
            # if self.ParamExists('MissingValue'):
                
        # Check shape versus shape of any object with a data layer
        # (i.e. data layer is masked array)

        for exObjKey,exObjVal in executedObjects.items():
            # Skip results that are not data
            if not exObjVal.IsDataLayer():
                continue
            
            if exObjVal.ExecRslt().shape != self.execRslt.shape:
                raise Exception(
                    '{}{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Input variable shape did not match existing data:\n',
                        '  Input file name, field name, and shape: {}  {}'.format(
                            self.ParamByNm('InFileName'),
                            self.ParamByNm('InFieldName'),
                            self.execRslt.shape
                            ),
                        '  Existing field name and shape: {}  {}'.format(
                            exObjKey,
                            exObjVal.ExecRslt().shape
                            ),
                        'File: {}  Line number: {}\n'.format(
                            self.mptCmdStruct['cmdFileNm'],
                            self.mptCmdStruct['lineNo']
                            ),
                        'Full command:\n{}\n'.format(self.mptCmdStruct['rawCmdStr'])
                    ),
                )
            else:
                break
            
        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):

# class EEMSRead(mpefp._MPilotEEMSFxnParent)        

class EEMSWrite(mpefp._MPilotEEMSFxnParent):

    def __init__(
        self,
        mptCmdStruct=None
        ):

        super(EEMSWrite, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Boolean',
            isDataLayer=False
            )

    # def __init__(self,mptCmdStruct=None):
    
    def _SetFxnDesc(self):
        # description of command used for validation and
        # information display Each Pilot fxn command should have its
        # own description

        self.fxnDesc['DisplayName'] = 'EEMSWrite'
        self.fxnDesc['ShortDesc'] = 'Writes one or more file'
        self.fxnDesc['ReturnType'] = 'Boolean'

        self.fxnDesc['ReqParams'] = {
            'OutFileName':'File Name',
            'OutFieldNames':['Field Name','Field Name List'],
            'DimensionFileName':'File Name',
            'DimensionFieldName':'Field Name',
            }
        self.fxnDesc['OptParams'] = {
            'PrecursorFieldNames':['Field Name','Field Name List']
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('OutFieldNames')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Exec(self,executedObjects):

        outFldNms = self._ParamToList('OutFieldNames')

        # Check that all output variables are data layers
        for outFldNm in outFldNms:
            self._ValidateIsDataLayer(executedObjects[outFldNm])

        with nc4.Dataset(self.ParamByNm('OutFileName'),'w') as outDS:
            
            # Prep the dimensions in the ouput file
            with nc4.Dataset(self.ParamByNm('DimensionFileName')) as dimDS:
                dimNms = dimDS[self.ParamByNm('DimensionFieldName')].dimensions
                for dimNm in dimNms:
                    inDimV = dimDS.variables[dimNm]
                    outDS.createDimension(dimNm,inDimV.size)
                    outDimV = outDS.createVariable(dimNm,inDimV.dtype,[dimNm])
                    for attNm in dir(inDimV):
                        if attNm not in dir(outDimV):
                            setattr(outDimV,attNm,getattr(inDimV,attNm))
                    outDimV[:] = inDimV[:]
            # with Dataset(self.ParamByNm('DimensionFileName')) as dimDS:

            
            # Write those bad boys
            for outFldNm in outFldNms:
                outV = outDS.createVariable(
                    outFldNm,
                    executedObjects[outFldNm].ExecRslt().dtype.char,
                    dimNms,
                    fill_value = executedObjects[outFldNm].ExecRslt().fill_value
                    )
                outV[:] = cp.deepcopy(executedObjects[outFldNm].ExecRslt())
            # for outFldNm in outFldNms:
        
        self.execRslt = True
        executedObjects[self.RsltNm()] = self
        
    # def Exec(self,executedObjects):

# class EEMSWrite(mpefp._MPilotEEMSFxnParent)        
