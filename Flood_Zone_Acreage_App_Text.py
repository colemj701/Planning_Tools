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

arcpy.SetProgressor("default","Initiating FHA Acreage Analysis Tool...")

SFHA = arcpy.GetParameterAsText(0)
Dis_Fields = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
Output_TBFLD = arcpy.GetParameterAsText(3)
App_text = arcpy.GetParameterAsText(4)
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

# get the file name from a given file path
def get_file_name(file_path):
    return Path(file_path).name

# get a list of keys from the dictionary that match the list of target values - 
# the list will build in the order of the dictionary and list
def get_keys_by_value(dictionary, target_value):
    key_list = []
    for key, value in dictionary.items():
        if value == target_value:
            key_list.append(key)
    return key_list

# build string to append
def apptxt(x):
    if x == "":
        txto = ""
    else:
        txt = str(x.replace(" ","_"))
        txto = str(txt+"_")
    return txto

# Calculate Land Use Areas by SFHA
def calcatt(w,x,y):
    arcpy.SetProgressor("default","Calculating FHA {0}...".format(y))
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

# Execute SFHA Dissolve
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(SFHA,default_gdb+"\\"+str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis",Dis_Fields)
arcpy.SetProgressorPosition()

### New Tool Argument - SFHA Dissolve Output Feature Class in Default GDB ####
SFHA1 = (default_gdb+"\\"+str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis")

calcatt(SFHA1,"Acres","ACRES_US"),calcatt(SFHA1,"Sq_Mi","SQUARE_MILES_US")

arcpy.management.CalculateField(SFHA1,"Percent_Area","!Acres! / " + str(sum_field_values(SFHA1,"Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")

### New Tool Argument - SFHA Dissolve Output Feature Class in Default GDB ####
SFHA2 = (default_gdb+"\\"+str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis")

# creat DataFrame from ranking csv
df = pd.read_csv(xlsxPath('SFHA_Rankings.csv'),na_values='')
print(df)


#build fld zone and subtype ranking dictionaries
for value, index in enumerate(df['Flood Zone']):
    FLD_List[value] = index

for value, index in enumerate(df['Subtype']):
    Sub_List[value] = index

# add fld zone and subtype fields back to dissolved feature class
arcpy.management.AddField(SFHA2,"FLD_ZONE","TEXT")
arcpy.management.AddField(SFHA2,"Subtype","TEXT")

# use ranking to updated flood zone and subtype attribute fields in results table
edit = arcpy.da.Editor(default_gdb)
edit.startEditing(False, True)

with arcpy.da.UpdateCursor(SFHA2, ['FLD_ZONE', 'Subtype','Ranking']) as cursor:
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

# Exporting Feature to Output GDB
arcpy.SetProgressor("default","Exporting derived FHA feature class...")
arcpy.management.CopyFeatures(SFHA2,Output_GDB+"\\"+str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis")
arcpy.SetProgressorPosition()

### New Tool Argument - SFHA Dissolve Output Feature Class in Output GDB####
SFHA3 = (Output_GDB+"\\"+str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting FHA Analysis Attribute Table...")
arcpy.conversion.TableToTable(SFHA3,Output_TBFLD,str(apptxt(App_text))+"S_FLD_HAZ_AR_Acreage_Analysis.csv")
arcpy.SetProgressorPosition()
