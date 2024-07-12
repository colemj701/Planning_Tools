# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.SetProgressor("default","Initiating Parcel Exposure By Land Use Tool...")
arcpy.SetProgressorPosition()

# Tool Parameter Arguments
Features = arcpy.GetParameterAsText(0)
Dis_Field1 = arcpy.GetParameterAsText(1)
Dis_Field2 = arcpy.GetParameterAsText(2)
Dis_Field3 = arcpy.GetParameterAsText(3)
Dis_Field4 = arcpy.GetParameterAsText(4)
Output_GDB = arcpy.GetParameterAsText(5)
Output_TBFLD = arcpy.GetParameterAsText(6)
ParcelType = arcpy.GetParameterAsText(7)
LandUse = arcpy.GetParameterAsText(8)
Spa_Ref = arcpy.GetParameterAsText(9)

# Local Tool Arguments
default_gdb = arcpy.env.scratchGDB
FDissolve_Fields1 = [Dis_Field1,Dis_Field2,Dis_Field3,Dis_Field4]
FDissolve_Fields2 = [Dis_Field1,Dis_Field2,Dis_Field4]

# Append String Parameter function
def apptxt(x):
    if x == "":
        txt = ""
    else:
        txt = str(x+"_")
    return txt

# Run initial Intersect
arcpy.SetProgressor("default","Running Intersect Tool...")
arcpy.Intersect_analysis(Features,default_gdb+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_Int_"+LandUse+"_Land_Use","ALL")
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int1 = (default_gdb+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_Int_"+LandUse+"_Land_Use")

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int1,default_gdb+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use_Prep",FDissolve_Fields1)
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int2 = (default_gdb+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use_Prep")

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(int2,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(int2,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return parcel_count
parcelcount(1)

# Execute Dissolve - generate parcel counts per SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int2,Output_GDB+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use",FDissolve_Fields2,[["Parcel_Count","SUM"]])
arcpy.SetProgressorPosition()

### New Tool Argument - Exposure by Land Use Dissolve Output Feature Class ####
int3 = (Output_GDB+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use")

# Calculate Land Use Areas by SFHA
def calcatt(x,y):
    arcpy.SetProgressor("default","Calculating Parcel Land Use {0} by SFHA...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(int3,[[x,"AREA"]],"",y,Spa_Ref,"")
    return calcatt1

calcatt("Acres","ACRES_US"),calcatt("Sq_Mi","SQUARE_MILES_US")

# Calculate Percentages
def sum_field_values(x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(int3,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

arcpy.management.CalculateField(int3,"Percent_Area","!Acres! / " + str(sum_field_values("Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")

### New Tool Argument - New Schema Lock on modified feature ####
int4 = (Output_GDB+"\\"+str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting Exposure by {0} Land Use Attribute Table...".format(LandUse))
arcpy.conversion.TableToTable(int4,Output_TBFLD,str(apptxt(ParcelType))+"_Parcel_Exposure_"+LandUse+"_Land_Use.csv")
