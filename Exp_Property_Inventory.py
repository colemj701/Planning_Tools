# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
Output_GDB = arcpy.GetParameterAsText(1)
output_folder = arcpy.GetParameterAsText(2)

# Script Argument
default_gdb = arcpy.env.scratchGDB

# Copy feature attribute table for derived calculations
arcpy.SetProgressor("default","Copying Hazus Point Feature Attribute table...")
arcpy.conversion.ExportTable(input_feature,default_gdb+"\\Exp_Property_Inventory","","NOT_USE_ALIAS")
arcpy.SetProgressorPosition()

calc_tbl = default_gdb+"\\Exp_property_Inventory"

arcpy.SetProgressor("default","Adding Property Inventory Fields...")

# Add Building count field and auto fill value of 1 for each row
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
arcpy.management.CalculateField(calc_tbl,"TotalBldgValue","!BldgCost! + !ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

stats = []

for field in arcpy.ListFields(calc_tbl):
    if field.name in ("Bldg_Count","BldgCost","ContentCos","TotalBldgValue"):
        stats.append([field.name,"Sum"])

arcpy.analysis.Statistics(calc_tbl,Output_GDB+"\\Exp_Property_Inventory",stats,"Type_oc")

calc_tbl1 = (Output_GDB+"\\Exp_Property_Inventory")

# Export Final Calculated Attribute Table
arcpy.SetProgressor("default","Exporting Hazus 100yr UDF Results table...")
arcpy.conversion.ExportTable(calc_tbl1,output_folder+"\\Exp_Property_Inventory.csv","","NOT_USE_ALIAS")
arcpy.SetProgressorPosition()