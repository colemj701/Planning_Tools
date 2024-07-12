import os,sys, arcpy
import pandas as pd
import numpy as np
from arcpy.sa import* 

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

gdb = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\Florida\Critical_Asset\Boundary_Redo\County_no_city_Assets.gdb'
SFHA = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\FFRMS_Processing\Working_Data\Eff_data.gdb\S_FLD_HAZ_AR'
Depth_Grid = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Depth_Grid.gdb\FL_12097_17N_03m_WSEL_Con'
FVA_00 = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Depth_Grid.gdb\FL_12097_17N_03m_FVA00_Con'
FVA_01 = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Depth_Grid.gdb\FL_12097_17N_03m_FVA01_Con'
FVA_02 = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Depth_Grid.gdb\FL_12097_17N_03m_FVA02_Con'
FVA_03 = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Depth_Grid.gdb\FL_12097_17N_03m_FVA03_Con'
csv_point = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Critical_Assets_Boundary_Redo\County_Sensitivity_Analysis_Point.csv'
csv_ln_ply = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Critical_Assets_Boundary_Redo\County_Sensitivity_Analysis_Line_Poly.csv'
csv_asset = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Critical_Assets_Boundary_Redo\County_Sensitivity_Analysis_Asset_List.csv'


sfha = arcpy.GetParameterAsText(0)

datasets = []
fc_all = []
ds_paths = []
fc_dict = {}
fc_dictx = {}
surface = [Depth_Grid,FVA_00,FVA_01,FVA_02,FVA_03]
zones = {'1pct':Depth_Grid,'FVA00':FVA_00,'FVA01':FVA_01,'FVA02':FVA_02,'FVA03':FVA_03}

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

env(gdb)

feature_datasets = arcpy.ListDatasets()
for dataset in feature_datasets:
    datasets.append(dataset)

for ds in datasets:
    ds_path = paths(gdb,ds)
    ds_paths.append(ds_path)
print(ds_paths)


