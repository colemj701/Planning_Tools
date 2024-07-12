# Import arcpy module
import arcpy, time, os, sys
import pandas as pd
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.SetProgressor("default","Initiating FHA Intersect Analysis Tool...")

Features = arcpy.GetParameterAsText(0)
Dis_Field = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
Output_TBFLD = arcpy.GetParameterAsText(3)
PolyAnalysis = arcpy.GetParameterAsText(4)
Spa_Ref = arcpy.GetParameterAsText(5)

default_gdb = arcpy.env.scratchGDB

FLD_List = {}
Sub_List = {}

# get the location of the csv template file in FFRMS_Bin
def xlsxPath(x):
    cDir = os.getcwd()
    xsNm = x
    exPath = os.path.join(cDir,xsNm)
    return exPath

# Calculate Intersect Area
def calcatt(w,x,y):
    arcpy.SetProgressor("default","Calculating Intersect {0}...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(w,[[x,"AREA"]],"",y,Spa_Ref,"")
    arcpy.SetProgressorPosition()
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

# run layer intersect
arcpy.SetProgressor("default","Running Intersect Tool...")
arcpy.Intersect_analysis(Features,default_gdb+"\\S_FLD_HAZ_AR_"+PolyAnalysis+"_Int","ALL")
arcpy.SetProgressorPosition()

### New Tool Argument - SFHA intersect feature class ####
int1 = (default_gdb+"\\S_FLD_HAZ_AR_"+PolyAnalysis+"_Int")

calcatt(int1,"Acres","ACRES_US"),calcatt(int1,"Sq_Mi","SQUARE_MILES_US")

#Execute Dissolve
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int1,Output_GDB+"\\S_FLD_HAZ_AR_"+PolyAnalysis+"_Analysis",Dis_Field,[["Acres","SUM"],["Sq_Mi","SUM"]])
arcpy.SetProgressorPosition()

### New Tool Argument - SFHA dissolve feature class ####
int_dissolve1 = (Output_GDB+"\\S_FLD_HAZ_AR_"+PolyAnalysis+"_Analysis")

# creat DataFrame from ranking csv
df = pd.read_csv(xlsxPath('SFHA_Rankings.csv'),na_values='')
print(df)

#build fld zone and subtype ranking dictionaries
for value, index in enumerate(df['Flood Zone']):
    FLD_List[value] = index

for value, index in enumerate(df['Subtype']):
    Sub_List[value] = index

# add fld zone and subtype fields back to dissolved feature class
arcpy.management.AddField(int_dissolve1,"FLD_ZONE","TEXT")
arcpy.management.AddField(int_dissolve1,"Subtype","TEXT")

# use ranking to updated flood zone and subtype attribute fields in results table
edit = arcpy.da.Editor(Output_GDB)
edit.startEditing(False, True)

with arcpy.da.UpdateCursor(int_dissolve1, ['FLD_ZONE', 'Subtype','Ranking']) as cursor:
    for row in cursor:
        # Check the condition
        fldzone = FLD_List.get(row[2], 'default_value_for_FLD_ZONE')
        print(fldzone)
        subtype = Sub_List.get(row[2], 'default_value_for_Subtype')
        print(subtype)
        row[0] = fldzone
        cursor.updateRow(row)
        row[1] = subtype
        cursor.updateRow(row)

edit.stopEditing(True)

arcpy.management.CalculateField(int_dissolve1,"Percent_Area","!SUM_Acres! / " + str(sum_field_values(int_dissolve1,"SUM_Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")

### New Tool Argument - Calculated Percent new schema lock ####
int_dissolve2 = (Output_GDB+"\\S_FLD_HAZ_AR_"+PolyAnalysis+"_Analysis")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting Attribute Table...")
arcpy.conversion.TableToTable(int_dissolve2,Output_TBFLD,"S_FLD_HAZ_AR_"+PolyAnalysis+"_Analysis.csv")
arcpy.SetProgressorPosition()