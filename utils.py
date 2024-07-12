import arcpy, os, sys, requests, logging, errno, datetime
import pandas as pd
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from arcpy.sa import *

env_settings_list = [
    "compression",
    "resamplingMethod",
    "nodata",
    "cellSize",
    "cellSizeProjectionMethod",
    "cellAlignment",
    "pyramid",
    "snapRaster"
]

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

def log_message(mes):
    arcpy.AddMessage(mes)
    logging.info(mes)

def get_file_name(file_path):
    return Path(file_path).name

def createFolder(folderPath):
    if not os.path.exists(folderPath):
        try:
            os.makedirs(folderPath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

#Logging level specified in script configuration
def dir_file(out_ras):
    directory, filename = os.path.split(out_ras)

    if directory.endswith('.gdb'):
        gp_dir = os.path.abspath(os.path.dirname(directory))
    else:
        gp_dir = directory

    return directory, filename, gp_dir

def log_setup(dir):
    # Close and reinitialize logging handlers to release file handles
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    log_folder = paths(dir,'GeoProcess_Logs')
    createFolder(log_folder)
    log_file_name = 'Mosaic_Logs_'+str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    log_file_path = paths(log_folder,log_file_name)
    log_set = logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    return log_set

def gp_env(snap):
    arcpy.env.compression = 'LZW'
    arcpy.env.resamplingMethod = 'BILINEAR'
    arcpy.env.snapRaster = snap
    arcpy.env.nodata = 'NONE'
    arcpy.env.cellAlignment = 'DEFAULT'
    arcpy.env.cellSize = 'MAXOF'
    arcpy.env.pyramid = 'PYRAMIDS -1 BILINEAR DEFAULT 75 NO_SKIP'
    arcpy.env.cellSizeProjectionMethod = 'CONVERT_UNITS'

def bld_tile_path(root_fld, contains, DQ):
    arcpy.SetProgressor('default', 'Building Raster List...')
    log_message('Building Raster List{0}'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
    ras_list = []
    un_match = []
    match_list = []
    match_count = 0
    index_count = len(contains)
    found_all_matches = False

    # Traverse through directories to find directories containing DQ
    for root, dirs, files in os.walk(root_fld):
        if match_count == index_count:  # Check if all matches have been found
            found_all_matches = True
            break
        for dir_name in dirs:
            arcpy.SetProgressor('default', 'Searching {0} for {1} raster tiles'.format(dir_name,DQ))
            if match_count == index_count:  # Check if all matches have been found
                found_all_matches = True
                break
            if DQ in dir_name:  # Check if DQ is present in the directory name
                dir_path = paths(root, dir_name)
                for rootx, dirsx, filesx in os.walk(dir_path):
                    for file in filesx:
                        if match_count == index_count:  # Check if all matches have been found
                            found_all_matches = True
                            break
                        file_path = paths(rootx, file)
                        if file_path.endswith('.tif'):
                            for substring in contains:
                                if substring in file and substring not in match_list:
                                    match_list.append(substring)
                                    ras_list.append(file_path)
                                    match_count += 1
                                    log_message('Tile matched query {0} ::  {1} tiles remaining'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")),index_count-match_count))
                                if match_count == index_count:  # Check if all matches have been found
                                    found_all_matches = True
                                    break

    log_message(f'A total of {len(match_list)} out of {len(contains)} tiles were located in the LiDAR Folders')
    mismatch = list(set(contains) - set(match_list))
    un_match.extend(mismatch)

    un_match_count = len(un_match)
    if len(mismatch) > 0:
        log_message(f'The following {un_match_count} tiles were not found within the LIDAR Folders:\n   ::  {un_match}')
        arcpy.AddWarning(f'The following tiles were not found within the LIDAR Folders:\n   ::  {un_match}')

    log_message('Raster Mosaic List Built{0}\n------------------------------------------------'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    return ras_list, un_match

def build_tile_index(in_feat, Tile_Field,DQ):
    arcpy.SetProgressor('default', 'Building Tile Index List...')
    log_message('Building Tile Index List{0}'.format('  ::  ' + str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
    index_list = set()
    tile_pre = DQ.replace('EM','')
    # Convert Tile_Field to a list if it's received as a string
    if isinstance(Tile_Field, str):
        Tile_Field = [Tile_Field]

    # Reading feature class data into a pandas DataFrame
    data = arcpy.da.SearchCursor(in_feat, Tile_Field)
    df = pd.DataFrame(data, columns=Tile_Field)

    for _, row in df.iterrows():
        index_item = '_'.join(map(str, row.values.tolist()))
        f_index_item = f'{tile_pre}_37_{index_item}_'
        index_list.add(f_index_item)

    log_message(f'Input index contains {len(index_list)} total tiles')
    log_message('Tile Index List Built{0}\n------------------------------------------------'.format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    return index_list

def mosaic(raster_list,out_raster,ras_list):
    arcpy.SetProgressor('default','Executing Tile Mosaic...')
    log_message('Executing Tile Mosaic Module{0}'.format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))
    
    directory, filename = os.path.split(out_raster)
    desc = arcpy.Describe(raster_list[0])
    spa = desc.SpatialReference
    spa_name = spa.name
    cell_size_x = desc.meanCellWidth
    out_ras = None
    
    gp_env(raster_list[0])

    log_message(f'Reference tile spatial reference  ::  {spa_name}')
    log_message(f'Reference tile cell size  ::  {cell_size_x}')
    log_message('---------------\nMosaic GeoProcessing Environments  ::\n---------------')
    for setting in env_settings_list:
        value = getattr(arcpy.env,setting)  # Get the value of the setting
        log_message(f"::   {setting}: {value}")

    log_message('Creating mosaic DEM{0}'.format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    try:
        arcpy.management.MosaicToNewRaster(
            input_rasters=ras_list,
            output_location=directory,
            raster_dataset_name_with_extension=filename,
            coordinate_system_for_the_raster=spa,
            pixel_type='32_BIT_FLOAT',
            cellsize=cell_size_x,
            number_of_bands=1,
            mosaic_method='MEAN',
            mosaic_colormap_mode='FIRST')
        
    except (Exception, OSError) as e:
            log_message("A process error occurred{0} \n{1}".format('  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S")),e))
            arcpy.AddWarning("An unexpected error occurred: {}".format(e))
            sys.exit()

    log_message('\n\nFinal Mosaic DEM has been exported to   ::\n   {0}   ::\n{1}'.format(directory,'  ::  '+str(datetime.now().strftime("%Y-%m-%d @ %H:%M:%S"))))

    return out_ras