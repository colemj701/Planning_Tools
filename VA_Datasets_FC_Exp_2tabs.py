import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Tab Export Tool...")

gdb = arcpy.GetParameterAsText(0)
out_table = arcpy.GetParameterAsText(1)

combined_df = pd.DataFrame() # create DataFrame
excel_writer = pd.ExcelWriter(out_table) # assign existing excel file to have tabs created in
datasets = [] # create empty dataset list
fc_all = [] # create empty fc list
ds_paths = [] # create empty dataset file path list

###----------------------- Tool Functions -----------------------###

def env(x):# set workspace
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):# create file path
    path = os.path.join(x,y)
    return path

###----------------------- Finish Tool Setup -----------------------###
###----------------------- Execute Script Below -----------------------###

###----------------------- Get Dataset Information -----------------------###

env(gdb) # set target workspace

feature_datasets = arcpy.ListDatasets() #list datasets within gdb
for dataset in feature_datasets:
    datasets.append(dataset) #append datasets to empty datasets list

for ds in datasets:
    ds_path = paths(gdb,ds)# use dataset names to create filepaths for the datasets
    ds_paths.append(ds_path)# append file paths to ds_paths list
print(ds_paths)

###----------------------- Query Datasets And Export All FC Attribute Tables -----------------------###

for dsp in ds_paths:# loop through each dataset in the list
    env(dsp)
    fc_list = arcpy.ListFeatureClasses() # get list of feature classes in dataset
    parse_dsp = dsp.split('\\') # split dataset file path at '\\' and create list of items 
    dsp_name = parse_dsp[-1] # return the final item in the dataset path (the dataset name) as string
    dsp_final = dsp_name.replace("_"," ") # replace any '_' with spaces in the dataset name string

    arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list: # query each feature class in the dataset
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name # retrieve fc nam
        fc_path = paths(dsp,fc_name) # build fc file path
        arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

        parse_g = fc_path.split('\\') # split fc file path at '\\' and create list of items 
        group = parse_g[-2] # return the second to last item in the fc path (the dataset name) as string

        parse_t = fc_path.split('\\') # split fc file path at '\\' and create list of items 
        type = parse_t[-1] # return the final item in the fc path (the fc name) as string

        def tab_name(x,y): # function that creates tab names for sheets to be exported to excel
            gsplit = x.split("_") # split dataset name at '_' and create list of items
            group_word_letters = [word[0] for word in gsplit] # return the first letter of each item in the list (first letter of each word in the dataset name)
            group_name_abbr = ''.join(group_word_letters) # create string of letters from retrieved list items

            tsplit = y.split("_") # split fc name at '_' and create list of items
            first_word = tsplit[0] # return the first word of the fc name
            last_word = tsplit[-1] # return the last word of the fc name

            tab = group_name_abbr + "__" + first_word + "_" + last_word # concatenate the tab name using derived data

            return tab

        ###----------------------- Write Excel Table Using Queried Data -----------------------###

        table = arcpy.TableToTable_conversion(fc, 'in_memory', tab_name(group,type)) # convert fc table to excel and create tab name
        fields = [field.name for field in arcpy.ListFields(fc)] # query fields to be populated in excel tab
        data = [row for row in arcpy.da.SearchCursor(fc_path, fields)] # query the data for each row of queried fields
        fc_df = pd.DataFrame(data, columns=fields) # use Pandas to create dataframe structure to be used in excel
        fc_df.to_excel(excel_writer, sheet_name=tab_name(group,type), index=False) # use pandas to write queried data to existing excel spreadsheet
        arcpy.SetProgressorPosition()

excel_writer.save() # save changes to excel workbook


    