# Import arcpy module
import arcpy, time, os, sys
import pandas as pd
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating HAZUS Analysis...")

HAZUS_FP = arcpy.GetParameterAsText(0)
FHA = arcpy.GetParameterAsText(1)
Dis_Fld = arcpy.GetParameterAsText(2)
Output_GDB = arcpy.GetParameterAsText(3)
output_folder = arcpy.GetParameterAsText(4)

FLD_List = {}
Sub_List = {}

# Script Argument
default_gdb = arcpy.env.scratchGDB

arcpy.SetProgressor("default","Joining HAZUS Results and FHA data...")
join_fm = arcpy.FieldMappings() # create a field map object
join_fm.addTable(HAZUS_FP) # add the HAZUS atrributes fields to the object
join_fm.addTable(FHA) # add the FHA attributes to the object


# get the location of the csv template file in FFRMS_Bin
def xlsxPath(x):
    cDir = os.getcwd()
    xsNm = x
    exPath = os.path.join(cDir,xsNm)
    return exPath

arcpy.SetProgressor("default","Joining HAZUS Results and FHA data...")
join_fm = arcpy.FieldMappings() # create a field map object
join_fm.addTable(HAZUS_FP) # add the HAZUS atrributes fields to the object
join_fm.addTable(FHA) # add the FHA attributes to the object


join_fc = default_gdb+"\\HAZUS_FHA_Join"
arcpy.analysis.SpatialJoin(HAZUS_FP,FHA,join_fc,"JOIN_ONE_TO_ONE","KEEP_ALL",join_fm,"INTERSECT")

calc_tbl = default_gdb+"\\HAZUS_FHA_Join"

arcpy.SetProgressor("default","Adding Hazus Summary Fields...")

# Add building count field and auto fill value of 1 for each row
def buildingcount(x):
    arcpy.SetProgressor("default","Adding Building Count Values...")
    arcpy.management.AddField(calc_tbl,"Bldg_Count","DOUBLE")
    bldg_count = arcpy.management.CalculateField(calc_tbl,"Bldg_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    arcpy.SetProgressorPosition()
    return bldg_count
buildingcount(1)

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(calc_tbl,"TotalBldgValue","DOUBLE")

time.sleep(2) # delay script for 2 seconds

arcpy.management.CalculateField(calc_tbl,"TotalBldgValue","!BldgCost! + !ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

time.sleep(2) # delay script for 2 seconds

# Add Total Damage field and calculate from existing fields
arcpy.SetProgressor("default","Adding Estimated Total Damage Values...")
arcpy.management.AddField(calc_tbl,"EstTot_Damage","DOUBLE")

time.sleep(2) # delay script for 2 seconds

arcpy.management.CalculateField(calc_tbl,"EstTot_Damage","!BldgLossUS! + !ContentLos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

# Run Summary Statistics for output table
arcpy.SetProgressor("default","Calculating HAZUS Results Table Data...")
dissolve_fields = ["Type_oc",Dis_Fld]
arcpy.management.Dissolve(calc_tbl,default_gdb+"\\HAZUS_FHA_Dissolve",dissolve_fields,[["Bldg_Count","SUM"],["EstTot_Damage","SUM"],["ContentLos","SUM"],["TotalBldgValue","SUM"],["BldgLossUS","SUM"]])

time.sleep(2) # delay script for 2 seconds

calc_tbl1 = default_gdb+"\\HAZUS_FHA_Dissolve"

# creat DataFrame from ranking csv
df = pd.read_csv(xlsxPath('SFHA_Rankings.csv'),na_values='')
print(df)


#build fld zone and subtype rankings
for value, index in enumerate(df['Flood Zone']):
    FLD_List[value] = index

for value, index in enumerate(df['Subtype']):
    Sub_List[value] = index


calc_tbl1 = default_gdb+"\\HAZUS_FHA_Dissolve"

# Add Loss Ratio field and calculate from existing fields
arcpy.SetProgressor("default","Adding Loss Ratio Values...")
arcpy.management.AddField(calc_tbl1,"LossRatio","DOUBLE")
arcpy.management.AddField(calc_tbl1,"FLD_ZONE","TEXT")
arcpy.management.AddField(calc_tbl1,"Subtype","TEXT")



# use ranking to updated flood zone and subtype attribute fields in results table
edit = arcpy.da.Editor(default_gdb)
edit.startEditing(False, True)

with arcpy.da.UpdateCursor(calc_tbl1, ['FLD_ZONE', 'Subtype','Ranking']) as cursor:
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


arcpy.management.CalculateField(calc_tbl1,"LossRatio","!SUM_EstTot_Damage! / !SUM_TotalBldgValue!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

time.sleep(2)

# Lines 61-79 reorder the fields of the output table to meet the format of the HAZUS table
# Get a list of field names in the current order
fields = arcpy.ListFields(calc_tbl1)
field_names = [fld.name for fld in arcpy.ListFields(calc_tbl1)]

# Specify the desired field order
out_fld_order = ["OBJECTID","Type_Oc",'FLD_ZONE','Subtype',"SUM_Bldg_Count","SUM_TotalBldgValue","SUM_BldgLossUS","SUM_ContentLos","SUM_EstTot_Damage","LossRatio"]

# Create a new field mapping object
fm = arcpy.FieldMappings()

# Add fields to the field mapping in the desired order
for fld_nm in out_fld_order:
    # assign index to field based on output list order
    field_index2 = field_names.index(fld_nm)
    # create field map object
    field_map = arcpy.FieldMap()
    # add the input fields from the input feature class
    field_map.addInputField(calc_tbl1,fld_nm)
    # add the new field map for each field to the field mappings parameter
    fm.addFieldMap(field_map)

# Copy the table to a new table with reordered fields
output_table = "HAZUS_100yr_UDF_Results_By_Flood_Zone.csv"
arcpy.conversion.TableToTable(calc_tbl1, output_folder, output_table,"",fm)
arcpy.SetProgressorPosition()
