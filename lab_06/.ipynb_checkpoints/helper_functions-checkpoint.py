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






### RAP REANALYSIS ###
#########################################################################################################
def give_me_rap_data(year, month, day, hour, latlon=[-139.9699, -57.2685, 16.2086, 55.5167]):
    st = comp_time.time()
    
    print(f'> RAP REANALYSIS DATA ACCESS FUNCTION --\n-----------------------------------------')

    # create dict of RAP-data urls for the different versions of RAP and RUC from NCEI    
    urls = {  
    'RAP_13km' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap130/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',
    'RAP_13km_old' : 'https://www.ncdc.noaa.gov/thredds/ncss/model-rap130-old/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',

    'RAP_13km_anl' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap130anl/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',
    'RAP_13km_anl_old' : 'https://www.ncdc.noaa.gov/thredds/ncss/model-rap130anl-old/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',

    'RAP_25km' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap252/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',
    'RAP_25km_old' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap252-old/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',

    'RAP_25km_anl' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap252anl/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',
    'RAP_25km_anl_old' : 'https://www.ncei.noaa.gov/thredds/ncss/model-rap252anl-old/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/rap_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',

    'RUC_13km' : 'https://www.ncei.noaa.gov/thredds/ncss/model-ruc130anl/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/ruc2anl_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',
    'RUC_13km_old' : 'https://www.ncei.noaa.gov/thredds/ncss/model-ruc130anl-old/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/ruc2anl_130_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb2',

    'RUC_25km' : 'https://www.ncei.noaa.gov/thredds/ncss/model-ruc252anl/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/ruc2anl_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb',
    'RUC_25km_old' : 'https://www.ncei.noaa.gov/thredds/ncss/model-ruc252anl/'+str(year)+str(month)+'/'+str(year)+str(month)+str(day)+'/ruc2anl_252_'+str(year)+str(month)+str(day)+'_'+str(hour)+'00_000.grb'
    }

    # create a simple test for each URL, use the first one that works 
    try:
        for url, key in zip(urls.values(), urls.keys()):
            try:
                NCSS(url)
                print(f'> DATASET USED: {key}')
                url_to_use = url
                source = str(key)[0:3]
                break
            except:
                pass
    except:
        pass
    try:
        data = NCSS(url_to_use)
    except:
        warnings.filterwarnings("ignore")
        sys.exit('NCSS URL FAILED -- THIS HAPPENS WHEN A BAD REQUEST IS MADE.\n> CHECK TO MAKE SURE YOU ENTERED THE CORRECT DATES.\n> NOTE: DATA IS NOT AVAILIABLE FOR EVERY DATE\n> THIS CATALOG OFTEN EXPERIENCES MISSING DATA/OUTAGES\n> MAKE SURE DATES ARE STRINGS -- MONTH, DAY AND HOUR MUST BE TWO DIGITS (EX: 18, 06, 00)')
        pass

    # set up TDS query 
    query = data.query()

    # subset data by variable names for RAP & RUC (of course they have to be different)
    if source in ['rap', 'RAP']:
        query.variables(
          'Geopotential_height_isobaric',
                    'Geopotential_height_surface',
                    'Temperature_isobaric',
                    'u-component_of_wind_isobaric',
                    'v-component_of_wind_isobaric').add_lonlat()
    else:
        query.variables(
          'Geopotential_height_isobaric',
                    'Geopotential_height_surface',
                    'Temperature_isobaric',
                    'u-component_of_wind_isobaric',
                    'v-component_of_wind_isobaric').add_lonlat()

    # subset data by requested domain
    query.lonlat_box(latlon[0], latlon[1], latlon[2], latlon[3])

    # laod the data from TDS
    raw_data = xr.open_dataset(NetCDF4DataStore(data.get_data(query)))
    #raw_data = data.get_data(query)

    print('> COMPLETE --------')

    elapsed_time = comp_time.time() - st
    print('> RUNTIME:', comp_time.strftime("%H:%M:%S", comp_time.gmtime(elapsed_time)))
    return raw_data












# IDEAL GASE LAW, SOLVED FOR RHO
###########################################
def gas_law(pressure, temperature): 

    '''
    compute air density at the 500hPa level via the gas law

    where 

    rho = p/(T*R)
    '''
    # constants
    gas_constant = 287.05 # ideal gas constant of dry air (J/kg*K)

    # compute air density, convert pressure to Pa
    rho = (pressure*100) / (temperature * gas_constant)

    return rho










# PRESSURE INTERPOLATION AT HEIGHT
# FROM GEOPOTENTIAL & PLEVS
###########################################
def pres_at_hgt(geopotential, isobaric_levels, lat, lon, target_height):

    '''
    given a 3D array of geohgts, a 2D array of lats, lons, a 1D array of isobaric coordinates 
    and a target altitude (meters)...

    use metpy's log_interpolate_1d to interpolate pressure at a given altitude.... 
    - "Interpolates data with logarithmic x-scale over a specified axis. Interpolation on a logarithmic x-scale for interpolation values in pressure coordinates."

    returns a 2D array of interpolated pressures (hPa) at the target height for every lat/lon point

    '''
    
    pressure_at_height = np.zeros((1, len(lat), len(lon)))

    for ilat in range(len(lat)):
        for ilon in range(len(lon)):
            pressure_at_height[:, ilat, ilon] = log_interpolate_1d(target_height,
                                                                   geopotential[:, ilat, ilon],
                                                                   isobaric_levels)

    

    return pressure_at_height[0,:,:]





# TEMPERATURE INTERPOLATION AT HEIGHT
# FROM TEMPERATURE & PLEVS
##########################################

def temp_at_hgt(temperature, isobaric_levels, lat, lon, pres_aloft):

    '''
    given a 3D array of temperatures, a 2D array of lats, lons, a 1D array of isobaric coordinates 
    and a target altitude (meters)...

    use metpy's log_interpolate_1d to interpolate temperature at a given altitude.... 
    - "Interpolates data with logarithmic x-scale over a specified axis. Interpolation on a logarithmic x-scale for interpolation values in pressure coordinates."

    returns a 2D array of interpolated temperatures (hPa) at the target height for every lat/lon point

    '''
    
    temperature_at_height = np.zeros((1, len(lat), len(lon)))

    
    for ilat in range(len(lat)):
        for ilon in range(len(lon)):
            temperature_at_height[:, ilat, ilon] = log_interpolate_1d(pres_aloft[ilat, ilon],
                                                                      isobaric_levels,
                                                                       temperature[:, ilat, ilon])

    

    return temperature_at_height[0,:,:]
