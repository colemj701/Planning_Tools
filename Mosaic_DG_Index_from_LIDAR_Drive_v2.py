import arcpy, os, sys, requests, logging, errno, datetime
import pandas as pd
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from arcpy.sa import *
from utilsDG1 import (
    paths, 
    createFolder, 
    log_message, 
    build_tile_index, 
    bld_tile_path, 
    mosaic, 
    dir_file, 
    log_setup)

arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension('3D')

arcpy.SetProgressor('default','Initiating Tile Index Mosaic Processing Tool...')

arcpy.env.overwriteOutput = True


Smp_tiles = arcpy.GetParameterAsText(0)
tile_field = arcpy.GetParameterAsText(1)
DLQ = arcpy.GetParameterAsText(2)
Out_Raster = arcpy.GetParameterAsText(3)
Prelim = arcpy.GetParameterAsText(4)

LiDAR_Path = r'\\5rd2wx3\LIDAR_RASTERS\Statewide FLOOD Rasters'

#Logging level specified in script configuration
directory, filename, gp_dir = dir_file(Out_Raster)
log_setup(gp_dir)
Index_List, Tile_List = build_tile_index(Smp_tiles,tile_field,DLQ,LiDAR_Path,Prelim)
Raster_List, Unmatched_List = bld_tile_path(Index_List,DLQ)
mosaic(Raster_List,Out_Raster)
