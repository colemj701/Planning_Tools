# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
SLOSH1 = arcpy.GetParameterAsText(1)
SLOSH2 = arcpy.GetParameterAsText(2)
SLOSH3 = arcpy.GetParameterAsText(3)
SLOSH4 = arcpy.GetParameterAsText(4)
SLOSH5 = arcpy.GetParameterAsText(5)
Output_GDB = arcpy.GetParameterAsText(6)
output_folder = arcpy.GetParameterAsText(7)

# Script Argument
default_gdb = arcpy.env.scratchGDB
FDissolve = 'Type_Oc'

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# Add Parcel count field and auto fill value of 1 for each row
def BuildingCount(w,x):
    arcpy.SetProgressor("default","Adding Building Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(w,"Building_Count","DOUBLE")
    building_count = arcpy.management.CalculateField(w,"Building_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return building_count

def FL_fc(in_fc,query,fc_gdb,fc_name):
    arcpy.SetProgressor('default','Querying building data...')

    FC_Out = paths(fc_gdb,fc_name)
    FL_temp = 'temp'
    try:
        arcpy.management.MakeFeatureLayer(
            in_features=in_fc, 
            out_layer=FL_temp)
        
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=FL_temp,
            selection_type='NEW_SELECTION',
            where_clause=query)
        
        arcpy.management.CopyFeatures (
            in_features=FL_temp,
            out_feature_class =FC_Out)
        
    except (Exception, OSError) as e:
        arcpy.AddWarning("An unexpected error occurred: {}".format(e))

    arcpy.SetProgressorPosition()
    return FC_Out

# execute exposure summary stats
def exposure(inFC):
    desc = arcpy.Describe(inFC)
    desc_name = desc.name
    dis_name = desc_name + '_Exp_Building_By_Occupancy'

    # Execute Dissolve - Dissolve by Parcel Number and SFHA
    arcpy.SetProgressor("default","Running Dissolve Tool...")
    arcpy.management.Dissolve(inFC,paths(default_gdb,dis_name),FDissolve,[['Building_Count','SUM'],["BldgCost","SUM"],['ContentCos','SUM'],['TotalBldgValue','SUM']])
    arcpy.SetProgressorPosition()

    dis1 = paths(default_gdb,dis_name)
    # Export Final Calculated Attribute Table
    arcpy.SetProgressor("default","Exporting SLOSH Building by Occupancy Results table...")
    exp_tbl = arcpy.conversion.ExportTable(dis1,output_folder+"\\"+dis_name+".csv","","NOT_USE_ALIAS")
    arcpy.SetProgressorPosition()

    return exp_tbl

### -------------------------------------------------------------------------------- ###
                                    #SQL Queries
### -------------------------------------------------------------------------------- ###

QSLOSH1_string = f"{SLOSH1} IS NOT NULL"
QSLOSH1 = QSLOSH1_string
QSLOSH2_string = f"{SLOSH2} IS NOT NULL"
QSLOSH2 = QSLOSH2_string
QSLOSH3_string = f"{SLOSH3} IS NOT NULL"
QSLOSH3 = QSLOSH3_string
QSLOSH4_string = f"{SLOSH4} IS NOT NULL"
QSLOSH4 = QSLOSH4_string
QSLOSH5_string = f"{SLOSH5} IS NOT NULL"
QSLOSH5 = QSLOSH5_string

# Add Parcel count field and auto fill value of 1 for each row
BuildingCount(input_feature,1)

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(input_feature,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(input_feature,"TotalBldgValue","!BldgCost! + !ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

# Execute SLOSH Exposure Analysis for Minimum exposure of each parcel
SLOSH1_FC = FL_fc(input_feature,QSLOSH1,default_gdb,'All_SLOSH1_Query')
exposure(SLOSH1_FC)
SLOSH2_FC = FL_fc(input_feature,QSLOSH2,default_gdb,'All_SLOSH2_Query')
exposure(SLOSH2_FC)
SLOSH3_FC = FL_fc(input_feature,QSLOSH3,default_gdb,'All_SLOSH3_Query')
exposure(SLOSH3_FC)
SLOSH4_FC = FL_fc(input_feature,QSLOSH4,default_gdb,'All_SLOSH4_Query')
exposure(SLOSH4_FC)
SLOSH5_FC = FL_fc(input_feature,QSLOSH5,default_gdb,'All_SLOSH5_Query')
exposure(SLOSH5_FC)