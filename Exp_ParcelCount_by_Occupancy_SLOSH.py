# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
PIN = arcpy.GetParameterAsText(1)
SLOSH1 = arcpy.GetParameterAsText(2)
SLOSH2 = arcpy.GetParameterAsText(3)
SLOSH3 = arcpy.GetParameterAsText(4)
SLOSH4 = arcpy.GetParameterAsText(5)
SLOSH5 = arcpy.GetParameterAsText(6)
Output_GDB = arcpy.GetParameterAsText(7)
output_folder = arcpy.GetParameterAsText(8)

# Script Argument
default_gdb = arcpy.env.scratchGDB
FDissolve = [PIN,'Type_Oc']

# build path
def paths(x,y):
    path = os.path.join(x,y)
    return path

# Add Parcel count field and auto fill value of 1 for each row
def parcelcount(w,x):
    arcpy.SetProgressor("default","Adding Parcel Count Values...")
    arcpy.SetProgressorPosition()
    arcpy.management.AddField(w,"Parcel_Count","DOUBLE")
    parcel_count = arcpy.management.CalculateField(w,"Parcel_Count",x,"PYTHON3","","", "ENFORCE_DOMAINS")
    return parcel_count

def FL_fc(in_fc,query,fc_gdb,fc_name):
    arcpy.SetProgressor('default','Querying Parcel Data...')

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
    stats = []

    for field in arcpy.ListFields(inFC):
        if field.name in ("Parcel_Count","SUM_BldgCost","SUM_ContentCos","TotalBldgValue"):
            stats.append([field.name,"Sum"])

    arcpy.analysis.Statistics(inFC,Output_GDB+'//'+desc_name+"_Exp_Parcel_By_Occupancy_tbl",stats,"Type_oc")

    calc_tbl1 = (Output_GDB+"//"+desc_name+"_Exp_Parcel_By_Occupancy_tbl")

    # Export Final Calculated Attribute Table
    arcpy.SetProgressor("default","Exporting SLOSH Parcel by Occupancy Results table...")
    exp_tbl = arcpy.conversion.ExportTable(calc_tbl1,output_folder+"//"+desc_name+"_Exp_Parcel_By_Occupancy.csv","","NOT_USE_ALIAS")
    arcpy.SetProgressorPosition()

    return exp_tbl

### -------------------------------------------------------------------------------- ###
                                    #SQL Queries
### -------------------------------------------------------------------------------- ###

QSLOSH1_string = f"MAX_{SLOSH1} IS NOT NULL"
QSLOSH1 = QSLOSH1_string
QSLOSH2_string = f"MAX_{SLOSH2} IS NOT NULL And MAX_{SLOSH1} IS NULL"
QSLOSH2 = QSLOSH2_string
QSLOSH3_string = f"MAX_{SLOSH3} IS NOT NULL And MAX_{SLOSH2} IS NULL And MAX_{SLOSH1} IS NULL"
QSLOSH3 = QSLOSH3_string
QSLOSH4_string = f"MAX_{SLOSH4} IS NOT NULL And MAX_{SLOSH3} IS NULL And MAX_{SLOSH2} IS NULL And MAX_{SLOSH1} IS NULL"
QSLOSH4 = QSLOSH4_string
QSLOSH5_string = f"MAX_{SLOSH5} IS NOT NULL And MAX_{SLOSH4} IS NULL And MAX_{SLOSH3} IS NULL And MAX_{SLOSH2} IS NULL And MAX_{SLOSH1} IS NULL"
QSLOSH5 = QSLOSH5_string

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(input_feature,paths(default_gdb,"SLOSH_Exp_Parcel_By_Occupancy"),FDissolve,[[SLOSH1,'MAX'],[SLOSH2,'MAX'],[SLOSH3,'MAX'],[SLOSH4,'MAX'],[SLOSH5,'MAX'],["BldgCost","SUM"],['ContentCos','SUM']])
arcpy.SetProgressorPosition()

dis1 = paths(default_gdb,"SLOSH_Exp_Parcel_By_Occupancy")

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(dis1,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(dis1,"TotalBldgValue","!SUM_BldgCost! + !SUM_ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

# Add Parcel count field and auto fill value of 1 for each row
parcelcount(dis1,1)

# Execute SLOSH Exposure Analysis for Minimum exposure of each parcel
SLOSH1_FC = FL_fc(dis1,QSLOSH1,default_gdb,'Min_SLOSH1_Query')
exposure(SLOSH1_FC)
SLOSH2_FC = FL_fc(dis1,QSLOSH2,default_gdb,'Min_SLOSH2_Query')
exposure(SLOSH2_FC)
SLOSH3_FC = FL_fc(dis1,QSLOSH3,default_gdb,'Min_SLOSH3_Query')
exposure(SLOSH3_FC)
SLOSH4_FC = FL_fc(dis1,QSLOSH4,default_gdb,'Min_SLOSH4_Query')
exposure(SLOSH4_FC)
SLOSH5_FC = FL_fc(dis1,QSLOSH5,default_gdb,'Min_SLOSH5_Query')
exposure(SLOSH5_FC)