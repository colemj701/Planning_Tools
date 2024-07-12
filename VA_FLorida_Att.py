# Import arcpy module
import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Adding VA Standardized Fields...")

gdb = arcpy.GetParameterAsText(0)

datasets = []
fc_all = []

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def dataset_path(x,y):
    path = os.path.join(x,y)
    return path

def VAattributeadd(x):  # Standard VA_Attribute_add

    # Add required and derived VA attribute fields.
    Field_List = ["EntityName","Asset_Elev","Own_Maintn","Name","Asset","Asset_Type","Asset_Group"]
    FieldType = "TEXT"

    existing_fields = [field.name for field in arcpy.ListFields(x)]

    for fld in Field_List:
        if fld not in existing_fields:
            add_fld = arcpy.management.AddField(x,fld,FieldType)
        else:
            add_fld = None

    return add_fld

env(gdb)

feature_datasets = arcpy.ListDatasets()
for dataset in feature_datasets:
    datasets.append(dataset)
print(datasets)

datset_count = len(datasets)
dataset_paths = []

for ds in datasets:
    ds_path = dataset_path(gdb,ds)
    dataset_paths.append(ds_path)

for dsp in dataset_paths:
    env(dsp)
    print(dsp)
    fclist = arcpy.ListFeatureClasses()

    for fc in fclist:
        fc_desc = arcpy.Describe(fc)
        fc_path = os.path.join(dsp,fc_desc.name)
        fc_all.append(fc_path)
fc_count = len(fc_all)

arcpy.SetProgressor("step","Adding Fields...",0,fc_count)
for fc in fc_all:
    name = os.path.basename(fc)
    arcpy.SetProgressorLabel("adding fields to {0}...".format(name))
    VAattributeadd(str(fc))
    arcpy.SetProgressorPosition()

