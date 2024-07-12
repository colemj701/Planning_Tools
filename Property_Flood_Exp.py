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
Ranking = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
output_folder = arcpy.GetParameterAsText(3)

# Script Argument
default_gdb = arcpy.env.scratchGDB
FDissolve = [Ranking,'Type_Oc']
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

def rank(x,y):# creat DataFrame from ranking csv
    # x is in feature class
    # y is target gdb
    arcpy.SetProgressor('default','Building FLD Zone Ranking...')
    df = pd.read_csv(xlsxPath('SFHA_Rankings.csv'),na_values='')

    #build fld zone and subtype ranking dictionaries
    for value, index in enumerate(df['Flood Zone']):
        FLD_List[value] = index

    for value, index in enumerate(df['Subtype']):
        Sub_List[value] = index

    # add fld zone and subtype fields back to dissolved feature class
    arcpy.management.AddField(x,"FLD_ZONE","TEXT")
    arcpy.management.AddField(x,"Subtype","TEXT")

    # use ranking to update flood zone and subtype attribute fields in results table
    edit = arcpy.da.Editor(y)
    edit.startEditing(False, True)

    with arcpy.da.UpdateCursor(x, ['FLD_ZONE', 'Subtype',Ranking]) as cursor:
        for row in cursor:
            # Check the condition
            fldzone = FLD_List.get(row[2], 'default_value_for_FLD_ZONE')
            subtype = Sub_List.get(row[2], 'default_value_for_Subtype')
            row[0] = fldzone
            cursor.updateRow(row)
            row[1] = subtype
            update = cursor.updateRow(row)

    edit.stopEditing(True)
    arcpy.SetProgressorPosition()
    return update


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
arcpy.management.Dissolve(input_feature,paths(default_gdb,"Exp_Building_By_Occupancy"),FDissolve,[['Building_Count','SUM'],["BldgCost","SUM"],['ContentCos','SUM'],['TotalBldgValue','SUM']])
arcpy.SetProgressorPosition()

dis1 = paths(default_gdb,"Exp_Building_By_Occupancy")

rank(dis1,default_gdb)

# Export Final Calculated Attribute Table
arcpy.SetProgressor("default","Exporting Hazus 100yr UDF Results table...")
arcpy.conversion.ExportTable(dis1,output_folder+"\\Exp_Building_By_Occupancy.csv","","NOT_USE_ALIAS")
arcpy.SetProgressorPosition()