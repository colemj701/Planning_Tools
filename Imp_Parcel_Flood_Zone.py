# Import arcpy module
import arcpy, time, os, sys
import pandas as pd
import numpy as np
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
arcpy.env.overwriteOutput = True
from arcpy.sa import*
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.SetProgressor("default","Initiating Exposure By Land Use Tool...")

# Tool Parameter Arguments
Features = arcpy.GetParameterAsText(0)
Ranking = arcpy.GetParameterAsText(1)
PIN = arcpy.GetParameterAsText(2)
Output_GDB = arcpy.GetParameterAsText(3)
Output_TBFLD = arcpy.GetParameterAsText(4)
ParceType = arcpy.GetParameterAsText(5)
Spa_Ref = arcpy.GetParameterAsText(6)

# Local Tool Arguments
default_gdb = arcpy.env.scratchGDB
FDissolve_Fields = [Ranking,PIN]

FLD_List = {}
Sub_List = {}

# set processing environment
def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# Append String Parameter function
def apptxt(x):
    if x == "":
        txto = ""
    else:
        txt = x.replace(" ","_")
        txto = str(txt+"_")
    return txto

# get the location of the csv template file in FFRMS_Bin
def xlsxPath(x):
    cDir = os.getcwd()
    xsNm = x
    exPath = os.path.join(cDir,xsNm)
    return exPath

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(w,x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.management.AddField(w,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(w,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    arcpy.SetProgressorPosition()
    return parcel_count

# Calculate Land Use Areas by SFHA
def calcatt(w,x,y):
    arcpy.SetProgressor("default","Calculating Parcel {0} by FHA...".format(y))
    calcatt1 = arcpy.management.CalculateGeometryAttributes(w,[[x,"AREA"]],"",y,Spa_Ref,"")
    arcpy.SetProgressorPosition()
    return calcatt1

# Calculate Percentages
def sum_field_values(w,x):
    arcpy.SetProgressor("default","Calculating Percent Area...")
    total = 0
    with arcpy.da.SearchCursor(w,x) as cursor:
        for row in cursor:
            total += row[0]
    arcpy.SetProgressorPosition()
    return total

def df_exp_parcel(w,x,y,z):
    # w is feature class
    # x is fields list
    # y is Parcel ID
    # z is output csv
    arcpy.SetProgressor('default','Preparing results table...')
    # Reading feature class data into a pandas DataFrame
    data = [row for row in arcpy.da.SearchCursor(w, x)]
    df = pd.DataFrame(data, columns=x)

    df.fillna(np.nan, inplace=True)

    # Finding the row with the maximum ranking for each PIN
    result = df.loc[df.groupby(y)['Ranking'].idxmax()]

    # Creating a new DataFrame with the results
    new_df = result[[y, 'Ranking','FLD_ZONE','Subtype']].reset_index(drop=True)

    # Calculate frequency of each unique Ranking in the entire DataFrame 'new_df'
    frequency = new_df['Ranking'].value_counts()

    # Create a DataFrame with specified columns ('Ranking', 'Frequency', 'FLD_ZONE', 'Subtype')
    new1_df = pd.DataFrame(columns=['Ranking', 'Frequency', 'FLD_ZONE', 'Subtype'])

    for rank in frequency.index:
        rank_data = new_df[new_df['Ranking'] == rank]
        FLD_List[rank] = rank_data['FLD_ZONE'].iloc[0]
        Sub_List[rank] = rank_data['Subtype'].iloc[0]

    # Create a DataFrame with specified columns ('Ranking', 'Frequency', 'FLD_ZONE', 'Subtype')
    new1_df = pd.DataFrame(columns=['Ranking', 'Frequency', 'FLD_ZONE', 'Subtype'])

    for rank in frequency.index:
        frequency_count = frequency[rank]

        # Get FLD_ZONE and Subtype values using the dictionaries
        fld_zone = FLD_List[rank]
        subtype = Sub_List[rank]

        # Append the row to the DataFrame
        new1_df = new1_df.append({
            'Ranking': rank,
            'Frequency': frequency_count,
            'FLD_ZONE': fld_zone,
            'Subtype': subtype
        }, ignore_index=True)

    # Write the resulting DataFrame to a CSV file
    new1_df.to_csv(z, mode='w', header=True, index=True)
    arcpy.SetProgressorPosition()

    return True

def rank(x,y):# creat DataFrame from ranking csv
    # x is in feature class
    # y is target gdb
    arcpy.SetProgressor('default','Building FLD Zone Ranking...')
    df = pd.read_csv(xlsxPath('SFHA_Rankings.csv'),na_values='')

    #build fld zone and subtype ranking dictionaries
    for value, index in enumerate(df['Flood Zone']):
        FLD_List[value] = index

    for value, index in enumerate(df['Subtype']):
        Sub_List[value] = index

    # add fld zone and subtype fields back to dissolved feature class
    arcpy.management.AddField(x,"FLD_ZONE","TEXT")
    arcpy.management.AddField(x,"Subtype","TEXT")

    # use ranking to update flood zone and subtype attribute fields in results table
    edit = arcpy.da.Editor(y)
    edit.startEditing(False, True)

    with arcpy.da.UpdateCursor(x, ['FLD_ZONE', 'Subtype','Ranking']) as cursor:
        for row in cursor:
            # Check the condition
            fldzone = FLD_List.get(row[2], 'default_value_for_FLD_ZONE')
            subtype = Sub_List.get(row[2], 'default_value_for_Subtype')
            row[0] = fldzone
            cursor.updateRow(row)
            row[1] = subtype
            update = cursor.updateRow(row)

    edit.stopEditing(True)
    arcpy.SetProgressorPosition()
    return update

# Run initial Intersect
arcpy.SetProgressor("default","Running Intersect Tool...")
arcpy.Intersect_analysis(Features,default_gdb+"\\"+str(apptxt(ParceType))+"Parcel_Int_FHA","ALL")
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int1 = (default_gdb+"\\"+str(apptxt(ParceType))+"Parcel_Int_FHA")

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int1,default_gdb+"\\"+str(apptxt(ParceType))+"Parcel_Flood_Exposure",FDissolve_Fields)
arcpy.SetProgressorPosition()


### New Tool Argument - SFHA intersect feature class ####
int2 = (default_gdb+"\\"+str(apptxt(ParceType))+"Parcel_Flood_Exposure")

# calculate acreage of intersected features
calcatt(int2,"Acres","ACRES_US"),calcatt(int2,"Sq_Mi","SQUARE_MILES_US")

# build ranked fld zone attributes
rank(int2,default_gdb)

arcpy.conversion.FeatureClassToFeatureClass(
    in_features=int2, 
    out_path=Output_GDB, 
    out_name=str(apptxt(ParceType))+"Parcel_Flood_Exposure"
    )

# execute results table process
csv1 = paths(Output_TBFLD,str(apptxt(ParceType))+'Parcel_Flood_Zone.csv')
field_names = [field.name for field in arcpy.ListFields(int2)]
df_exp_parcel(int2,field_names,PIN,csv1)

# add parcel count to each row
parcelcount(int2,1)

# Execute Dissolve - generate final parcel counts per SFHA
Dis_fields = [Ranking,'FLD_ZONE','Subtype']
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(int2,Output_GDB+"\\"+str(apptxt(ParceType))+"Parcel_Flood_Exposure_area_calc",Dis_fields,[["Parcel_Count","SUM"],["Acres","SUM"],["Sq_Mi","SUM"]])
arcpy.SetProgressorPosition()


### New Tool Argument - Exposure by Land Use Dissolve Output Feature Class ####
int3 = (Output_GDB+"\\"+str(apptxt(ParceType))+"Parcel_Flood_Exposure_area_calc")

arcpy.management.CalculateField(int3,"Percent_Area","!SUM_Acres! / " + str(sum_field_values(int3,"SUM_Acres")) + " *100","PYTHON3","","", "ENFORCE_DOMAINS")


### New Tool Argument - New schema lock on modified feature ####
int4 = (Output_GDB+"\\"+str(apptxt(ParceType))+"Parcel_Flood_Exposure_area_calc")

#Export Attribute Table
arcpy.SetProgressor("default","Exporting Exposure by {0} Land Use Attribute Table...".format(ParceType))
arcpy.conversion.TableToTable(int4,Output_TBFLD,str(apptxt(ParceType))+"Parcel_Flood_Exposure_area_calc.csv")
arcpy.SetProgressorPosition()
