# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
PIN = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
output_folder = arcpy.GetParameterAsText(3)

# Script Argument
default_gdb = arcpy.env.scratchGDB
FDissolve = [PIN,'Type_Oc']

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(input_feature,paths(default_gdb,"Exp_Parcel_By_Occupancy"),FDissolve,[["BldgCost","SUM"],['ContentCos','SUM']])
arcpy.SetProgressorPosition()

dis1 = paths(default_gdb,"Exp_Parcel_By_Occupancy")

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(w,x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(w,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(w,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return parcel_count
parcelcount(dis1,1)

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(dis1,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(dis1,"TotalBldgValue","!SUM_BldgCost! + !SUM_ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

stats = []

for field in arcpy.ListFields(dis1):
    if field.name in ("Parcel_Count","SUM_BldgCost","SUM_ContentCos","TotalBldgValue"):
        stats.append([field.name,"Sum"])

arcpy.analysis.Statistics(dis1,Output_GDB+"\\Exp_Parcel_By_Occupancy_tbl",stats,"Type_oc")

calc_tbl1 = (Output_GDB+"\\Exp_Parcel_By_Occupancy_tbl")

# Export Final Calculated Attribute Table
arcpy.SetProgressor("default","Exporting Hazus 100yr UDF Results table...")
arcpy.conversion.ExportTable(calc_tbl1,output_folder+"\\Exp_Parcel_By_Occupancy.csv","","NOT_USE_ALIAS")
arcpy.SetProgressorPosition()