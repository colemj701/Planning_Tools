# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
SLR1 = arcpy.GetParameterAsText(1)
SLR2 = arcpy.GetParameterAsText(2)
SLR3 = arcpy.GetParameterAsText(3)
Output_GDB = arcpy.GetParameterAsText(4)
output_folder = arcpy.GetParameterAsText(5)

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
    arcpy.SetProgressor("default","Exporting SLR Building by Occupancy Results table...")
    exp_tbl = arcpy.conversion.ExportTable(dis1,output_folder+"\\"+dis_name+".csv","","NOT_USE_ALIAS")
    arcpy.SetProgressorPosition()

    return exp_tbl

### -------------------------------------------------------------------------------- ###
                                    #SQL Queries
### -------------------------------------------------------------------------------- ###

QSLR1_string = f"{SLR1} IS NOT NULL"
QSLR1 = QSLR1_string
QSLR2_string = f"{SLR2} IS NOT NULL And {SLR1} IS NULL"
QSLR2 = QSLR2_string
QSLR3_string = f"{SLR3} IS NOT NULL And {SLR2} IS NULL And {SLR1} IS NULL"
QSLR3 = QSLR3_string

# Add Parcel count field and auto fill value of 1 for each row
BuildingCount(input_feature,1)

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(input_feature,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(input_feature,"TotalBldgValue","!BldgCost! + !ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

# Execute SLR Exposure Analysis for Minimum exposure of each parcel
SLR1_FC = FL_fc(input_feature,QSLR1,default_gdb,'Min_SLR1_Query')
exposure(SLR1_FC)
SLR2_FC = FL_fc(input_feature,QSLR2,default_gdb,'Min_SLR2_Query')
exposure(SLR2_FC)
SLR3_FC = FL_fc(input_feature,QSLR3,default_gdb,'Min_SLR3_Query')
exposure(SLR3_FC)