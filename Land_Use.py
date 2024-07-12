# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.SetProgressor("default","Initiating Exposure By Land Use Tool...")

# Tool Parameter Arguments
Features = arcpy.GetParameterAsText(0)
Output_GDB = arcpy.GetParameterAsText(1)
Output_TBFLD = arcpy.GetParameterAsText(2)
Dis_Field1 = arcpy.GetParameterAsText(3)
P_Status = arcpy.GetParameterAsText(4)
LandUse = arcpy.GetParameterAsText(5)
Spa_Ref = arcpy.GetParameterAsText(6)
arcpy.SetProgressorPosition()

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.management.AddField(Features,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(Features,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    arcpy.SetProgressorPosition()
    return parcel_count
parcelcount(1)

# Execute Dissolve - Dissolve by Landuse
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(Features,Output_GDB+"\\"+LandUse+"_Land_Use_{0}_Parcels_Calc".format(P_Status),Dis_Field1,[["Parcel_Count","SUM"]])
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
dis1 = (Output_GDB+"\\"+LandUse+"_Land_Use_{0}_Parcels_Calc".format(P_Status))

# Calculate Land Use Areas by SFHA
def calcatt(x,y):
    arcpy.SetProgressor("default","Calculating {0} of Land Use...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(dis1,[[x,"AREA"]],"",y,Spa_Ref,"")
    arcpy.SetProgressorPosition()
    return calcatt1

calcatt("Acres","ACRES_US"),calcatt("Sq_Mi","SQUARE_MILES_US")

# Calculate Percentages
def sum_field_values(x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(dis1,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

arcpy.management.CalculateField(dis1,"Percent_Area","!Acres! / " + str(sum_field_values("Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")


#Export Attribute Table
arcpy.SetProgressor("default","Exporting Exposure by {0} Land Use Attribute Table...".format(LandUse))
arcpy.conversion.TableToTable(dis1,Output_TBFLD,LandUse+"_Land_Use_{0}_Parcels_Calc.csv".format(P_Status))
arcpy.SetProgressorPosition()