for dsp in ds_paths:
    env(dsp)
    fc_list = arcpy.ListFeatureClasses()
    print(len(fc_list))
    parse_dsp = dsp.split('\\')
    dsp_name = parse_dsp[-1]
    dsp_final = dsp_name.replace("_"," ")

    arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        fc_path = paths(dsp,fc_name)
        spa = fc_desc.SpatialReference
        print(fc_path)
        geo_type = fc_desc.shapeType
        FID_Field = "FID_"+fc_name
        int_list = [SFHA,fc]
        geo_result_join = fc_path+"_int_join"
        geo_result_int = fc_path+"_int"
        geo_result = fc_path+'_final'
            
        arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

        def exp_geo_line_poly(x,y,z):

            arcpy.analysis.PairwiseIntersect(
                in_features=x,
                out_feature_class=y,
                join_attributes="ALL",
                output_type="INPUT")

            print('FLD Zone Intersect Completed')

            int_fl = arcpy.management.MakeFeatureLayer(y,'int_fl')

            fields = ['Z_Max_1pct','Z_Mean_1pct',
                      'Z_Max_FVA00','Z_Mean_FVA00',
                      'Z_Max_FVA01','Z_Mean_FVA01',
                      'Z_Max_FVA02','Z_Mean_FVA02',
                      'Z_Max_FVA03','Z_Mean_FVA03']
            

            
            arcpy.management.AddFields(
                in_table=int_fl,
                field_description=[[fields[0],'DOUBLE',fields[0]],
                                [fields[1],'DOUBLE',fields[1]],
                                [fields[2],'DOUBLE',fields[2]],
                                [fields[3],'DOUBLE',fields[3]],
                                [fields[4],'DOUBLE',fields[4]],
                                [fields[5],'DOUBLE',fields[5]],
                                [fields[6],'DOUBLE',fields[6]],
                                [fields[7],'DOUBLE',fields[7]],
                                [fields[8],'DOUBLE',fields[8]],
                                [fields[9],'DOUBLE',fields[9]]])
            
            # build table names and execute zonal stats
            for item in surface:
                for key, value in zones.items():
                    if value == item:
                        tbl = paths(gdb,fc_name+'_'+key+'_Zonal')

                        #Execute Zonal Stats for each surface
                        ZonalStatisticsAsTable(
                        in_zone_data=int_fl,
                        zone_field='OBJECTID',
                        in_value_raster=item,
                        out_table=tbl,
                        ignore_nodata='DATA',
                        statistics_type='ALL',
                        percentile_values=90)
            
                        print(f'zonal {key} calculated')

                        field_zonal_dict_max = {}
                        field_zonal_dict_mean = {}

                        with arcpy.da.SearchCursor(tbl,['OBJECTID_1','MAX','MEAN']) as cursor1:
                            for row1 in cursor1:
                                OID = row1[0]
                                zmax = row1[1]
                                zmean = row1[2]

                                field_zonal_dict_max[OID] = zmax
                                field_zonal_dict_mean[OID] = zmean

                        update_fields = [f'Z_Max_{key}',f'Z_Mean_{key}','OBJECTID']

                        print(f'{key} mean and max dictionaries built')

                        for key, value in field_zonal_dict_max.items():
                            with arcpy.da.UpdateCursor(int_fl,update_fields) as cursor2:
                                for row2 in cursor2:
                                    if row2[2] == key:
                                        row2[0] = value 
                                        cursor2.updateRow(row2)

                        for key, value in field_zonal_dict_mean.items():
                            with arcpy.da.UpdateCursor(int_fl,update_fields) as cursor3:
                                for row3 in cursor3:
                                    if row3[2] == key:
                                        row3[1] = value 
                                        cursor3.updateRow(row3)

                        print(field_zonal_dict_max)

            product = arcpy.management.Dissolve(
                        in_features=int_fl,
                        out_feature_class=z,
                        dissolve_field=['FID_'+fc_name,"Ranking"],
                        statistics_fields=[['Z_Max_1pct','MAX'],['Z_Mean_1pct','MEAN'],
                          ['Z_Max_FVA00','MAX'],['Z_Mean_FVA00','MEAN'],
                          ['Z_Max_FVA01','MAX'],['Z_Mean_FVA01','MEAN'],
                          ['Z_Max_FVA02','MAX'],['Z_Mean_FVA02','MEAN'],
                          ['Z_Max_FVA03','MAX'],['Z_Mean_FVA03','MEAN']])
            
            print('dissolve successful')    
            return product
        
        def exp_geo_point(u,v,w,x):
 
            fields = ['Z','Z_1pct','FVA00','FVA01','FVA02','FVA03']
            z_fields = ['Z_1pct','FVA00','FVA01','FVA02','FVA03']

             # Initialize an empty dictionary
            field_sur_dict = {}

            # Build the dictionary pairing the lists fields with zonal_z_Fields
            for i in range(len(z_fields)):
                field_sur_dict[z_fields[i]] = surface[i]

            arcpy.analysis.PairwiseIntersect(
                in_features=u,
                out_feature_class=v,
                join_attributes="ALL",
                output_type="INPUT")
            
            pt_fl = arcpy.management.MakeFeatureLayer(v,'pt_fl')

            arcpy.management.AddFields(
                in_table=v,
                field_description=[
                    [z_fields[0],'DOUBLE',z_fields[0]],
                    [z_fields[1],'DOUBLE',z_fields[1]],
                    [z_fields[2],'DOUBLE',z_fields[2]],
                    [z_fields[3],'DOUBLE',z_fields[3]],
                    [z_fields[4],'DOUBLE',z_fields[4]]])

            for item in z_fields:
                for key, value in field_sur_dict.items():
                    if key == item:
                        fields = [key,value]

                        AddSurfaceInformation(
                            in_feature_class=pt_fl,
                            in_surface=fields[1],
                            out_property="Z",
                            method="BILINEAR")

                        edit = arcpy.da.Editor(x)
                        edit.startEditing(False,True)
                        cursor_fields = ['Z',key]
                        with arcpy.da.UpdateCursor(pt_fl,cursor_fields) as cursor:
                            for row in cursor:
                                Z_value = row[0]
                                row[1] = Z_value
                                cursor.updateRow(row)
                        edit.stopEditing(True)
                    print(f'{fc_name} {key} values updated')

            product = arcpy.CopyFeatures_management(
                in_features=pt_fl,
                out_feature_class=w)

            return product
        
        if fc_name not in fc_dict:
            fc_dict[fc_name] = []
        fc_dict[fc_name].append(geo_type)
        print(fc_dict[fc_name])

        if "Point" in fc_dict[fc_name]:
            print(f'{fc_name} is a point layer :: adding surface information')
            arcpy.management.CalculateGeometryAttributes(
                in_features=fc,
                geometry_property=[['Lat','POINT_Y'],['Long','POINT_X']],
                coordinate_system=spa,
                coordinate_format='DD')
            with arcpy.EnvManager(workspace=dsp):
                exp_geo_point(int_list,geo_result_int,geo_result,gdb)
        else:
            with arcpy.EnvManager(workspace=dsp):
                exp_geo_line_poly(int_list,geo_result_int,geo_result)

