#!/usr/bin/env python

#####################
# HELPER FUNCTIONS 
# UND ATSC411 
#####################

# IMPORTS
##########################################
import numpy as np
from datetime import datetime, timedelta
import requests
from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
from xarray.backends import NetCDF4DataStore
import xarray as xr
import sys
import time as comp_time
import warnings
from metpy.interpolate import log_interpolate_1d

import pyproj
from metpy.units import units


def get_xarray(H,model):
    if model=='gfs':
        #open data as xarray
        #isobaric
        ds_vert = H.xarray(r":(UGRD|VGRD|HGT|TMP|RH):\d+ mb",remove_grib=False)
        #surface & hght above ground (opens 3 xarray datasets)
        ds_sfc = H.xarray(r":(TMP|HGT|OROG|PRES|RH|UGRD|VGRD):(10 m above ground|2 m above ground|surface):",remove_grib=False)

        #assing xarray datasets and drop vertical coordinate since there's only one
        #this allows us to merge with the isobaric data
        
        #wind xarray ds
        ds_sfc_uv = ds_sfc[0]
        ds_sfc_uv = ds_sfc_uv.drop_vars('heightAboveGround')
        
        #temp & rel humidity xarray ds
        ds_sfc_t_rh = ds_sfc[1]
        ds_sfc_t_rh = ds_sfc_t_rh.drop_vars('heightAboveGround')
        
        #surface orography xarray ds
        ds_sfc_orog = ds_sfc[2]
        ds_sfc_orog = ds_sfc_orog.drop_vars('surface')

        #create new xarray dataset
        ds = ds_vert
        #put in surface vars
        ds['t2'] = ds_sfc_t_rh['t2m']
        ds['rh2'] = ds_sfc_t_rh['r2']
        ds['u10'] = ds_sfc_uv['u10']
        ds['v10'] = ds_sfc_uv['v10']
        ds['orog'] = ds_sfc_orog['orog']

        #subset to north america
        #lat is weird because it starts at north pole
        min_lat=75
        max_lat=10
        min_lon=180
        max_lon=355
        ds = ds.sel(latitude=slice(min_lat, max_lat), longitude=slice(min_lon, max_lon))

        #set projection
        ds = ds.metpy.assign_crs(grid_mapping_name='latitude_longitude',
                                 earth_radius=6371229.0)
        
        return(ds)

    elif model=='nam':
        #open data as xarray
        #isobaric
        ds_vert = H.xarray(r":(UGRD|VGRD|HGT|TMP|RH):\d+ mb",product='awphys',remove_grib=False)
        ds_vert = ds_vert.drop_vars('valid_time')
        #surface & hght above ground (opens 3 xarray datasets)
        ds_sfc = H.xarray(r":(TMP|HGT|OROG|PRES|RH|UGRD|VGRD):(10 m above ground|2 m above ground|surface):",remove_grib=False)

        #assing xarray datasets and drop vertical coordinate since there's only one
        #this allows us to merge with the isobaric data
        
        #wind xarray ds
        ds_sfc_uv = ds_sfc[0]
        ds_sfc_uv = ds_sfc_uv.drop_vars(['heightAboveGround','valid_time'])
        
        #temp & rel humidity xarray ds
        ds_sfc_t_rh = ds_sfc[1]
        ds_sfc_t_rh = ds_sfc_t_rh.drop_vars(['heightAboveGround','valid_time'])
        
        #surface orography xarray ds
        ds_sfc_orog = ds_sfc[2]
        ds_sfc_orog = ds_sfc_orog.drop_vars(['surface','valid_time'])

        #create new xarray dataset
        ds = ds_vert
        #put in surface vars
        ds['t2'] = ds_sfc_t_rh['t2m']
        ds['rh2'] = ds_sfc_t_rh['r2']
        ds['u10'] = ds_sfc_uv['u10']
        ds['v10'] = ds_sfc_uv['v10']
        ds['orog'] = ds_sfc_orog['orog']

        #set projection
        # Rename dims if needed
        if 'grid_xt' in ds.dims and 'grid_yt' in ds.dims:
            ds = ds.rename({'grid_xt': 'x', 'grid_yt': 'y'})
        # Extract 2D lat/lon
        proj = pyproj.Proj(proj='lcc', lat_1=25, lat_2=25,
                   lat_0=25, lon_0=-95,
                   x_0=0, y_0=0,
                   ellps='WGS84')
        lats = ds['latitude'].values
        lons = ds['longitude'].values
        # Project lat/lon to x/y in meters (still 2D)
        x2d, y2d = proj(lons, lats)
        # Convert 2D x/y to 1D assuming regular grid
        x1d = x2d[0, :] * units.meter  # first row, along columns
        y1d = y2d[:, 0] * units.meter  # first column, along rows
        # Assign 1D coordinates
        ds = ds.assign_coords({'x': x1d, 'y': y1d})
        # Assign CF-style CRS
        lc_cf = {
                'grid_mapping_name': 'lambert_conformal_conic',
                'standard_parallel': [25, 25],
                'longitude_of_central_meridian': -95.0,
                'latitude_of_projection_origin': 25,
                'false_easting': 0.0,
                'false_northing': 0.0,
                'semi_major_axis': 6371229.0,
                #'inverse_flattening': 297.0
        }
        ds = ds.metpy.assign_crs(lc_cf)

        return(ds)
    
    else:
        print('not implemented yet')



