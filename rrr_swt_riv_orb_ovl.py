#!/usr/bin/python
#******************************************************************************
#rrr_swt_riv_orb_ovl.py
#******************************************************************************
#Purpose:
#SWOT Orbit overlay on map of rivers.  
#Author:
#Cedric H. David, 2016-2016


#*******************************************************************************
#Import Python modules
#*******************************************************************************
import sys
import fiona
import shapely.geometry
import rtree
import csv


#*******************************************************************************
#Declaration of variables (given as command line arguments)
#*******************************************************************************
# 1 - rrr_riv_shp
# 2 - rrr_orb_shp
# 3 - rrr_ovl_shp
# 4 - rrr_ovl_csv


#*******************************************************************************
#Get command line arguments
#*******************************************************************************
IS_arg=len(sys.argv)
if IS_arg != 5:
     print('ERROR - 4 and only 4 arguments can be used')
     raise SystemExit(22) 

rrr_riv_shp=sys.argv[1]
rrr_orb_shp=sys.argv[2]
rrr_ovl_shp=sys.argv[3]
rrr_ovl_csv=sys.argv[4]


#*******************************************************************************
#Print input information
#*******************************************************************************
print('Command line inputs')
print('- '+rrr_riv_shp)
print('- '+rrr_orb_shp)
print('- '+rrr_ovl_shp)
print('- '+rrr_ovl_csv)


#*******************************************************************************
#Check if files exist 
#*******************************************************************************
try:
     with open(rrr_riv_shp) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_riv_shp)
     raise SystemExit(22) 

try:
     with open(rrr_orb_shp) as file:
          pass
except IOError as e:
     print('ERROR - Unable to open '+rrr_orb_shp)
     raise SystemExit(22) 


#*******************************************************************************
#Open rrr_riv_shp
#*******************************************************************************
print('Open rrr_riv_shp')

rrr_riv_lay=fiona.open(rrr_riv_shp, 'r')
IS_riv_tot=len(rrr_riv_lay)
print('- The number of river features is: '+str(IS_riv_tot))

if 'COMID' in rrr_riv_lay[0]['properties']:
     YV_riv_id='COMID'
elif 'ARCID' in rrr_riv_lay[0]['properties']:
     YV_riv_id='ARCID'
else:
     print('ERROR - Neither COMID nor ARCID exist in '+rrr_riv_shp)
     raise SystemExit(22) 

IV_riv_tot_id=[]
for JS_riv_tot in range(IS_riv_tot):
     IV_riv_tot_id.append(int(rrr_riv_lay[JS_riv_tot]['properties'][YV_riv_id]))


#*******************************************************************************
#Open rrr_orb_shp
#*******************************************************************************
print('Open rrr_orb_shp')

rrr_orb_lay=fiona.open(rrr_orb_shp, 'r')
IS_orb_tot=len(rrr_orb_lay)
print('- The number of orbit features is: '+str(IS_orb_tot))


#*******************************************************************************
#Create spatial index for the bounds of each river feature
#*******************************************************************************
print('Create spatial index for the bounds of each river feature')

index=rtree.index.Index()
for rrr_riv_feat in rrr_riv_lay:
     riv_fid=int(rrr_riv_feat['id'])
     #the first argument of index.insert has to be 'int', not 'long' or 'str'
     riv_geom=shapely.geometry.shape(rrr_riv_feat['geometry'])
     index.insert(riv_fid, riv_geom.bounds)


#*******************************************************************************
#Find intersections 
#*******************************************************************************
print('Find intersections')

IS_ovl_cnt=0
#The total count of river features completely contained in orbit features

IM_ovl_cnt={}  # create empty dictionary for hash table
IM_ovl_tim={}
for JS_riv_tot in range(IS_riv_tot):
    
     #A hash table associating each river reach ID with the number of overlays
     IM_ovl_cnt[IV_riv_tot_id[JS_riv_tot]]=0

     #A hash table associating each river reach ID with the overlay times 
     IM_ovl_tim[IV_riv_tot_id[JS_riv_tot]]=[]
     