# clean up process data
for dsp in ds_paths:
    env(dsp)
    fc_list = arcpy.ListFeatureClasses()

    arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        fc_path = paths(dsp,fc_name)
        name_end = fc_name.split('_')[-1]

        if name_end == 'int' or name_end == 'join':
            arcpy.Delete_management(fc)
            print(f'{fc_name} is process feature :: fc deleted')
        else:
            print(f'{fc_name} is either final or original fc :: fc retained')

# clean up process zonal tables
env(gdb)
tbl_list = arcpy.ListTables()
for tbl in tbl_list:
    tbl_desc = arcpy.Describe(tbl)
    tbl_name = tbl_desc.name
    tbl_path = paths(gdb,tbl_name)
    arcpy.Delete_management(tbl_path)
    if arcpy.Exists(tbl_path):
        print(f'{tbl} not deleted')
    else:
        print(f'{tbl} successfully deleted')


# Export Summary tables

def df_exp_line_poly(w,x,y,z):

    out_field_list = [
        'MAX_Z_Max_1pct',
        'MEAN_Z_Mean_1pct',
        'MAX_Z_Max_FVA00',
        'MEAN_Z_Mean_FVA00',
        'MAX_Z_Max_FVA01',
        'MEAN_Z_Mean_FVA01',
        'MAX_Z_Max_FVA02',
        'MEAN_Z_Mean_FVA02',
        'MAX_Z_Max_FVA03',
        'MEAN_Z_Mean_FVA03']

    # Reading feature class data into a pandas DataFrame
    data = [row for row in arcpy.da.SearchCursor(w, x)]
    df = pd.DataFrame(data, columns=x)

    # Displaying the DataFrame
    print(df.head())  # Displaying the first few rows of the DataFrame

    # Handling <Null> values (assuming they are represented as NaN)
    df[out_field_list[0]].fillna(np.nan, inplace=True)
    df[out_field_list[1]].fillna(np.nan, inplace=True)
    df[out_field_list[2]].fillna(np.nan, inplace=True)
    df[out_field_list[3]].fillna(np.nan, inplace=True)
    df[out_field_list[4]].fillna(np.nan, inplace=True)
    df[out_field_list[5]].fillna(np.nan, inplace=True)
    df[out_field_list[6]].fillna(np.nan, inplace=True)
    df[out_field_list[7]].fillna(np.nan, inplace=True)
    df[out_field_list[8]].fillna(np.nan, inplace=True)
    df[out_field_list[9]].fillna(np.nan, inplace=True)

    # Finding the row with the maximum ranking for each OID
    result = df.loc[df.groupby(y)['Ranking'].idxmax()]

    # Creating a new DataFrame with the results
    new_df = result[
        [y,
         'Ranking',
        out_field_list[0],
        out_field_list[1],
        out_field_list[2],
        out_field_list[3],
        out_field_list[4],
        out_field_list[5],
        out_field_list[6],
        out_field_list[7],
        out_field_list[8],
        out_field_list[9]]].reset_index(drop=True)

    # Displaying the new DataFrame
    num_rows=len(new_df)
    print(num_rows)
    new_df.head() 

    # Calculate frequency of each unique Ranking in the entire DataFrame 'new_df'
    frequency = new_df['Ranking'].value_counts()

    # Check the frequency counts and head of the DataFrame for diagnostics
    print("Frequency counts:\n", frequency.head())

    # Calculate the maximum MAX_Z_Max and average MEAN_Z_Mean for each 'Ranking'
    aggregated_data = new_df.groupby('Ranking').agg({
        out_field_list[0]: 'max',
        out_field_list[1]: 'mean',
        out_field_list[2]: 'max',
        out_field_list[3]: 'mean',
        out_field_list[4]: 'max',
        out_field_list[5]: 'mean',
        out_field_list[6]: 'max',
        out_field_list[7]: 'mean',
        out_field_list[8]: 'max',
        out_field_list[9]: 'mean'
    }).reset_index()

    # Check the aggregated data for diagnostics
    print("Aggregated data:\n", aggregated_data.head())

    # Create a DataFrame with specified columns ('Ranking', 'Frequency')
    new1_df = pd.DataFrame({
        'Ranking': frequency.index,
        'Frequency': frequency.values,
    })

    # Merge 'new_df' with 'aggregated_data' based on 'Ranking' to get 'Max_Z_Max' and 'MEAN_Z_Mean'
    new2_df = new1_df.merge(aggregated_data, on='Ranking')
    new2_df['Asset_Type'] = fc_name
    new2_df['Asset_Group'] =dsp_name

    # Displaying the new DataFrame 'new2_df'
    print(new2_df.head())

    # Mapping rankings to sensitivity levels using lambda function
    new2_df['Sensitivity'] = new2_df['Ranking'].apply(lambda x: 'Low' if x == 1 else ('Med' if x == 2 else 'High'))

    out_table = new2_df.to_csv(z, mode='a', header=False, index=False)
    print("CSV Successfully Appended")

    return out_table

