import ogr
import osr
import numpy as np
import netCDF4
import gdal

def getEPSGFromNCfile(ncfile):
    with netCDF4.Dataset(ncfile, 'r') as nc:
        wkt = nc.variables['crs'].getncattr('crs_wkt')
        srs = osr.SpatialReference()
        srs.ImportFromWkt(wkt)
        epsg = srs.GetAttrValue("AUTHORITY", 1)
        return int(epsg)

def getWktFromNCFile(ncfile):
  with netCDF4.Dataset(ncfile, 'r') as nc:
    return nc.variables['crs'].getncattr('crs_wkt')

def getExtentFromNCFile(ncfile, coords=['lat','lon']):
  with netCDF4.Dataset(ncfile, 'r') as nc:
    # had to rearange order. NetCDF Flipped?
    y_min = np.amin(nc.variables[coords[0]])
    y_max = np.amax(nc.variables[coords[0]])
    x_min = np.amin(nc.variables[coords[1]])
    x_max = np.amax(nc.variables[coords[1]])
    return [x_min, x_max, y_min, y_max]

def getExtentInDifferentCRS(extent=False, wkt=False, proj4=False, epsg=False, to_epsg=False):
  s_srs = osr.SpatialReference()
  if wkt:
    s_srs.ImportFromWkt(wkt)
  elif proj4:
    s_srs.ImportFromProj4(proj4)
  elif epsg:
    s_srs.ImportFromEPSG(epsg)
  else: # no reprojection to do
    return extent
  t_srs = osr.SpatialReference()
  t_srs.ImportFromEPSG(to_epsg) # we want lat-lon
  transform = osr.CoordinateTransformation(s_srs, t_srs)
  ring = ogr.Geometry(ogr.wkbLinearRing)
  for x in range(2):
    for y in range(2):
      ring.AddPoint(float(extent[x]), float(extent[2+y]))
  poly = ogr.Geometry(ogr.wkbPolygon)
  poly.AddGeometry(ring)
  poly.Transform(transform)
  return(poly.GetEnvelope())

def rasterize(infile, outfile, pixel_size):

  fill = -9999. # nodata value
  # We assume a single layer, and that all features have the same fields.
  # So we use feature 0 as a pattern for the fields to transcribe.

  # Fields we don't want to turn into netcdf variables:
  exclude = ['Shape_Length', 'Shape_Area']

  # Need to map gdal types to numpy types, but not sure how to
  # use the library commands to do this. Right now, all I have is reals:
  npTypes = {2: np.float32, 0:np.int, 4:np.int}
  ps = pixel_size # shorthand

  c = ogr.Open(infile)
  src = c.GetLayer(0)
  x_min, x_max, y_min, y_max = src.GetExtent()
  rows = int((y_max - y_min) / ps)
  cols = int((x_max - x_min) / ps)

  # create an in-memory workspace
  # might need to do this per-field if we have other data types
  buf = gdal.GetDriverByName('MEM').Create('', cols, rows, 1, gdal.GDT_Float32)
  wkt = src.GetSpatialRef().ExportToWkt()
  buf.SetProjection(wkt)
  # Going north-to-south
  # buf.SetGeoTransform((x_min, ps, 0, y_min, 0, ps))
  buf.SetGeoTransform((x_min, ps, 0, y_max, 0, -ps))
  band = buf.GetRasterBand(1)
  band.SetNoDataValue(fill)

  # make netcdf vars for each field
  featureDefn = src.GetLayerDefn()
  with netCDF4.Dataset(outfile, 'w') as nc:
    nc.createDimension('y', rows)
    nc.createDimension('x', cols)
    nc.createVariable('y', np.double, ['y'])
    nc.createVariable('x', np.double, ['x'])
    # For CF-compliant projection info
    nc.createVariable('crs', np.int32, [])
    nc.variables['crs'].setncattr('crs_wkt', wkt)

    for fieldIndex in range(featureDefn.GetFieldCount()):
      fieldDefn = featureDefn.GetFieldDefn(fieldIndex)
      fieldName = fieldDefn.GetNameRef()
      if fieldName in exclude:
        continue
      type = fieldDefn.GetType()
      npType = npTypes[type]
      nc.createVariable(fieldName, npType, ['y', 'x'], fill_value=fill)

    # Now we've created all the vars, we write them. If we did this
    # in the above loop, we'd switch the netCDF driver between define
    # and write modes, which takes a lot of time
    # Going north-to-south
    # nc.variables['y'][:] = [(y_min + ps/2.) + ps * i for i in range(rows)]
    nc.variables['y'][:] = [(y_max - ps/2.) - ps * i for i in range(rows)]
    nc.variables['x'][:] = [(x_min + ps/2.) + ps * i for i in range(cols)]
    for fieldIndex in range(featureDefn.GetFieldCount()):
      fieldName = featureDefn.GetFieldDefn(fieldIndex).GetNameRef()
      if fieldName in exclude:
        continue
      band.Fill(fill) # Don't know whether this is necessary
      err = gdal.RasterizeLayer(buf, [1], src,
        options=["ATTRIBUTE=%s" % fieldName])
      nc.variables[fieldName][:] = band.ReadAsArray()
