# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)
PIN = arcpy.GetParameterAsText(1)
SLR1 = arcpy.GetParameterAsText(2)
SLR2 = arcpy.GetParameterAsText(3)
SLR3 = arcpy.GetParameterAsText(4)
Output_GDB = arcpy.GetParameterAsText(5)
output_folder = arcpy.GetParameterAsText(6)

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
    arcpy.SetProgressor("default","Exporting SLR Parcel by Occupancy Results table...")
    exp_tbl = arcpy.conversion.ExportTable(calc_tbl1,output_folder+"//"+desc_name+"_Exp_Parcel_By_Occupancy.csv","","NOT_USE_ALIAS")
    arcpy.SetProgressorPosition()

    return exp_tbl

### -------------------------------------------------------------------------------- ###
                                    #SQL Queries
### -------------------------------------------------------------------------------- ###

QSLR1_string = f"MAX_{SLR1} IS NOT NULL"
QSLR1 = QSLR1_string
QSLR2_string = f"MAX_{SLR2} IS NOT NULL"
QSLR2 = QSLR2_string
QSLR3_string = f"MAX_{SLR3} IS NOT NULL"
QSLR3 = QSLR3_string

# Execute Dissolve - Dissolve by Parcel Number and SFHA
arcpy.SetProgressor("default","Running Dissolve Tool...")
arcpy.management.Dissolve(input_feature,paths(default_gdb,"SLR_Exp_Parcel_By_Occupancy"),FDissolve,[[SLR1,'MAX'],[SLR2,'MAX'],[SLR3,'MAX'],["BldgCost","SUM"],['ContentCos','SUM']])
arcpy.SetProgressorPosition()

dis1 = paths(default_gdb,"SLR_Exp_Parcel_By_Occupancy")

# Add Total Building Cost field and calculate from existing fields
arcpy.SetProgressor("default","Adding Building Total Values...")
arcpy.management.AddField(dis1,"TotalBldgValue","DOUBLE")
arcpy.management.CalculateField(dis1,"TotalBldgValue","!SUM_BldgCost! + !SUM_ContentCos!","PYTHON3","","", "ENFORCE_DOMAINS")
arcpy.SetProgressorPosition()

# Add Parcel count field and auto fill value of 1 for each row
parcelcount(dis1,1)

# Execute SLR Exposure Analysis for Minimum exposure of each parcel
SLR1_FC = FL_fc(dis1,QSLR1,default_gdb,'All_SLR1_Query')
exposure(SLR1_FC)
SLR2_FC = FL_fc(dis1,QSLR2,default_gdb,'All_SLR2_Query')
exposure(SLR2_FC)
SLR3_FC = FL_fc(dis1,QSLR3,default_gdb,'All_SLR3_Query')
exposure(SLR3_FC)