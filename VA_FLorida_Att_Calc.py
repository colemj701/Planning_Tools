import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Att Calc Tool...")

gdb = arcpy.GetParameterAsText(0)

datasets = []
fc_all = []
fc_paths_all = []
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
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        fc_path = paths(dsp,fc_name)
        fc_paths_all.append(fc_path)
print(fc_paths_all)
fc_count = len(fc_paths_all)

env(gdb)
arcpy.SetProgressor("step","Calculating FC Atts...",0,fc_count)
for fcs in fc_paths_all:
    parse_g = fcs.split('\\')
    group = "'"+parse_g[-2]+"'"

    parse_t = fcs.split('\\')
    type = "'"+parse_t[-1]+"'"

    Calc_Fields = ["Asset_Group","Asset_Type","Asset"]
    arcpy.SetProgressorLabel("Calculating attributes for {0}...".format(type))
    for fld in Calc_Fields:
        def exp(x):
            if x is Calc_Fields[0]:
                ex = group
            elif x is Calc_Fields[1]:
                ex = type
            elif x is Calc_Fields[2]:
                ex = "!NAME!"
            return ex
    
        def calc_att(x):
            c_att = arcpy.management.CalculateField(fcs,x,str(exp(x)),"PYTHON")
            return(c_att)

        calc_att(fld)
    arcpy.SetProgressorPosition()
    