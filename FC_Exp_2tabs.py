import arcpy, os, sys
import pandas as pd
arcpy.env.overwriteOutput = True

arcpy.SetProgressor("default","Initiating VA Tab Export Tool...")

gdb = arcpy.GetParameterAsText(0)
out_table = arcpy.GetParameterAsText(1)

combined_df = pd.DataFrame() # create DataFrame
excel_writer = pd.ExcelWriter(out_table, engine='xlsxwriter') # assign existing excel file to have tabs created in
fc_all = [] # create empty fc list

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

fc_list = arcpy.ListFeatureClasses() # get list of feature classes in dataset
parse_gdb = gdb.split('\\') # split dataset file path at '\\' and create list of items 
gdb_name = parse_gdb[-1] # return the final item in the dataset path (the dataset name) as string
gdb_final = gdb_name.replace("_"," ") # replace any '_' with spaces in the dataset name string

arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(gdb_final),0,len(fc_list))
for fc in fc_list: # query each feature class in the dataset
    fc_desc = arcpy.Describe(fc)
    fc_name = fc_desc.name # retrieve fc nam
    fc_path = paths(gdb,fc_name) # build fc file path
    arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

    ###----------------------- Write Excel Table Using Queried Data -----------------------###

    table = arcpy.TableToTable_conversion(fc, 'in_memory', fc_name) # convert fc table to excel and create tab name
    fields = [field.name for field in arcpy.ListFields(fc)] # query fields to be populated in excel tab
    data = [row for row in arcpy.da.SearchCursor(fc_path, fields)] # query the data for each row of queried fields
    fc_df = pd.DataFrame(data, columns=fields) # use Pandas to create dataframe structure to be used in excel
    fc_df.to_excel(excel_writer, sheet_name=fc_name, index=False) # use pandas to write queried data to existing excel spreadsheet
    arcpy.SetProgressorPosition()

excel_writer.save() # save changes to excel workbook


    