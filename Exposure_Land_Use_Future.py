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

arcpy.SetProgressor("default","Initiating Parcel Exposure By Land Use Tool...")
arcpy.SetProgressorPosition()

# Tool Parameter Arguments
InFHA = arcpy.GetParameterAsText(0)
Ranking = arcpy.GetParameterAsText(1)
InParcel = arcpy.GetParameterAsText(2)
PIN = arcpy.GetParameterAsText(3)
LUse = arcpy.GetParameterAsText(4)
Output_GDB = arcpy.GetParameterAsText(5)
Output_TBFLD = arcpy.GetParameterAsText(6)
LandUse = arcpy.GetParameterAsText(7)
Spa_Ref = arcpy.GetParameterAsText(8)

# Local Tool Arguments
default_gdb = arcpy.env.scratchGDB
Feature_List = [InFHA,InParcel]
FDissolve_Fields1 = [Ranking,PIN,LUse]
FDissolve_Fields2 = [Ranking,LUse]
FLD_List = {}
Sub_List = {}

# set processing environment
def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# Append String Parameter function
def apptxt(x):
    if x == "":
        txto = ""
    else:
        txt = x.replace(" ","_")
        txto = str("_"+txt+"_")
    return txto

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(w,x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(w,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(w,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return parcel_count

# Calculate Land Use Areas by SFHA
def calcatt(w,x,y):
    arcpy.SetProgressor("default","Calculating Parcel Land Use {0} by SFHA...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(w,[[x,"AREA"]],"",y,Spa_Ref,"")
    return calcatt1

# Calculate Percentages
def sum_field_values(w,x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(w,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

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

    with arcpy.da.UpdateCursor(x, ['FLD_ZONE', 'Subtype','Ranking']) as cursor:
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

# Run initial Intersect
arcpy.SetProgressor("default","Running Intersect Tool...")
arcpy.Intersect_analysis(Feature_List,paths(default_gdb,"Parcel_Exposure_Int"+str(apptxt(LandUse)))+"Land_Use","ALL")
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int1 = paths(default_gdb,"Parcel_Exposure_Int"+str(apptxt(LandUse))+"Land_Use")

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int1,paths(default_gdb,"Parcel_Exposure_By"+str(apptxt(LandUse)))+"Land_Use_Prep",FDissolve_Fields1)
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int2 = paths(default_gdb,"Parcel_Exposure_By"+str(apptxt(LandUse))+"Land_Use_Prep")

# Add Parcel count
parcelcount(int2,1)

# Execute Dissolve - generate parcel counts per SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int2,paths(Output_GDB,"Parcel_Exposure_By"+str(apptxt(LandUse)))+"Land_Use",FDissolve_Fields2,[["Parcel_Count","SUM"]])
arcpy.SetProgressorPosition()

### New Tool Argument - Exposure by Land Use Dissolve Output Feature Class ####
int3 = paths(Output_GDB,"Parcel_Exposure_By"+str(apptxt(LandUse))+"Land_Use")

# build ranked fld zone attributes
rank(int3,default_gdb)

calcatt(int3,"Acres","ACRES_US"),calcatt(int3,"Sq_Mi","SQUARE_MILES_US")

arcpy.management.CalculateField(int3,"Percent_Area","!Acres! / " + str(sum_field_values(int3,"Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")

### New Tool Argument - New Schema Lock on modified feature ####
int4 = paths(Output_GDB,"Parcel_Exposure_By"+str(apptxt(LandUse))+"Land_Use")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting Exposure by {0} Land Use Attribute Table...".format(LandUse))
arcpy.conversion.TableToTable(int4,Output_TBFLD,"Parcel_Exposure_by"+str(apptxt(LandUse))+"Land_Use.csv")
