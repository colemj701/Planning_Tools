# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.SetProgressor("default","Initiating NWI Acreage Analysis Tool...")

NWI = arcpy.GetParameterAsText(0)
Dis_Fields = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
Output_TBFLD = arcpy.GetParameterAsText(3)
App_text = arcpy.GetParameterAsText(4)
Spa_Ref = arcpy.GetParameterAsText(5)

default_gdb = arcpy.env.scratchGDB

def apptxt(x):
    if x == "":
        txt = ""
    else:
        txt = str(x+"_")
    return txt

# Execute NWI Dissolve
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(NWI,default_gdb+"\\"+str(apptxt(App_text))+"NWI_Acreage_Analysis",Dis_Fields)
arcpy.SetProgressorPosition()

### New Tool Argument - NWI Dissolve Output Feature Class in Default GDB ####
NWI1 = (default_gdb+"\\"+str(apptxt(App_text))+"NWI_Acreage_Analysis")

# Calculate Land Use Areas by NWI
def calcatt(x,y):
    arcpy.SetProgressor("default","Calculating NWI {0}...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(NWI1,[[x,"AREA"]],"",y,Spa_Ref,"")
    arcpy.SetProgressorPosition()
    return calcatt1

calcatt("Acres","ACRES_US"),calcatt("Sq_Mi","SQUARE_MILES_US")

# Calculate Percentages
def sum_field_values(x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(NWI1,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

arcpy.management.CalculateField(NWI1,"Percent_Area","!Acres! / " + str(sum_field_values("Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")


### New Tool Argument - NWI Dissolve Output Feature Class in Default GDB ####
NWI2 = (default_gdb+"\\"+str(apptxt(App_text))+"NWI_Acreage_Analysis")

# Exporting Feature to Output GDB
arcpy.SetProgressor("default","Exporting derived NWI feature class...")
arcpy.management.CopyFeatures(NWI2,Output_GDB+"\\"+str(apptxt(App_text))+"NWI_Acreage_Analysis")
arcpy.SetProgressorPosition()

### New Tool Argument - NWI Dissolve Output Feature Class in Output GDB####
NWI3 = (Output_GDB+"\\"+str(apptxt(App_text))+"NWI_Acreage_Analysis")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting NWI Analysis Attribute Table...")
arcpy.conversion.TableToTable(NWI3,Output_TBFLD,str(apptxt(App_text))+"NWI_Acreage_Analysis.csv")
arcpy.SetProgressorPosition()
