import arcpy, os, sys

arcpy.SetProgressor("default", "Initiating Clear Data Development GDBs Tool...")

def ws(x):
    arcpy.env.workspace = os.path.join(os.path.dirname(os.path.dirname(__file__)), x)
    return arcpy.env.workspace

ws("Temp_Processing.gdb")

fc_count = len(arcpy.ListFeatureClasses())
raster_count = len(arcpy.ListRasters())
tb_count = len(arcpy.ListTables())

arcpy.SetProgressor("step", "Deleting Temp_Processing.gdb Feature Classes...",0,fc_count,1)
list1 = arcpy.ListFeatureClasses()
for fc in list1:
    arcpy.SetProgressorLabel('Deleting "{0}" from Temp_Processing.gdb...'.format(fc))
    arcpy.Delete_management(fc)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting Temp_Processing.gdb Raster Layers...",0,raster_count,1)
Raster_list1 = arcpy.ListRasters()
for raster in Raster_list1:
    arcpy.SetProgressorLabel('Deleting "{0}" from Temp_Processing.gdb...'.format(raster))
    arcpy.Delete_management(raster)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting Temp_Processing.gdb Tables...",0,tb_count,1)
tb_list1 = arcpy.ListTables()
for table in tb_list1:
    arcpy.SetProgressorLabel('Deleting "{0}" from Temp_Processing.gdb...'.format(table))
    arcpy.Delete_management(table)
    arcpy.SetProgressorPosition()

ws("Work.gdb")

fc_count1 = len(arcpy.ListFeatureClasses())
raster_count1 = len(arcpy.ListRasters())
tb_count1 = len(arcpy.ListTables())

arcpy.SetProgressor("step", "Deleting Work.gdb Feature Classes...",0,fc_count1,1)
list2 = arcpy.ListFeatureClasses()
for fc in list2:
    arcpy.SetProgressorLabel('Deleting "{0}" from Work.gdb...'.format(fc))
    arcpy.Delete_management(fc)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting Work.gdb Raster Layers...",0,raster_count1,1)
Raster_list2 = arcpy.ListRasters()
for raster in Raster_list2:
    arcpy.SetProgressorLabel('Deleting "{0}" from Work.gdb...'.format(raster))
    arcpy.Delete_management(raster)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting Work.gdb Tables...",0,tb_count1,1)
tb_list2 = arcpy.ListTables()
for table in tb_list2:
    arcpy.SetProgressorLabel('Deleting "{0}" from Work.gdb...'.format(table))
    arcpy.Delete_management(table)
    arcpy.SetProgressorPosition()