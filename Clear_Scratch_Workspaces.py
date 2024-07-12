import arcpy, os

default_gdb = arcpy.env.scratchGDB

arcpy.env.workspace = default_gdb

arcpy.SetProgressor("default", "Initiating Clear scratchGDB Tool...")

fc_count = len(arcpy.ListFeatureClasses())
raster_count = len(arcpy.ListRasters())
tb_count = len(arcpy.ListTables())

arcpy.SetProgressor("step", "Deleting feature classes from scratchGDB...",0,fc_count,1)
fc_list = arcpy.ListFeatureClasses()
for fc in fc_list:
    arcpy.SetProgressorLabel('Deleting "{0}" from scratchGDB...'.format(fc))
    arcpy.Delete_management(fc)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting raster layers from scratchGDB...",0,raster_count,1)
Raster_list = arcpy.ListRasters()
for raster in Raster_list:
    arcpy.SetProgressorLabel('Deleting "{0}" from scratchGDB...'.format(raster))
    arcpy.Delete_management(raster)
    arcpy.SetProgressorPosition()

arcpy.SetProgressor("step", "Deleting tables from scratchGDB...",0,tb_count,1)
tb_list = arcpy.ListTables()
for table in tb_list:
    arcpy.SetProgressorLabel('Deleting "{0}" from scratchGDB...'.format(table))
    arcpy.Delete_management(table)
    arcpy.SetProgressorPosition()