
# Import arcpy module
import arcpy, os, sys
# Script Argument - environment settings
arcpy.env.workspace = arcpy.GetParameterAsText(0)
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating Batch Shapefile Export tool...")

# Script Argument
Output_FLD = arcpy.GetParameterAsText(1)

# Process: Export all features as shapefiles to the output folder.
FCs = arcpy.ListFeatureClasses()
fc_count = len(FCs)
for fc in FCs:
    arcpy.SetProgressor("step","Exporting data...",0,fc_count,1)
    desc = arcpy.Describe(fc)
    arcpy.SetProgressorLabel('Exporting "{0}" to .shp...'.format(desc.name))
    arcpy.conversion.FeatureClassToShapefile(fc,Output_FLD)
    arcpy.SetProgressorPosition()

