# Import arcpy module
import arcpy, os, sys
arcpy.env.overwriteOutput = True

input_feature = arcpy.GetParameterAsText(0)

arcpy.SetProgressor("default","Adding Hazus Fields...")

def HazusDerivedAttributeadd():  # Hazus_Derived_Attribute_add

    # Add required and derived Hazus attribute fields.
    bcost = arcpy.management.AddField(input_feature,"BldgCost","DOUBLE",19,4)
    ccost = arcpy.management.AddField(input_feature,"ContentCos","DOUBLE",19,4)
    Type_Oc = FoundTy = arcpy.management.AddField(input_feature,"Type_Oc","TEXT","","",25)
    Occ = arcpy.management.AddField(input_feature,"Occupancy","TEXT","","",5)
    FoundTy = arcpy.management.AddField(input_feature,"FoundationType","TEXT","","",1)
    YrBlt = arcpy.management.AddField(input_feature,"YearBuilt","SHORT",5)
    NStr = arcpy.management.AddField(input_feature,"NumStories","SHORT",3)
    FFlrH = arcpy.management.AddField(input_feature,"FirstFloorHt","FLOAT",53)
    PctBldCost = arcpy.management.AddField(input_feature,"percent_building_cost","DOUBLE")
    DerBldCost = arcpy.management.AddField(input_feature,"derived_building_cost","DOUBLE")

    return ccost,Occ,FoundTy,YrBlt,NStr,FFlrH,PctBldCost,DerBldCost,Type_Oc

HazusDerivedAttributeadd()

