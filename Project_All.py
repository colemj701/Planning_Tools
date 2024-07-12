
# Import arcpy module
import arcpy, os, sys
arcpy.env.workspace = arcpy.GetParameterAsText(0)
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating Project All Features tool...")

# Script Arguments 1 Project Area 2 Target Output 3 workspace 4 output coordinate system
Output_GDB = arcpy.GetParameterAsText(1)

Output_Coordinate_System = arcpy.GetParameterAsText(2)

# Process: Project All Features Within Given Workspace
FCs = arcpy.ListFeatureClasses()
fc_count = len(FCs)
arcpy.SetProgressor("step","Projecting data...",0,fc_count,1)
for fc in FCs:
    desc = arcpy.Describe(fc)
    arcpy.SetProgressorLabel('Projecting "{0}"...'.format(desc.name))
    arcpy.management.Project(fc, Output_GDB + os.sep + fc.rstrip(".shp"), Output_Coordinate_System)
    arcpy.SetProgressorPosition()

