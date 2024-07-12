import arcpy,os

arcpy.SetProgressor("default","Initiating batch layout export tool...")

arcpy.env.overwriteOutput = True

folder_path = arcpy.GetParameterAsText(0)

Project = arcpy.GetParameterAsText(1)

aprx = arcpy.mp.ArcGISProject(Project)

lyts = aprx.listLayouts()
lyt_list = len(lyts)
arcpy.SetProgressor("step","Exporting project layouts...",0,lyt_list,1)

for lyt in lyts:
  arcpy.SetProgressorLabel('Exporting "{0}" to JPEG...'.format(f"{lyt.name}"))
  lyt.exportToJPEG(os.path.join(folder_path, f"{lyt.name}"),96, "24-BIT_TRUE_COLOR", 100, True, False)
  arcpy.SetProgressorPosition()