import os,sys, arcpy
import pandas as pd
import numpy as np
from arcpy.sa import* 

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

gdb = arcpy.GetParameterAsText(0)
DEM = arcpy.GetParameterAsText(1)

datasets = []
fc_all = []
ds_paths = []
fc_dict = {}
fc_dictx = {}

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

env(gdb)

feature_datasets = arcpy.ListDatasets()
for dataset in feature_datasets:
    datasets.append(dataset)

for ds in datasets:
    ds_path = paths(gdb,ds)
    ds_paths.append(ds_path)

for dsp in ds_paths:
    env(dsp)
    fc_list = arcpy.ListFeatureClasses()
    parse_dsp = dsp.split('\\')
    dsp_name = parse_dsp[-1]
    dsp_final = dsp_name.replace("_"," ")

    arcpy.SetProgressor("Step","Calculating Z for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        fc_path = paths(dsp,fc_name)
        spa = fc_desc.SpatialReference
        geo_type = fc_desc.shapeType
        arcpy.SetProgressorLabel("Calculating Z for {0} assets...".format(fc_name.replace("_"," ")))

        def exp_geo_point(inFt,inRas):

            arcpy.management.CalculateField(
                in_table=inFt, 
                field='Z', 
                expression='None', 
                expression_type='PYTHON3'
            )

            addZ = AddSurfaceInformation(
                in_feature_class=inFt,
                in_surface=inRas,
                out_property="Z",
                method="BILINEAR")

            return addZ
        
        if geo_type == 'Point':
            exp_geo_point(fc_path,DEM)

        arcpy.SetProgressorPosition()