def df_exp_point(w,x,y,z):

    z_fields = ['Z_1pct','FVA00','FVA01','FVA02','FVA03']

    # Reading feature class data into a pandas DataFrame
    data = [row for row in arcpy.da.SearchCursor(w, x)]
    df = pd.DataFrame(data, columns=x)

    # Displaying the DataFrame
    print(df.head())  # Displaying the first few rows of the DataFrame

    # Handling <Null> values (assuming they are represented as NaN)
    df['Z'].fillna(np.nan, inplace=True)

    # Finding the row with the maximum ranking for each OID
    result = df.loc[df.groupby(y)['Ranking'].idxmax()]

    # Creating a new DataFrame with the results
    new_df = result[[
        y,
        'Ranking',
        z_fields[0],
        z_fields[1],
        z_fields[2],
        z_fields[3],
        z_fields[4]]].reset_index(drop=True)

    # Displaying the new DataFrame
    num_rows=len(new_df)
    print(num_rows)
    new_df.head() 

    # Calculate frequency of each unique Ranking in the entire DataFrame 'new_df'
    frequency = new_df['Ranking'].value_counts()

    # Check the frequency counts and head of the DataFrame for diagnostics
    print("Frequency counts:\n", frequency.head())

    # Calculate the maximum MAX_Z_Max and average MEAN_Z_Mean for each 'Ranking'
    aggregated_data = new_df.groupby('Ranking').agg({
        z_fields[0]: 'max',
        z_fields[1]: 'max',
        z_fields[2]: 'max',
        z_fields[3]: 'max',
        z_fields[4]: 'max',
    }).reset_index()

    # Check the aggregated data for diagnostics
    print("Aggregated data:\n", aggregated_data.head())

    # Create a DataFrame with specified columns ('Ranking', 'Frequency')
    new1_df = pd.DataFrame({
        'Ranking': frequency.index,
        'Frequency': frequency.values,
    })

    # Merge 'new_df' with 'aggregated_data' based on 'Ranking' to get 'Max_Z_Max'
    new2_df = new1_df.merge(aggregated_data, on='Ranking')
    new2_df['Asset_Type'] = fc_name
    new2_df['Asset_Group'] =dsp_name

    # Displaying the new DataFrame 'new2_df'
    print(new2_df.head())

    # Mapping rankings to sensitivity levels using lambda function
    new2_df['Sensitivity'] = new2_df['Ranking'].apply(lambda x: 'Low' if x == 1 else ('Med' if x == 2 else 'High'))

    out_table = new2_df.to_csv(z, mode='a', header=False, index=False)
    print("CSV Successfully Appended")

    return out_table

