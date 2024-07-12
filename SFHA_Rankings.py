import arcpy, os, sys
arcpy.env.overwriteOutput = True

sfha = arcpy.GetParameterAsText(0)

arcpy.management.AddField(
    in_table=sfha,field_name="Ranking",
    field_type="DOUBLE",
    field_precision=20,
    field_scale=0,
    field_length=2,
    field_alias="Ranking",
    field_is_nullable="NULLABLE")

arcpy.SetProgressor("default","Calculating SFHA Ranking...")

field_list = ["FLD_ZONE","ZONE_SUBTY","Ranking"]

with arcpy.da.UpdateCursor(sfha,field_list) as cursor:
    for row in cursor:
        if row[0] == "AE":
            row[2] = 13
            cursor.updateRow(row)
        elif row[0] == "A":
            row[2] = 12
            cursor.updateRow(row)
        elif row[0] == "AH":
            row[2] = 11
            cursor.updateRow(row)
        elif row[0] == "AO":
            row[2] = 10
            cursor.updateRow(row)
        elif row[0] == "AR":
            row[2] = 9
            cursor.updateRow(row)
        elif row[0] == "A99":
            row[2] = 8
            cursor.updateRow(row)
        elif row[0] == "VE":
            row[2] = 7
            cursor.updateRow(row)
        elif row[0] == "V":
            row[2] = 6
            cursor.updateRow(row)
        elif row[0] == "X" and row[1] == "0.2 PCT ANNUAL CHANCE FLOOD HAZARD":
            row[2] = 5
            cursor.updateRow(row)
        elif row[0] == "OPEN WATER":
            row[2] = 4
            cursor.updateRow(row)
        elif row[0] == "X":
            row[2] = 3
            cursor.updateRow(row)
        elif row[0] == "D":
            row[2] = 2
            cursor.updateRow(row)
        elif row[0] == "AREA NOT INCLUDED":
            row[2] = 1
            cursor.updateRow(row)
        elif row[0] == "NP – NOT POPULATED":
            row[2] = 0
            cursor.updateRow(row)