# loop through swot orbits
for rrr_orb_feat in rrr_orb_lay:
     orb_fid=int(rrr_orb_feat['id'])
     orb_shy=shapely.geometry.shape(rrr_orb_feat['geometry'])
     for riv_fid in [int(x) for x in list(index.intersection(orb_shy.bounds))]:
          #---------------------------------------------------------------------
          #print('The bounds of riv_fid='+str(riv_fid)+                        \
          #      ' intersect with the bounds of orb_fid='+str(orb_fid))
          #---------------------------------------------------------------------
          rrr_riv_feat=rrr_riv_lay[riv_fid]
          riv_shy=shapely.geometry.shape(rrr_riv_feat['geometry'])
          if orb_shy.contains(riv_shy):
               #----------------------------------------------------------------
               #print('riv_fid='+str(riv_fid)+                                 \
               #      ' is completely inside of orb_fid='+str(orb_fid))
               #----------------------------------------------------------------
               #out_shy=riv_shy.intersection(orb_shy)    # EF: out_shy variable is not used anywhere.
               IS_ovl_cnt = IS_ovl_cnt+1
               IS_riv_id = int(rrr_riv_feat['properties'][YV_riv_id])
               ZS_orb_tim=float(rrr_orb_feat['properties']['Mean_time'])
               #IM_ovl_cnt[IS_riv_id]=IM_ovl_cnt[IS_riv_id]+1
               IM_ovl_tim[IS_riv_id].append(ZS_orb_tim)

print('- The number of river features completely contained in orbit features ' \
      +'is: '+str(IS_ovl_cnt))


#*******************************************************************************
#Create rrr_ovl_shp based on rrr_riv_shp and rrr_orb_shp
#*******************************************************************************
print('Create rrr_ovl_shp based on rrr_riv_shp and rrr_orb_shp')

rrr_riv_crs=rrr_riv_lay.crs
rrr_ovl_crs=rrr_riv_crs.copy()
#print(rrr_ovl_crs)
print('- Coordinate Reference System copied')

rrr_riv_sch=rrr_riv_lay.schema
rrr_orb_sch=rrr_orb_lay.schema
rrr_ovl_sch=rrr_riv_sch.copy()
rrr_ovl_sch['properties']['OVERLAYS']='int:9'
#print(rrr_ovl_sch)
print('- Schema copied')

rrr_ovl_lay=fiona.open(rrr_ovl_shp, 'w',                                       \
                       crs=rrr_ovl_crs,                                        \
                       driver='ESRI Shapefile',                                \
                       schema=rrr_ovl_sch                                      \
                       )
print('- New shapefile created')

for JS_riv_tot in range(IS_riv_tot):
     rrr_riv_feat=rrr_riv_lay[JS_riv_tot]
     rrr_ovl_prp=rrr_riv_feat['properties']
     rrr_ovl_prp['OVERLAYS']=IM_ovl_cnt[IV_riv_tot_id[JS_riv_tot]]
     rrr_ovl_geom=rrr_riv_feat['geometry']
     rrr_ovl_lay.write({                                                       \
                        'properties': rrr_ovl_prp,                             \
                        'geometry': rrr_ovl_geom,                              \
                        })
print('- New shapefile populated')

rrr_ovl_lay.close()
print('- Closing rrr_ovl_shp so that values are saved')


#*******************************************************************************
#Write outputs
#*******************************************************************************
print('Writing rrr_ovl_csv')

with open(rrr_ovl_csv, 'wb') as csvfile:
     csvwriter = csv.writer(csvfile, dialect='excel')

     # write header row to file
     fieldnames = ['IS_riv_id', 'IM_ovl_tim']
     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
     writer.writeheader()
     
     for JS_riv_tot in range(IS_riv_tot):
          IS_riv_id = IV_riv_tot_id[JS_riv_tot]
          #IV_line = [IS_riv_id, IM_ovl_cnt[IS_riv_id]] 

          for riv_times in IM_ovl_tim[IS_riv_id]:
              IV_line = [IS_riv_id, riv_times]
              
              csvwriter.writerow(IV_line) 


#*******************************************************************************
#End
#*******************************************************************************