def df_exp_asset(w,x,z):

    fields = ['Ranking','Asset','Name','Lat','Long','Z_1pct','FVA00','FVA01','FVA02','FVA03']

    # Reading feature class data into a pandas DataFrame
    data = [row for row in arcpy.da.SearchCursor(w, x)]
    df = pd.DataFrame(data, columns=x)

    # Find the column name that matches 'Name' in a case-insensitive way
    reference_column = next((col for col in df.columns if col.lower() == 'name'), None)

    if reference_column is not None:
        # Rename the found column to 'Name'
        df.rename(columns={reference_column: 'Name'}, inplace=True)

    print(df.head())

    filtered_df = df[fields].copy()
    filtered_df.loc[:,'Asset_Type'] = fc_name
    filtered_df.loc[:,'Asset_Group'] = dsp_name

    filtered_df['Sensitivity'] = filtered_df['Ranking'].apply(lambda x: 'Low' if x == 1 else ('Med' if x == 2 else 'High'))
    print(filtered_df.head())

    out_table = filtered_df.to_csv(z, mode='a', header=False, index=False)
    print("CSV Successfully Appended")

    return out_table

for dsp in ds_paths:
    env(dsp)
    fc_list = arcpy.ListFeatureClasses()
    print('Total feature count in feature dataset {0} :: {1}'.format(dsp.split("\\")[-1],len(fc_list)))
    parse_dsp = dsp.split('\\')
    dsp_name = parse_dsp[-1]
    dsp_final = dsp_name.replace("_"," ")

    arcpy.SetProgressor("Step","Exporting Tables for Dataset: {0}...".format(dsp_final),0,len(fc_list))
    for fc in fc_list:
        fc_desc = arcpy.Describe(fc)
        fc_name = fc_desc.name
        print(fc_name)
        geo_type = fc_desc.shapeType

        if fc_name.split('_')[-1] == 'final':
            if geo_type == "Point":
                print('is point feature')
                og_name = fc_name.replace('_final','')
                FID_Field = 'FID_'+og_name
                field_names = [field.name for field in arcpy.ListFields(fc)]
                df_exp_point(fc,field_names,FID_Field,csv_point)
                df_exp_asset(fc,field_names,csv_asset)
            else:
                print('is either polyline or polygon feature')
                og_name = fc_name.replace('_final','')
                FID_Field = 'FID_'+og_name
                Ranking = og_name+'_int_Ranking'
                field_names = [field.name for field in arcpy.ListFields(fc)]
                df_exp_line_poly(fc,field_names,FID_Field,csv_ln_ply)


