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
from Convert_GDB_to_NetCDF import *
from django.conf import settings

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
        
        self.fxnDesc['ReqArgs'] = {
            'InFieldName':'Field Name'
            }
        self.fxnDesc['OptArgs'] = {
            'OutFileName':'File Name',
            'Metadata':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'XMin':'Float',
            'XMax':'Float',
            'YMin':'Float',
            'YMax':'Float',
            'Color':'Any'
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ArgToList('InFieldName')
        rtrn += self._ArgToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):
        
    def Exec(self,executedObjects):

        dataObj = executedObjects[self.ValFromArgByNm('InFieldName')]
        self._ValidateIsDataLayer(dataObj)

        outFNm = self.ArgByNm('OutFileName')

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        xMin = self.ValFromArgByNm('XMin')
        if xMin is None:
            if dataObj.DataType() == 'Fuzzy':
                xMin = self.fuzzyMin
            else:
                xMin = dataObj.ExecRslt().min()

        xMax = self.ValFromArgByNm('XMax')
        if xMax is None:
            if dataObj.DataType() == 'Fuzzy':
                xMax = self.fuzzyMax
            else:
                xMax = dataObj.ExecRslt().max()

        # YMax must be set if we are going to use y limits
        yMax = self.ValFromArgByNm('YMax')
        yMin = self.ValFromArgByNm('yMin')
        if yMax is not None:
            if yMin is None: yMin = 0.
            ax1.set_ylim(yMin,yMax)

        if self.ValFromArgByNm('Color') is not None:
            faceColor = self.ValFromArgByNm('Color')
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
        ax1.set_title('Distribution for {}'.format(self.ValFromArgByNm('InFieldName')))
        
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
        
        self.fxnDesc['ReqArgs'] = {
            'InFieldName':'Field Name',
            'OutFileName':'File Name',
            }
        self.fxnDesc['OptArgs'] = {
            'Metadata':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            'ColorMap':'Any',
            'Origin':'Any',
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ArgToList('InFieldName')
        rtrn += self._ArgToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):

    def Project(self, outFNm):

            input_basename = outFNm.replace('.png','')
            trans_tiff = input_basename + "_trans.tiff"
            warp_tiff = input_basename + "_warp.tiff"
            output_png = input_basename + ".png"

            extent = self.ArgByNm('Extent')
            epsg = self.ArgByNm('EPSG')

            # Convert the PNG to a spatially referenced Tif in it's native CRS
            os.system(settings.GDAL_BINARY_DIR + os.sep + "gdal_translate -a_ullr " + extent + " -a_srs EPSG:" + epsg + " " + outFNm + " " + trans_tiff )

            # Get the extent in Web Mercator from Ken's script. Eventually only want to do this step once.
            extent_tuple = extent.split(" ")
            extent_list_for_ken=[extent_tuple[0], extent_tuple[2], extent_tuple[3], extent_tuple[1]]
            extent_wm = getExtentInDifferentCRS(extent=extent_list_for_ken,epsg=int(epsg),to_epsg=3857)

            # Restructure the Web Mercator extent for input to GDAL
            print "extent_wm"
            print extent_wm
            extent_wm_string = str(extent_wm[0]) + " " + str(extent_wm[2]) + " " + str(extent_wm[1]) + " " + str(extent_wm[3])
            print extent_wm_string

            # Project the tif to Web Mercator using the extent from Ken's script above to trim the excess no data values.
            # Alignment issues crop up if this is step is not performed because the resulting PNG has a border of NoData whitespace.
            os.system(settings.GDAL_BINARY_DIR + os.sep + "gdalwarp -te " + extent_wm_string + " -s_srs EPSG:" + epsg + " -t_srs EPSG:3857 " + trans_tiff + " " + warp_tiff)
            #os.system("gdalwarp -s_srs EPSG:" + epsg + " -t_srs EPSG:3857 " + trans_tiff + " " + warp_tiff)

            src_ds = gdal.Open(warp_tiff)

            # Overwrite Matplotlib png
            driver.CreateCopy(output_png, src_ds,0)

            src_ds = None

            os.remove(trans_tiff)
            os.remove(warp_tiff)
        
    def Exec(self,executedObjects):

        dataObj = executedObjects[self.ValFromArgByNm('InFieldName')]
        self._ValidateIsDataLayer(dataObj)

        outFNm = self.ArgByNm('OutFileName')

        if dataObj.DataType() == 'Fuzzy':
            minVal = self.fuzzyMin
            maxVal = self.fuzzyMax
        else:
            minVal = dataObj.ExecRslt().min()
            maxVal = dataObj.ExecRslt().max()

        map_quality = self.ArgByNm('MapQuality')
        w = int(map_quality.split(',')[0])
        h = int(map_quality.split(',')[1])
        fig = plt.figure(figsize=(w,h))
        ax1 = fig.add_axes([0,0,1,1])
        ax1.axis('off')

        cmap = self.ValFromArgByNm('ColorMap')
        if cmap is None: cmap = 'RdYlBu_r'

        origin = self.ArgByNm('Origin') if self.ArgByNm('Origin') is not None else 'lower'

        norm = mpl.colors.Normalize(vmin=minVal,vmax=maxVal)

        myImg = ax1.imshow(
            dataObj.ExecRslt(),
            aspect='auto',
            norm=norm,
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

        # ax1.tick_args(
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

        # origin = self.ArgByNm('Origin') if self.ArgByNm('Origin') is not None else 'lower'
            
        # myImg = ax1.imshow(
        #     dataObj.ExecRslt(),
        #     aspect='auto',
        #     interpolation='nearest',
        #     origin=origin
        #     )

        # myImg.set_clim(minVal,maxVal)

        # cmap = self.ValFromArgByNm('ColorMap')
        # if cmap is None: cmap = 'RdYlBu'

        # myImg.set_cmap(cmap)

        # # We don't want a title
        # # ax1.set_title('{}'.format(self.ValFromArgByNm('InFieldName')))

        # # if DoSeparate key is not specified or is false, it will be printed
        
        # if not self.ArgByNm('DoSeparateKey') == 'True':
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
        
        self.fxnDesc['ReqArgs'] = {
            'XFieldName':'Field Name',
            'YFieldName':'Field Name'
            }
        self.fxnDesc['OptArgs'] = {
            'OutFileName':'File Name',
            'Metadata':'Any',
            'PrecursorFieldNames':['Field Name','Field Name List'],
            }
        
    # _SetFxnDesc(self):

    def DependencyNms(self):
        
        rtrn = self._ArgToList('XFieldName') + self._ArgToList('YFieldName')
        rtrn += self._ArgToList('PrecursorFieldNames')
        return rtrn
    
    # def DependencyNms(self):
        
    def Exec(self,executedObjects):
        
        xDataObj = executedObjects[self.ValFromArgByNm('XFieldName')]
        yDataObj = executedObjects[self.ValFromArgByNm('YFieldName')]
        self._ValidateIsDataLayer(xDataObj)
        self._ValidateIsDataLayer(yDataObj)

        outFNm = self.ArgByNm('OutFileName')

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

        ax1.set_xlabel(self.ValFromArgByNm('XFieldName'))
        ax1.set_ylabel(self.ValFromArgByNm('YFieldName'))

        ax1.set_xlim(xMinVal,xMaxVal)
        ax1.set_ylim(yMinVal,yMaxVal)
        
        ax1.set_title('{} vs {}'.format(
            self.ValFromArgByNm('YFieldName'),
            self.ValFromArgByNm('XFieldName')
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
