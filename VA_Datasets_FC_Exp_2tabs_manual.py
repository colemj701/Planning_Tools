import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Tab Export Tool...")

gdb = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\Florida\Critical_Asset\Boundary_Redo\St_Cloud_Assets.gdb'
out_table = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Critical_Assets\Filtered_St_Cloud_Assets_by_tabs.xlsx'

combined_df = pd.DataFrame()
excel_writer = pd.ExcelWriter(out_table)
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
        fc_path = paths(dsp,fc_name)
        arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

        parse_g = fc_path.split('\\')
        group = parse_g[-2]

        parse_t = fc_path.split('\\')
        type = parse_t[-1]

        def tab_name(x,y):
            gsplit = x.split("_")
            group_word_letters = [word[0] for word in gsplit]
            group_name_abbr = ''.join(group_word_letters)

            tsplit = y.split("_")
            first_word = tsplit[0]
            last_word = tsplit[-1]

            tab = group_name_abbr + "__" + first_word + "_" + last_word

            return tab

        table = arcpy.TableToTable_conversion(fc, 'in_memory', tab_name(group,type))
        fields = [field.name for field in arcpy.ListFields(fc)]
        data = [row for row in arcpy.da.SearchCursor(fc_path, fields)]
        fc_df = pd.DataFrame(data, columns=fields)
        fc_df.to_excel(excel_writer, sheet_name=tab_name(group,type), index=False)
        arcpy.SetProgressorPosition()

excel_writer.save()


    