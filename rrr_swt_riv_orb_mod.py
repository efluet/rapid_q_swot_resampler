#!/usr/bin/python
#******************************************************************************
#rrr_swt_riv_orb_mod.py
#******************************************************************************
#Purpose:
#SWOT Orbit overlay on model outputs from a river model.  
#Authors:
#Cedric H. David, Etienne Fluet-Chouinard, 2016-2016


#%%*****************************************************************************
# Import Python modules
#*******************************************************************************
import sys
import netCDF4
import xray
import numpy as np
import pandas as pd


#%%*****************************************************************************
# Declaration of variables (given as command line arguments)
#*******************************************************************************
# 1 - rrr_mod_nc1
# 2 - rrr_ovl_csv
# 3 - rrr_mod_nc2


#%%*****************************************************************************
#  Get command line arguments
#*******************************************************************************
IS_arg=len(sys.argv)
if IS_arg != 4:
     print('ERROR - 3 and only 3 arguments can be used')
     raise SystemExit(22) 

rrr_mod_nc1 = sys.argv[1]
rrr_ovl_csv = sys.argv[2]
rrr_mod_csv_out = sys.argv[3]


#%%*****************************************************************************
#  Print input information
#*******************************************************************************
print('Command line inputs')
print('- '+rrr_mod_nc1)
print('- '+rrr_ovl_csv)
print('- '+rrr_mod_csv_out)


#%%*****************************************************************************
#  Check if files exist 
#*******************************************************************************

try:
     with open(rrr_mod_nc1) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_mod_nc1)
     raise SystemExit(22) 

try:
     with open(rrr_ovl_csv) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_ovl_csv)
     raise SystemExit(22) 



#%%*****************************************************************************
#  read the csv output from the intersection, and sort values (optional)
#*******************************************************************************

rrr_ovl_df = pd.read_csv(rrr_ovl_csv, dtype=int)
rrr_ovl_df = rrr_ovl_df.sort_values(by='IM_ovl_tim')


#%%*****************************************************************************
#  Extend the SWOT orbit timepoints by repeating the time cycle.
#*******************************************************************************
# There are 69 complete cycles of 20 days in the three years of 2004-07 covered by Rapid data.
# Assuming that the orbit cycles are identical, we extend the orbit timing 
# by adding cycles of 1802700 seconds to the river overlay of the initial cycle.

rrr_ovl_df_yrs = rrr_ovl_df.copy(deep=True)

for i in range(1,69):

    rrr_ovl_df_yrs['IM_ovl_tim'] = rrr_ovl_df_yrs['IM_ovl_tim'] + 1802700
    rrr_ovl_df = pd.concat([rrr_ovl_df, rrr_ovl_df_yrs])

del rrr_ovl_df_yrs


#%%*****************************************************************************
#  read the netcdf file to dataframe
#*******************************************************************************

da = xray.open_dataset(rrr_mod_nc1)
rrr_mod_df1 = da.to_dataframe()

# convert multi-level index to columns, for merger
rrr_mod_df1.reset_index(inplace=True)

# Convert time steps to seconds to match SWOT time format.
rrr_mod_df1['Time_sec'] = (rrr_mod_df1['Time'] * (3*60*60)).astype(int)

# Remove old time step column
rrr_mod_df1.drop('Time', axis=1, inplace=True)



#%%*****************************************************************************
#  Find the closest sec
#*******************************************************************************
# takes a pd.Timestamp() instance and a pd.Series with dates in it
# calcs the delta between `timepoint` and each date in `time_series`
# returns the closest date and optionally the number of days in its time delta

def find_closest_date(timepoint, time_series, add_time_delta_column=True):
    deltas = np.abs(time_series - timepoint)
    idx_closest_date = np.argmin(deltas)
    res = {"closest_date": time_series.ix[idx_closest_date]}
    idx = ['closest_date']
    if add_time_delta_column:
        res["closest_delta"] = deltas[idx_closest_date]
        idx.append('closest_delta')
    return pd.Series(res, index=idx)


#%%*****************************************************************************
#  Subset the Qout time series to the SWOT time-points
#*******************************************************************************

# Subset the  Rapid Qout data to the river reaches in input.
# This first selection speeds up the subsequent riv+time selection.
rrr_mod_df1 = rrr_mod_df1[rrr_mod_df1['COMID'].isin(rrr_ovl_df['IS_riv_id'])]

# Create series of unique time steps. 
# Because river reaches all share the same time steps, we can pair 
unique_rrr_time = pd.Series(rrr_mod_df1['Time_sec'].unique())

# Find the closest matching time, calculate distance/difference in seconds between the two.
# add the time and difference to the table
rrr_ovl_df[['closest_rrr_time', 'secs_diff']] = rrr_ovl_df.IM_ovl_tim.apply(find_closest_date, args=[unique_rrr_time])

# Join the timeseries and timepoints, on river_id and time_stamp. 
rrr_ovl_df_qout = pd.merge(rrr_ovl_df, rrr_mod_df1, how='inner', left_on=['IS_riv_id','closest_rrr_time'], right_on=['COMID','Time_sec'])

# drop duplicated columns in the joined table; remove unneeded variables.
rrr_ovl_df_qout.drop(['COMID','Time_sec'], axis=1, inplace=True)

del rrr_ovl_csv, rrr_mod_nc1, rrr_ovl_df, rrr_mod_df1, unique_rrr_time, i


#%%*****************************************************************************
# Write output to CSV file
#*******************************************************************************

rrr_ovl_df_qout.to_csv(rrr_mod_csv_out)
del rrr_mod_csv_out
