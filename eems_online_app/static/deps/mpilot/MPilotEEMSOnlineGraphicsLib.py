from __future__ import division
import MPilotEEMSFxnParent as mpefp
import numpy as np
import copy as cp
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import tempfile as tf
import os
import re
import gc
import gdal
driver = gdal.GetDriverByName("PNG")

class HistoDist(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(HistoDist, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Boolean',
            isDataLayer = False
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'HistoDist'
        self.fxnDesc['ShortDesc'] = 'Creates a histogram for a variable\'s distribution'
        self.fxnDesc['ReturnType'] = 'Boolean'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'XMin':'Float',
            'XMax':'Float',
            'YMin':'Float',
            'YMax':'Float',
            'Color':'Any'
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):
        
    def Exec(self,executedObjects):

        dataObj = executedObjects[self.ValFromParamByNm('InFieldName')]
        self._ValidateIsDataLayer(dataObj)

        outFNm = self.ParamByNm('OutFileName')

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        xMin = self.ValFromParamByNm('XMin')
        if xMin is None:
            if dataObj.DataType() == 'Fuzzy':
                xMin = self.fuzzyMin
            else:
                xMin = dataObj.ExecRslt().min()

        xMax = self.ValFromParamByNm('XMax')
        if xMax is None:
            if dataObj.DataType() == 'Fuzzy':
                xMax = self.fuzzyMax
            else:
                xMax = dataObj.ExecRslt().max()

        # YMax must be set if we are going to use y limits
        yMax = self.ValFromParamByNm('YMax')
        yMin = self.ValFromParamByNm('yMin')
        if yMax is not None:
            if yMin is None: yMin = 0.
            ax1.set_ylim(yMin,yMax)

        if self.ValFromParamByNm('Color') is not None:
            faceColor = self.ValFromParamByNm('Color')
        else:
            faceColor = 'grey'

            hist = plt.hist(
                dataObj.ExecRslt().ravel().compressed(),
                bins=50,
                range=(xMin,xMax),
                facecolor = faceColor,
            )
        ax1.set_xlabel('Value')
        ax1.set_ylabel('Count')
        ax1.set_title('Distribution for {}'.format(self.ValFromParamByNm('InFieldName')))
        
        if outFNm is None:
            outFNm = tf.mktemp(suffix='.png')
            plt.savefig(outFNm)
            os.system('open -a Preview {}'.format(outFNm))

        else:
            plt.savefig(outFNm)
        
        self.execRslt = True
        
        executedObjects[self.RsltNm()] = self
        
        plt.close(fig) # fig must be closed to get it out of memory
        
    # def Exec(self,executedObjects):
    
# class HistoDist(mpefp._MPilotEEMSFxnParent):

class RenderLayer(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(RenderLayer, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Boolean',
            isDataLayer = False
            )
        self.doSeparateKey = False

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'RenderLayer'
        self.fxnDesc['ShortDesc'] = 'Renders a layer'
        self.fxnDesc['ReturnType'] = 'Boolean'
        
        self.fxnDesc['ReqParams'] = {
            'InFieldName':'Field Name',
            'OutFileName':'File Name',
            }
        self.fxnDesc['OptParams'] = {
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'ColorMap':'Any',
            'Origin':'Any',
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('InFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Project(self, outFNm):

            input_basename = outFNm.replace('.png','')
            trans_tiff = input_basename + "_trans.tiff"
            warp_tiff = input_basename + "_warp.tiff"
            output_png = input_basename + ".png"

            extent = self.ParamByNm('Extent')
            epsg = self.ParamByNm('EPSG')

            os.system("gdal_translate -a_ullr " + extent + " -a_srs EPSG:" + epsg + " " + outFNm + " " + trans_tiff )

            os.system("gdalwarp -s_srs EPSG:" + epsg + " -t_srs EPSG:3857 " +  trans_tiff + " " + warp_tiff)

            src_ds = gdal.Open(warp_tiff)

            # Overwrite Matplotlib png
            driver.CreateCopy(output_png, src_ds,0)

            src_ds = None

            os.remove(trans_tiff)
            os.remove(warp_tiff)
        
    def Exec(self,executedObjects):

        dataObj = executedObjects[self.ValFromParamByNm('InFieldName')]
        self._ValidateIsDataLayer(dataObj)

        outFNm = self.ParamByNm('OutFileName')

        if dataObj.DataType() == 'Fuzzy':
            minVal = self.fuzzyMin
            maxVal = self.fuzzyMax
        else:
            minVal = dataObj.ExecRslt().min()
            maxVal = dataObj.ExecRslt().max()

        fig = plt.figure(figsize=(24,29))
        ax1 = fig.add_axes([0,0,1,1])
        ax1.axis('off')

        cmap = self.ValFromParamByNm('ColorMap')
        if cmap is None: cmap = 'RdYlBu_r'

        origin = self.ParamByNm('Origin') if self.ParamByNm('Origin') is not None else 'lower'

        myImg = ax1.imshow(
            dataObj.ExecRslt(),
            aspect='auto',
            interpolation='nearest',
            origin=origin
            )

        myImg.set_cmap(cmap)

        plt.gca().invert_yaxis()
        plt.savefig(outFNm, transparent=True)
        plt.close()
        gc.collect()
        plt.clf()

        # Project MatPlotLib png to Web Mercator
        self.Project(outFNm)

        # now the key
        fig = plt.figure(figsize=(8,1))
        ax1 = fig.add_axes([0.02,0.3,0.96,0.7])
        norm = mpl.colors.Normalize(vmin=minVal,vmax=maxVal)
        cb = mpl.colorbar.ColorbarBase(
            ax1,
            cmap=cmap,
            norm=norm,
            orientation='horizontal'
            )

        # Add string _key before the extension on the outfile name
        outFNm = re.sub(r'(\.[^\.]+)$',r'_key\1',outFNm)
        
        plt.savefig(outFNm)
        plt.close()
        gc.collect()

        # ax1 = fig.add_subplot(111)

        # if dataObj.DataType() == 'Fuzzy':
        #     minVal = self.fuzzyMin
        #     maxVal = self.fuzzyMax
        # else:
        #     minVal = dataObj.ExecRslt().min()
        #     maxVal = dataObj.ExecRslt().max()

        # ax1.tick_params(
        #         axis='both',
        #         which='both',
        #         bottom=False,
        #         top=False,
        #         left=False,
        #         right=False,
        #         labelbottom=False,
        #         labeltop=False,
        #         labelleft=False,
        #         labelright=False
        #         )

        # origin = self.ParamByNm('Origin') if self.ParamByNm('Origin') is not None else 'lower'
            
        # myImg = ax1.imshow(
        #     dataObj.ExecRslt(),
        #     aspect='auto',
        #     interpolation='nearest',
        #     origin=origin
        #     )

        # myImg.set_clim(minVal,maxVal)

        # cmap = self.ValFromParamByNm('ColorMap')
        # if cmap is None: cmap = 'RdYlBu'

        # myImg.set_cmap(cmap)

        # # We don't want a title
        # # ax1.set_title('{}'.format(self.ValFromParamByNm('InFieldName')))

        # # if DoSeparate key is not specified or is false, it will be printed
        
        # if not self.ParamByNm('DoSeparateKey') == 'True':
        #     cbar = fig.colorbar(myImg)
        
        # plt.savefig(outFNm)
        
        # self.execRslt = True
        
        # executedObjects[self.RsltNm()] = self

        # plt.close(fig) # fig must be closed to get it out of memory

    # def Exec(self,executedObjects):

# class RenderLayer(mpefp._MPilotEEMSFxnParent):


class ScatterXY(mpefp._MPilotEEMSFxnParent):

    def __init__(self,mptCmdStruct=None):

        super(ScatterXY, self).__init__(
            mptCmdStruct=mptCmdStruct,
            dataType='Boolean',
            isDataLayer = False
            )

    # def __init__(self,mptCmdStruct=None):

    def _SetFxnDesc(self):
        
        self.fxnDesc['DisplayName'] = 'ScatterXY'
        self.fxnDesc['ShortDesc'] = 'Creates a scatter plot for two fields'
        self.fxnDesc['ReturnType'] = 'Boolean'
        
        self.fxnDesc['ReqParams'] = {
            'XFieldName':'Field Name',
            'YFieldName':'Field Name'
            }
        self.fxnDesc['OptParams'] = {
            'OutFileName':'File Name',
            'MetaData':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ParamToList('XFieldName') + self._ParamToList('YFieldName')
        rtrn += self._ParamToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):
        
    def Exec(self,executedObjects):
        
        xDataObj = executedObjects[self.ValFromParamByNm('XFieldName')]
        yDataObj = executedObjects[self.ValFromParamByNm('YFieldName')]
        self._ValidateIsDataLayer(xDataObj)
        self._ValidateIsDataLayer(yDataObj)

        outFNm = self.ParamByNm('OutFileName')

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        if xDataObj.DataType() == 'Fuzzy':
            xMinVal = self.fuzzyMin
            xMaxVal = self.fuzzyMax
        else:
            xMinVal = xDataObj.ExecRslt().min()
            xMaxVal = xDataObj.ExecRslt().max()

        if yDataObj.DataType() == 'Fuzzy':
            yMinVal = self.fuzzyMin
            yMaxVal = self.fuzzyMax
        else:
            yMinVal = yDataObj.ExecRslt().min()
            yMaxVal = yDataObj.ExecRslt().max()

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        ax1.set_xlabel(self.ValFromParamByNm('XFieldName'))
        ax1.set_ylabel(self.ValFromParamByNm('YFieldName'))

        ax1.set_xlim(xMinVal,xMaxVal)
        ax1.set_ylim(yMinVal,yMaxVal)
        
        ax1.set_title('{} vs {}'.format(
            self.ValFromParamByNm('YFieldName'),
            self.ValFromParamByNm('XFieldName')
            )
            )

        myWhere = np.logical_or(
            xDataObj.ExecRslt().mask == False,
            yDataObj.ExecRslt().mask == False
            )

        # make the scatter plot
        plt.scatter(
            xDataObj.ExecRslt()[myWhere].ravel(),
            yDataObj.ExecRslt()[myWhere].ravel(),
            c='r',
            lw=0,
            marker='o',
            s=1,
            alpha=0.1
            )
                    
        if outFNm is None:
            outFNm = tf.mktemp(suffix='.png')
            plt.savefig(outFNm)
            os.system('open -a Preview {}'.format(outFNm))

        else:
            plt.savefig(outFNm)
        
        self.execRslt = True
        
        executedObjects[self.RsltNm()] = self
        
        plt.close(fig) # fig must be closed to get it out of memory

    # def Exec(self,executedObjects):

# class ScatterXY(mpefp._MPilotEEMSFxnParent):
