import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Tab Export Tool...")

gdb = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\Florida\Critical_Asset\StCloud_Cristical_Assets_Filtered_Assets.gdb'
out_table = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Filtered_Critical_Asset_Data\Filtered_StCloud_Assets_All_on_One.xlsx'

combined_df = pd.DataFrame()
excel_writer = pd.ExcelWriter(out_table)

datasets = []
fc_all = []
ds_paths = []
all_feature_data = []

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

        Field_List = ["EntityName","Asset_Elev","Own_Maintn","Name","Asset","Asset_Type","Asset_Group"]
        cursor = arcpy.da.SearchCursor(fc, Field_List)
        for row in cursor:
            all_feature_data.append({"Asset_Group":row[6],"Asset_Type":row[5],"Asset":row[4],"Name":row[3],"EntityName":row[0],"Own_Maintn":row[2],"Asset_Elev":row[1]})
        arcpy.SetProgressorPosition()

arcpy.SetProgressor("default", "Writing data to workbook...")
df = pd.DataFrame(all_feature_data)
df.to_excel(excel_writer, sheet_name="AllData", index=False)

excel_writer.save()


    