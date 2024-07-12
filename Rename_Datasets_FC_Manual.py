import arcpy, os, sys, errno
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Tab Export Tool...")

gdb = r'C:\Project_Files\GIS\HMP\St_Cloud\4.0 Reference Data\Florida\Critical_Asset\Data_Deliverable_033124\Exposure_Data\St_Cloud_Assets.gdb'
old = '_exposure_results'
new = ''
app = 'N'

datasets = []
fc_all = []
ds_paths = []

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
print(ds_paths)


for dsp in ds_paths:
    env(dsp)
    fc_list = arcpy.ListFeatureClasses()
    parse_dsp = dsp.split('\\')
    dsp_name = parse_dsp[-1]
    dsp_final = dsp_name.replace("_"," ")

    arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        print(f'Original FC Name :: {fc_name}')
        fc_path = paths(dsp,fc_name)
        arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

        def rename(x,y,z):
            new_name = x.replace(y,z)
            print(f'New FC name :: {new_name}')
            try:
                arcpy.management.Rename(x,new_name)
                print(f'Revised {x} to : {new_name}')
            except (Exception, OSError) as e:
                print(f'"A process error occurred \n{e}')

        def append(x,y):
            new_name = x + '_' + y
            print(f'New FC name :: {new_name}')
            try:
                arcpy.management.Rename(x,new_name)
                print(f'Revised {x} to : {new_name}')
            except (Exception, OSError) as e:
                print(f'"A process error occurred \n{e}')

        if fc_name.endswith(old):
            rename(fc_name,old,new)
        
        elif app == 'Y':
            append(fc_name,new)



    