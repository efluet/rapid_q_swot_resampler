#--------------------------------------------------------------------------------------------------
# RAPID model discharge SWOT-orbit resampler
#--------------------------------------------------------------------------------------------------
# This python code takes three inputs: 
#	1) the model outputs ("modeled_outputs.nc”), 
# 	2) the map of the largest rivers that are computed (“largest_rivers.shp”), and 
# 	3) the SWOT orbit map (“SWOT_orbit.shp”), 
#
# The input data are currently hard-coded in main module at the bottom for ease of testing, 
# but will be modified to parse command line arguments, once we get the script doing what it should.
#--------------------------------------------------------------------------------------------------

# function extracting the rapid discharge data, from the spatial intersection of rivers by a submodule
def rapid_q_swot_orbit_resampler (rapid_q, rivers, swot_orbits, resampled_output):

	# import modules
	import from netCDF4 import Dataset
	import pandas as np
	import fiona
	from shapely.geometry import shape, mapping
	import rtree


	# before attempting to select individual rivers with the orbits, we could first subset the orbits based on their intersection with the bounding box of river reaches.
	# this would exclude orbits that don't overlap at all with the river shapefile, and thus speed up the subsequent intersection for individual river reaches.
	# It seems like the module 'pyshp' can easily do that:  bbox = shapes[3].bbox


	# execute the intersection function (defined below) between the river reach and swot orbit identifiers
	# returns a dataframe of the identifiers intersection 
	intersected_rivers = shapefile_intersection(rivers, swot_orbits)

	# read in the RAPID discharge NETcdf file as a pandas dataframe
	rapid_q = Dataset(rapid_q, mode='r')
	# print rapid_q.variables   
	# print rapid_q.dimensions.keys()
	qout_df = pd.DataFrame(rapid_q.variables['Qout'][:])

	# NOTE: I initally wondered how to deal with river reaches straddling across the edge of the orbit;
	# upon further thought I realized that we'll need to use reach_id later on, so splitting reaches into new ones wouldn't be helpful there.  
	# join the intersection table to the rapid table, keeping only matches on 'REACHCODE' and 'Mean Time' of orbit 
	# (or within a time-window of orbit if there is an exact time mathc is not possible)

	# Cedric - We noticed that COMID's weren't all unique in the river shapefile. How should we deal with that?
	# Apoorva - I think you had a script from the workshop that did this - and matched time periods (have both start at Jan 1st)
	resampled_output = intersected_rivers.merge(rapid_q, left_on=['COMID','Mean time'], right_on=['COMID','Time'], how='inner')
	# this join would only work if the rapid_q data would have long format

	# write the output dataframe to a netcdf file as defined in argurment

	# also return the output dataframe, for function to be used as sub-module of broader script.
	return resampled_output


#-------------------------------------------------------------------------------------
# function intersecting two shapefiles, while keeping IDs of feat1.
# modified from the webpage suggested by Cedric on May 5 2016:  http://gis.stackexchange.com/questions/119374/intersect-shapefiles-using-shapely
# Shapely (does the intersection), and Rtree (allows to make the process of intersection faster).
# We only need a table of the intersection reaches and orbits (in long-table format).
# There is no need do not need a shapefile output

def shapefile_intersection (in_swot, in_riv, out_intersect):
	
	# create empty dataframe for the output
	output_df = pd.DataFrame(columns=['COMID','TIME', 'ORBITID','QOUT'])

	with fiona.open(in_swot, 'r') as layer1:

	    with fiona.open(in_riv, 'r') as layer2:
	        
	        # We copy schema and add the  new property for the new resulting shp
	        schema = layer2.schema.copy()
	        schema['properties']['COMID']['FID']['Mean time'] = 'int:10'   

	        # We open a first empty shp to write new content from both others shp
	        with fiona.open(out_intersect, 'w', 'ESRI Shapefile', schema) as layer3:
	            index = rtree.index.Index()
	            
	            for feat1 in layer1:
	                fid = int(feat1['FID'])
	                time = int(feat1['Mean time'])
	                geom1 = shape(feat1['geometry'])
	                index.insert(fid, geom1.bounds)

	            for feat2 in layer2:
	                reachcode = int(feat2['REACHCODE'])
	                geom2 = shape(feat2['geometry'])
	                for fid in list(index.intersection(geom2.bounds)):
	                    if fid != int(feat2['id']):
	                        feat1 = layer1[fid]
	                        geom1 = shape(feat1['geometry'])
	                        if geom1.intersects(geom2):
	                            
	                            # We take attributes from shp2, as a data frame
	                            out_df = pd.DataFrame(feat2['properties'])
	                            # Then append the uid attribute we want from the other shp
	                            #props['fid'] = feat1['properties']['fid']
	                            
	                            # append the loop intersect output to the cumulative 'intersect_df'
	                            intersect_df = output_df.append(out_row, ignore_index=True) 

    # return a pandas dataframe of the intersecting data
    return intersect_df


# test the function above with subset test data 
if __name__ == '__main__':

	import sys

	# reads in command line arguments
	cmdargs = str(sys.argv)

	# hardcoding the input file pathes, for ease of testing.
	rapid_q_output = r'Qout_San_Guad_1460days_p3_dtR900s.nc'
	rivers = r'..\data\nhd\NHDFlowline_San_Guad_with_dir.shp'
	swot_orbit = r'..\data\swot_swaths\SWOT_890km_77_onepolypertrack_nadirgap_180.shp'
	resampled_output = r'..\output\test.csv'

	# the below code parses command line arguments as inputs, we can use it once we get the script doing what it should.
	"""
	# declare input and output files from the command line arguments
	# this would be have the following format:
	#   ./rapid_q_swot_orbit_resampler.py modeled_outputs.nc largest_rivers.shp SWOT_orbit.shp sampled_outputs.nc
	
	rapid_q_output = sys.argv[0]
	rivers = sys.argv[1]
	swot_orbit = sys.argv[2]
	resampled_output = sys.argv[3]
	"""

	# execute the resampler function using the input files. 
	rapid_q_swot_orbit_resampler(rapid_q_output, rivers, swot_orbit, resampled_output)