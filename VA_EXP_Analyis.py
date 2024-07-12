import os,sys, arcpy
import pandas as pd
import numpy as np
from arcpy.sa import* 

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

gdb = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\Florida\Critical_Asset\Filtered_Regional_Assets.gdb'
SFHA = r'C:\Project_Files\GIS\Library\Dev_Apps\HMP_Tools\HMP_Tools\Temp_Processing.gdb\County_S_FLD_HAZ_AR'
Depth_Grid = r'C:\Project_Files\GIS\HMP+\St_Cloud+\4.0 Reference Data\USGS\Lidar\Data_Download\Derived_DEM\Depth_Con.tif'
csv_point = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Filtered_Critical_Asset_Data\Exposure\St_Cloud_Regional_Asset_Exp_Analysis_point.csv'
csv_ln_pt = r'C:\Project_Files\GIS\HMP+\St_Cloud+\2.0 Tables\1.0 Working\Filtered_Critical_Asset_Data\Exposure\St_Cloud_Regional_Asset_Exp_Analysis_line_poly.csv'

sfha = arcpy.GetParameterAsText(0)

datasets = []
fc_all = []
ds_paths = []
fc_dict = {}

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
        print(fc_path)
        geo_type = fc_desc.shapeType
        FID_Field = "FID_"+fc_name
        int_list = [SFHA,fc_path]
        z_fields = ["Z_Max","Z_Mean"]
        geo_result = fc_path+"_int_dis"
        geo_result_int = fc_path+"_int"
        geo_result_pt = fc_path+"_results"
            
        arcpy.SetProgressorLabel("Exporting {0} data...".format(fc_name.replace("_"," ")))

        def exp_geo_line_poly(x,y,z):
            arcpy.analysis.PairwiseIntersect(
                in_features=x,
                out_feature_class=geo_result_int,
                join_attributes="ALL",
                output_type="INPUT")

            AddSurfaceInformation(
                in_feature_class=geo_result_int,
                in_surface=Depth_Grid,
                out_property=z_fields,
                method="BILINEAR")

            product = arcpy.management.Dissolve(
                        in_features=geo_result_int,
                        out_feature_class=geo_result,
                        dissolve_field=[z,"Ranking"],
                        statistics_fields=[["Z_Max","MAX"],["Z_Mean","MEAN"]])
    
            return product
        
        def exp_geo_point(x):
            arcpy.analysis.PairwiseIntersect(
                in_features=x,
                out_feature_class=geo_result_pt,
                join_attributes="ALL",
                output_type="INPUT")

            product = AddSurfaceInformation(
                in_feature_class=geo_result_pt,
                in_surface=Depth_Grid,
                out_property="Z",
                method="BILINEAR")
    
            return product

        # List to hold field names

        def df_exp_line_poly(w,x,y,z):

            # Reading feature class data into a pandas DataFrame
            data = [row for row in arcpy.da.SearchCursor(w, x)]
            df = pd.DataFrame(data, columns=x)

            # Displaying the DataFrame
            print(df.head())  # Displaying the first few rows of the DataFrame

            # Handling <Null> values (assuming they are represented as NaN)
            df['MAX_Z_Max'].fillna(np.nan, inplace=True)
            df['MEAN_Z_Mean'].fillna(np.nan, inplace=True)

            # Finding the row with the maximum ranking for each OID
            result = df.loc[df.groupby(y)['Ranking'].idxmax()]

            # Creating a new DataFrame with the results
            new_df = result[[y, 'Ranking', 'MAX_Z_Max','MEAN_Z_Mean']].reset_index(drop=True)

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
                'MAX_Z_Max': 'max',
                'MEAN_Z_Mean': 'mean'
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

            out_table = new2_df.to_csv(z, mode='a', header=False, index=False)
            print("CSV Successfully Appended")

            return out_table

        def df_exp_point(w,x,y,z):

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
            new_df = result[[y, 'Ranking','Z']].reset_index(drop=True)

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
                'Z': 'max',
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

            out_table = new2_df.to_csv(z, mode='a', header=False, index=False)
            print("CSV Successfully Appended")

            return out_table
        
        if fc_name not in fc_dict:
            fc_dict[fc_name] = []
        fc_dict[fc_name].append(geo_type)
        print(fc_dict[fc_name])

        if "Point" in fc_dict[fc_name]:
            exp_geo_point(int_list)
            field_names = [field.name for field in arcpy.ListFields(geo_result_pt)]
            df_exp_point(geo_result_pt,field_names,FID_Field,csv_point)
        elif "Polyline" in fc_dict[fc_name]:
            exp_geo_line_poly(int_list,fc_path,FID_Field)
            field_names = [field.name for field in arcpy.ListFields(geo_result)]
            df_exp_line_poly(geo_result,field_names,FID_Field,csv_ln_pt)
        elif "Polygon" in fc_dict[fc_name]:
            exp_geo_line_poly(int_list,fc_path,FID_Field)
            field_names = [field.name for field in arcpy.ListFields(geo_result)]
            df_exp_line_poly(geo_result,field_names,FID_Field,csv_ln_pt)


