# Import arcpy module
import arcpy, time, os, sys
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating HAZUS Results Tool...")

HAZUS_FP = arcpy.GetParameterAsText(0)
Output_GDB = arcpy.GetParameterAsText(1)
output_folder = arcpy.GetParameterAsText(2)

# Script Argument
default_gdb = arcpy.env.scratchGDB


arcpy.management.CopyFeatures(HAZUS_FP,default_gdb+"\\HAZUS_Copy")

calc_tbl = default_gdb+"\\HAZUS_Copy"

arcpy.SetProgressor("default","Adding Hazus Fields...")

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

time.sleep(2) # delay script for 2 seconds

# Run Summary Statistics for output table
arcpy.SetProgressor("default","Calculating HAZUS Results Table Data...")
arcpy.management.Dissolve(calc_tbl,default_gdb+"\\HAZUS_Copy_Dissolve","Type_Oc",[["Bldg_Count","SUM"],["EstTot_Damage","SUM"],["ContentLos","SUM"],["TotalBldgValue","SUM"],["BldgLossUS","SUM"]])

time.sleep(2) # delay script for 2 seconds

calc_tbl1 = default_gdb+"\\HAZUS_Copy_Dissolve"

# Add Loss Ratio field and calculate from existing fields
arcpy.SetProgressor("default","Adding Loss Ratio Values...")
arcpy.management.AddField(calc_tbl1,"LossRatio","DOUBLE")

time.sleep(2) # delay script for 2 seconds

arcpy.management.CalculateField(calc_tbl1,"LossRatio","!SUM_EstTot_Damage! / !SUM_TotalBldgValue!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

time.sleep(2)

# Lines 61-79 reorder the fields of the output table to meet the format of the HAZUS table
# Get a list of field names in the current order
fields = arcpy.ListFields(calc_tbl1)
field_names = [fld.name for fld in arcpy.ListFields(calc_tbl1)]

# Specify the desired field order
out_fld_order = ["OBJECTID","Type_Oc","SUM_Bldg_Count","SUM_TotalBldgValue","SUM_BldgLossUS","SUM_ContentLos","SUM_EstTot_Damage","LossRatio"]

# Create a new field mapping object
fm = arcpy.FieldMappings()

# Add fields to the field mapping in the desired order
for fld_nm in out_fld_order:
    # assign index to field based on output list order
    field_index = field_names.index(fld_nm)
    # create field map object
    field_map = arcpy.FieldMap()
    # add the input fields from the input feature class
    field_map.addInputField(calc_tbl1,fld_nm)
    # add the new field map for each field to the field mappings parameter
    fm.addFieldMap(field_map)

# Copy the table to a new table with reordered fields
output_table = "HAZUS_100yr_UDF_Results.csv"
arcpy.conversion.TableToTable(calc_tbl1, output_folder, output_table,"",fm)
arcpy.SetProgressorPosition()
