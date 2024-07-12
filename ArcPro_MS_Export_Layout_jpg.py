import arcpy,os

arcpy.SetProgressor("default","Initiating batch layout export tool...")

arcpy.env.overwriteOutput = True

folder_path = arcpy.GetParameterAsText(0)

Project = arcpy.GetParameterAsText(1)

Index_Field = arcpy.GetParameterAsText(2)

aprx = arcpy.mp.ArcGISProject(Project)

# list layouts in daily report project
lyts = aprx.listLayouts()
for lyt in lyts:
    lyt_name = lyt.name # retrieve layout name

    # Check if lyt has map series enabled and print each map series page as seperate jpeg
    if not lyt.mapSeries is None:
        ms = lyt.mapSeries # define ms as layout map series object
        if ms.enabled: #if enabled export map series
            count = ms.pageCount
            arcpy.SetProgressor('step','Exporting Map Series for Layout :: {0}...'.format(lyt_name),0,count,1)
            for pageNum in range(1, ms.pageCount + 1): # iterate over pages based on page numbers in map series (page number cannot be assigned by field value for this to work)
                ms.currentPageNumber = pageNum # retrieve page number
                page_name = str(getattr(ms.pageRow, Index_Field))  # retrieve page name based on map series field's attribute value assigned during series setup
                arcpy.SetProgressorLabel('Exporting Map Series Page "{0}" to JPEG...'.format(f"{page_name}"))
                lyt.exportToJPEG(os.path.join(folder_path, f"{page_name}"),96, "24-BIT_TRUE_COLOR", 100, True, False) # export page as jpeg with page number as file name
                arcpy.SetProgressorPosition()