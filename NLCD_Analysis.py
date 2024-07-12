# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")

arcpy.SetProgressor("default","Initiating NLCD Tool...")

MaskFeature = arcpy.GetParameterAsText(0)
RasterLyr = arcpy.GetParameterAsText(1)
Output_GDB = arcpy.GetParameterAsText(2)
Output_TBFLD = arcpy.GetParameterAsText(3)
buf_dist = arcpy.GetParameterAsText(4)
NLCD_yr = arcpy.GetParameterAsText(5)
Spa_Ref = arcpy.GetParameterAsText(6)

default_gdb = arcpy.env.scratchGDB

MaskFLyr = arcpy.management.MakeFeatureLayer(MaskFeature,"Mask_Layer")

# Extract NLCD using buffer distance if provided and mask feature if no buffer distance provided
def mask(x):
    arcpy.SetProgressor("default","Extracting NLCD Area...")
    MaskBufLyr = arcpy.management.MakeFeatureLayer(arcpy.analysis.PairwiseBuffer(MaskFLyr,default_gdb+"\\NLCD_Buffer",x,"NONE","","PLANAR"),"Mask_Buf_Layer")
    NLCD = ExtractByMask(RasterLyr,MaskBufLyr,"INSIDE")
    NLCD.save(Output_GDB+"\\NLCD_"+NLCD_yr)
    
mask(buf_dist)

### New Tool Argument (NLCD Raster in GDB) ###
NLCD = Output_GDB+"\\NLCD_"+NLCD_yr

# Execute Zonal Geometry, and export zonal geo and raster reference tables.
arcpy.env.workspace = Output_GDB
ZonalGeo = ZonalGeometryAsTable(NLCD,"Value","NLCD_"+NLCD_yr+"_ZonalGeo")
ZonalGeo1 = Output_GDB+"\\NLCD_"+NLCD_yr+"_ZonalGeo"
arcpy.SetProgressor("default","Executing Zonal Geometry Table...")
arcpy.conversion.TableToTable(ZonalGeo1,Output_TBFLD,"NLCD_"+NLCD_yr+"_ZonalGeo.csv")
arcpy.SetProgressorPosition()
arcpy.SetProgressor("default","Exporting Raster Reference Table...")
arcpy.conversion.TableToTable(NLCD,Output_TBFLD,"NLCD_"+NLCD_yr+"_Reference.csv")
arcpy.SetProgressorPosition()


# Convert Raster to Polygon for further analysis
arcpy.SetProgressor("default","Converting NLCD Raster to Polygon Feature...")
arcpy.conversion.RasterToPolygon(NLCD,Output_GDB+"\\NLCD_"+NLCD_yr+"_Poly","","NLCD_Land_Cover_Class")
arcpy.SetProgressorPosition()

### New Tool Argument (NLCD Polygon Feature Class in GDB) ###
NLCD1 = Output_GDB+"\\NLCD_"+NLCD_yr+"_Poly"

# Calculate Intersect Areas
def calcatt(x,y):
    arcpy.SetProgressor("default","Calculating NLCD Areas...")
    calcatt1 = arcpy.management.CalculateGeometryAttributes(NLCD1,[[x,"AREA"]],"",y,Spa_Ref,"")
    arcpy.SetProgressorPosition()
    return calcatt1

# Calculate acres and square miles
calcatt("Acres","ACRES_US"),calcatt("Sq_Mi","SQUARE_MILES_US")

# Execute Dissolve
arcpy.SetProgressor("default","Executing NLCD Polygon Dissolve...")
arcpy.management.Dissolve(NLCD1,Output_GDB+"\\NLCD_"+NLCD_yr+"_Poly_Dissolve","NLCD_Land_Cover_Class",[["Acres","SUM"],["Sq_Mi","SUM"]])
arcpy.SetProgressorPosition()


### New Tool Argument (NLCD Polygon Dissolve in GDB) ###
NLCD2 = Output_GDB+"\\NLCD_"+NLCD_yr+"_Poly_Dissolve"

# Calculate Percentages
def sum_field_values(x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(NLCD2,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

arcpy.management.CalculateField(NLCD2,"Percent_Area","!SUM_Acres! / " + str(sum_field_values("SUM_Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")

# Export Attribute Table
arcpy.SetProgressor("default","Exporting Final NLCD Attribute Table...")
arcpy.conversion.TableToTable(NLCD2,Output_TBFLD,"NLCD_"+NLCD_yr+".csv")
arcpy.SetProgressorPosition()
