# Import arcpy module
import arcpy, time, os, sys
import pandas as pd
import numpy as np
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
Output_GDB = arcpy.GetParameterAsText(1)
output_folder = arcpy.GetParameterAsText(2)

# Script Argument
default_gdb = arcpy.env.scratchGDB
FDissolve = 'Type_Oc'
FLD_List = {}
Sub_List = {}

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# get the location of the csv template file in FFRMS_Bin
def xlsxPath(x):
    cDir = os.getcwd()
    xsNm = x
    exPath = os.path.join(cDir,xsNm)
    return exPath

# Add Parcel count field and auto fill value of 1 for each row
def buildingcount(w,x):
    arcpy.SetProgressor("default","Adding Building Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(w,"Building_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(w,"Building_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return parcel_count
buildingcount(input_feature,1)

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(input_feature,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(input_feature,"TotalBldgValue","!BldgCost! + !ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

stats = []

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(input_feature,paths(default_gdb,"Exp_to_Building_By_Occupancy"),FDissolve,[['Building_Count','SUM'],["BldgCost","SUM"],['ContentCos','SUM'],['TotalBldgValue','SUM']])
arcpy.SetProgressorPosition()

dis1 = paths(default_gdb,"Exp_to_Building_By_Occupancy")

# Export Final Calculated Attribute Table
arcpy.SetProgressor("default","Exporting Building Exposure Results table...")
arcpy.conversion.ExportTable(dis1,output_folder+"\\Exp_to_Building_By_Occupancy.csv","","NOT_USE_ALIAS")
arcpy.SetProgressorPosition()