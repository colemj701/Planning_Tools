# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

in_feat = arcpy.GetParameterAsText(0)
datasets = []
fc_all = []
ds_paths = []
fc_dict = {}
fc_dictx = {}

arcpy.SetProgressor("default","Adding Hazus Fields...")

def FL_VA_Res_Atts(input_feature):  # Hazus_Derived_Attribute_add

    field_list = ['Z', 'High_Tide_Flood',
                  'Precip_25yrSLR0', 'Precip_25yrSLR1', 'Precip_25yrSLR2', 'Precip_25yrSLR3', 
                  'CAT_1', 'CAT_2', 'CAT_3', 'CAT_4', 'CAT_5', 
                  'SLR1_Current', 'SLR2_Current', 'SLR3_Current',
                  'SLR_2030_Intermediate', 'SLR_2030_Intermediate-High', 
                  'SLR_2040_Intermediate', 'SLR_2040_Intermediate-High', 
                  'SLR_2070_Intermediate', 'SLR_2070_Intermediate-High']

    for field in field_list:
        # Add required and derived Hazus attribute fields.
        arcpy.management.AddField(
            in_table=input_feature, 
            field_name=field, 
            field_type='DOUBLE',
            field_alias=field,
            field_is_nullable='NULLABLE')
    return

FL_VA_Res_Atts(in_feat)

