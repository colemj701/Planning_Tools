import arcpy, os, sys
arcpy.env.overwriteOutput = True

dataset = arcpy.GetParameterAsText(0)

target_table = arcpy.GetParameterAsText(1)

arcpy.env.workspace = dataset

# Create a new empty table
output_table = arcpy.CreateTable_management(arcpy.env.workspace, "MergedTable")

# Get a list of all feature classes in the geodatabase
feature_classes = arcpy.ListFeatureClasses()

# Get a list of unique field names from all feature classes
field_names = ()



for feature_class in feature_classes:
    fields = arcpy.ListFields(feature_class)
    for field in fields:
        if not field.name in target_table:

        field_names.add(field.name)

# Add fields to the output table based on unique field names
for field_name in field_names:
    arcpy.AddField_management(output_table, field_name, "TEXT")

# Create an insert cursor for the output table
with arcpy.da.InsertCursor(output_table, list(field_names)) as insert_cursor:
    # Loop through each feature class and insert its rows into the output table
    for feature_class in feature_classes:
        fields = [field.name for field in arcpy.ListFields(feature_class)]
        with arcpy.da.SearchCursor(feature_class, fields) as search_cursor:
            for row in search_cursor:
                insert_cursor.insertRow(row)