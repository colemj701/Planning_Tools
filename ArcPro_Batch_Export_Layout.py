import arcpy,os

arcpy.SetProgressor("default","Initiating batch layout export tool...")

arcpy.env.overwriteOutput = True

folder_path = arcpy.GetParameterAsText(0)

Project = arcpy.GetParameterAsText(1)

aprx = arcpy.mp.ArcGISProject(Project)

lyts = aprx.listLayouts()
lyt_list = len(lyts)
arcpy.SetProgressor("step","Exporting project layouts",0,lyt_list,1)
for layout in lyts:
  arcpy.SetProgressorLabel('Exporting "{0}" to PDF...'.format(f"{layout.name}"))
  layout_name = layout.name.replace("\\"," ")
  layout.exportToPDF(os.path.join(folder_path, f"{layout_name}"), 300, "BEST", True, "ADAPTIVE", True, "LAYERS_ONLY", True, 80, False, False, True, False)
  arcpy.SetProgressorPosition()