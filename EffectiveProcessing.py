import arcpy, os, sys, requests, logging, errno, datetime
import pandas as pd
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

arcpy.env.overwriteOutput = True

arcpy.SetProgressor('default','Initiating Effective Data Processing Tool...')

Eff_Workspace = arcpy.GetParameterAsText(0)
Root = arcpy.GetParameterAsText(1)
coord = arcpy.GetParameterAsText(2)

######------------------------------------------------------------------------------------------------#####
                                                #Script Functions#
######------------------------------------------------------------------------------------------------#####

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

def csvPath(x):
    cDir = os.getcwd()
    xsNm = x
    exPath = paths(cDir,xsNm)
    return exPath

def get_file_name(file_path):
    return Path(file_path).name

def gdb(fld_path,gdb_name):
    env(fld_path)
    gdb_path = paths(fld_path,gdb_name+'.gdb')
    if arcpy.Exists(gdb_path):
        arcpy.Delete_management(gdb_path)
    gdb = arcpy.CreateFileGDB_management(out_folder_path=fld_path, 
                                         out_name=gdb_name)
    return gdb

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

def FL_Sel(in_fc,sel_fc,fc_gdb,fc_name):
    FC_Out = paths(fc_gdb,fc_name)
    FL_temp = 'temp'
    FL_temp_sel = 'temp_sel'

    try:
        arcpy.management.MakeFeatureLayer(
            in_features=in_fc, 
            out_layer=FL_temp)
        
        arcpy.management.MakeFeatureLayer(
            in_features=sel_fc, 
            out_layer=FL_temp_sel)
        
        arcpy.management.SelectLayerByLocation(
            in_layer=FL_temp,
            overlap_type='INTERSECT',
            select_features=FL_temp_sel,
            selection_type='NEW_SELECTION')
        
        arcpy.management.CopyFeatures(
            in_features=FL_temp,
            out_feature_class =FC_Out)
        
    except (Exception, OSError) as e:
        arcpy.AddWarning("An unexpected error occurred: {}".format(e))

    return FC_Out
    
def bld_FLDs(root_fld):
    folder_dict = {
        0:'Working_Data',
        1:'workspace.gdb',
        2:'SourceEffective'
    }

    for root, dirs, files in os.walk(root_fld):
        for directory in dirs:
            dir_path = paths(root,directory)
            base = os.path.join(directory)
            for key, value in folder_dict.items():
                if value == base:
                    folder_dict[key] = dir_path
    return folder_dict

def fc_path_eff(eff_db):
    Fc_dict = {
        0:'S_FLD_HAZ_AR',
        1:'S_XS',
        2:'S_BFE',
        3:'All_02pct_Zones'
    }

    for key,value in Fc_dict.items():
        fc_path = paths(eff_db,value)
        Fc_dict[key] = fc_path
    return Fc_dict

def fc_path_riv(riv_db):
    Fc_dict_riv = {
        0:'RIV_All_Zones',
        1:'Riv_1pct_Zones',
        2:'RIV_1pct_BFE_Zones',
        3:'RIV_1pct_XS_Zones',
        4:'RIV_02pct_Zones',
        5:'RIV_02pct_BFE_Zones',
        6:'RIV_02pct_XS_Zones',
        7:'RIV_S_Eff_0_2pct_Ar',

    }

    for key,value in Fc_dict_riv.items():
        fc_path = paths(riv_db,value)
        Fc_dict_riv[key] = fc_path
    return Fc_dict_riv

def fc_path_cst(cst_db):
    Fc_dict_cst = {
        0:'CST_All_Zones',
        1:'CST_1pct_Zones',
        2:'CST_1pct_BFE_Zones',
        3:'CST_02pct_Zones',
        4:'CST_02pct_BFE_Zones',
        5:'CST_S_Eff_0_2pct_Ar'
    }

    for key,value in Fc_dict_cst.items():
        fc_path = paths(cst_db,value)
        Fc_dict_cst[key] = fc_path
    return Fc_dict_cst

def bproj(x,y,z):
    env(x)
    arcpy.env.overwriteOutput = True
    shp_list = arcpy.ListFeatureClasses()
    shp_path_list = []
    arcpy.SetProgressor('default','Projecting Effective data...')
    try:
        for shp in shp_list:
            desc = arcpy.Describe(shp)
            shp_name = desc.name
            shp_path = paths(y,shp_name+'.shp')
            shp_path_list.append(shp_path)
        proj = arcpy.management.BatchProject(
            Input_Feature_Class_or_Dataset=shp_list,
            Output_Workspace=y,
            Output_Coordinate_System=z,
        )
    except (Exception, OSError) as e:
        arcpy.AddWarning("An unexpected error occurred: {}".format(e))

    arcpy.SetProgressorPosition()

    return proj

def eff_metric_df(gdb):
    feat_metric = []
    env(gdb)
    fc_list = arcpy.ListFeatureClasses()
    for fc in fc_list:
        desc = arcpy.Describe(fc)
        fc_name = desc.name
        if fc_name != 'XS' and fc_name != 'BFE' and  fc_name.split('_')[0] != 'AOI':
            result = arcpy.GetCount_management(fc)
            fc_count = int(result.getOutput(0))
            feat_metric.append({'Feature_Name': fc_name, 'Feature_Count': fc_count})
    return pd.DataFrame(feat_metric)

def total_count(S_FLD_HAZ_AR):
    feat_metric = []
    result = arcpy.GetCount_management(S_FLD_HAZ_AR)
    fc_count = int(result.getOutput(0))
    feat_metric.append({'Feature_Name': 'Total Features', 'Feature_Count': fc_count})
    return pd.DataFrame(feat_metric)

def eff_report(out_file,fcALL):
    riv_df = eff_metric_df(riv_gdb)
    cst_df = eff_metric_df(cst_gdb)
    tot = total_count(fcALL)
    combined_df = pd.concat([riv_df, cst_df, tot], ignore_index=True)
    report = combined_df.to_excel(out_file,index=False)
    return report

def clean_out(gdb):
    env(gdb)
    fc_list = arcpy.ListFeatureClasses()
    feature_classes_to_delete = []

    # Identify feature classes to be deleted
    for fc in fc_list:
        result = arcpy.GetCount_management(fc)
        fc_count = int(result.getOutput(0))
        if fc_count < 1:
            feature_classes_to_delete.append(fc)

    # Delete identified feature classes
    for fc_to_delete in feature_classes_to_delete:
        arcpy.Delete_management(fc_to_delete)

    # Check if any feature classes remain and delete the geodatabase if necessary
        env(gdb)
    fc_list_after_deletion = arcpy.ListFeatureClasses()
    if not fc_list_after_deletion:
        arcpy.Delete_management(gdb)

def copyFeat(inGDB,outGDB):
    env(inGDB)
    fc_list = arcpy.ListFeatureClasses()
    fc_count = len(fc_list)
    arcpy.SetProgressor('step','Exporting projected data to the SourceEffective folder...',0,fc_count,1)
    for fc in fc_list:
        try:
            desc = arcpy.Describe(fc)
            desc_name = desc.name
            arcpy.SetProgressorLabel(f'Exporting {desc_name} to the SourceEffective folder...')
            arcpy.management.CopyFeatures(
                in_features=fc, 
                out_feature_class=paths(outGDB,desc_name+'.shp')
                )
        except (Exception, OSError) as e:
            arcpy.AddWarning("An unexpected error occurred: {}".format(e))
        arcpy.SetProgressorPosition()

        # Generate S_Eff_0_2_pct_Ar
def merge02(inGDB,pct1,pct2,R_C):
    finFC = None
    if os.path.exists(inGDB):
        try:
            arcpy.SetProgressor('default',f'Processing {R_C}_S_Eff_0_2_pct_Ar feature class...')
            pct1_feat = paths(inGDB,pct1)
            pct2_feat = paths(inGDB,pct2)
            merge_list = [pct1_feat,pct2_feat]
            finFCx = paths(inGDB,R_C+'_S_Eff_0_2_pct_Ar_1')
            arcpy.management.Merge(
                inputs=merge_list, 
                output=paths(inGDB,R_C+'_S_Eff_0_2_pct_Ar_1')
                )
            fl_0_2 = arcpy.management.MakeFeatureLayer(
                in_features= finFCx, 
                out_layer='fl_0_2'
                )
            finFCxx = paths(inGDB,R_C+'_S_Eff_0_2_pct_Ar')
            finFC = arcpy.management.Dissolve(
                in_features=fl_0_2, 
                out_feature_class=finFCxx, 
                dissolve_field='DFIRM_ID'
                )
            env(inGDB)
            arcpy.Delete_management(finFCx)

        except (Exception, OSError) as e:
            arcpy.AddWarning("An unexpected error occurred: {}".format(e))

        arcpy.SetProgressorPosition()

    return finFC

def xs(inGDB,outGDB,infc1,infc2):
    arcpy.SetProgressor('default','Exoprting projected XS data to RIV.gdb...')
    s_xs = paths(inGDB,infc1)
    s_bfe = paths(inGDB,infc2)
    XS_list = [s_xs,s_bfe]
    for xs in XS_list:
        try:
            desc = arcpy.Describe(xs)
            desc_name = desc.name
            outFC = arcpy.management.CopyFeatures(
                in_features=xs, 
                out_feature_class=paths(outGDB,'RIV_'+desc_name)
                )
        except (Exception, OSError) as e:
            arcpy.AddWarning("An unexpected error occurred: {}".format(e))
    
    arcpy.SetProgressorPosition()

    return outFC

######------------------------------------------------------------------------------------------------#####
                                                #SQL Queries#
######------------------------------------------------------------------------------------------------#####

RIV_all = """
            ZONE_SUBTY <> 'COASTAL FLOODPLAIN' And
            ZONE_SUBTY <> 'RIVERINE FLOODPLAIN IN COASTAL AREA' And
            ZONE_SUBTY <> 'RIVERINE FLOODWAY IN COMBINED RIVERINE AND COASTAL ZONE' And
            ZONE_SUBTY <> '0.2 PCT ANNUAL CHANCE FLOOD HAZARD IN COASTAL ZONE' And
            FLD_ZONE <> 'VE' And
            FLD_ZONE <> 'OPEN WATER'
            """
_1pct = """
        FLD_ZONE <> 'X'
        """
CST = """
            ZONE_SUBTY = 'COASTAL FLOODPLAIN' Or
            ZONE_SUBTY = 'RIVERINE FLOODPLAIN IN COASTAL AREA' Or
            ZONE_SUBTY = 'RIVERINE FLOODWAY IN COMBINED RIVERINE AND COASTAL ZONE' Or
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD IN COASTAL ZONE' Or
            FLD_ZONE = 'OPEN WATER' Or
            FLD_ZONE = 'VE'
            """
BFE = """
            STATIC_BFE <> -9999
            """
XS_1pct = """
            FLD_ZONE = 'AE' And
            STATIC_BFE = -9999
            """
XS_02pct = """
            FLD_ZONE = 'X' And
            ZONE_SUBTY <> 'AREA OF MINIMAL FLOOD HAZARD' And
            STATIC_BFE = -9999
            """
Zone_02pct = """
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD' Or
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD CONTAINED IN CHANNEL' Or
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD CONTAINED IN STRUCTURE' Or
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD IN COASTAL ZONE' Or
            ZONE_SUBTY = '0.2 PCT ANNUAL CHANCE FLOOD HAZARD IN COMBINED RIVERINE AND COASTAL ZONE'
            """

AOI_Zone = """
            FLD_ZONE <> 'AE' And
            FLD_ZONE <> 'X' And
            STATIC_BFE = -9999
            """
######------------------------------------------------------------------------------------------------#####
                                                #Execute Tool#
######------------------------------------------------------------------------------------------------#####

arcpy.SetProgressor('default','Preparing Effective Data Environments...')

####------------------------------------------- Set up root environments

Folders = bld_FLDs(Root)
eff_gdb = paths(Folders[0],'Eff_data.gdb')
cst_gdb = paths(Folders[0],'CST_data.gdb')
riv_gdb = paths(Folders[0],'RIV_data.gdb')
gdb_list = [eff_gdb,riv_gdb,cst_gdb]

for db in gdb_list:
    if arcpy.Exists(db):
        arcpy.Delete_management(db)

env(Folders[0])
gdb(Folders[0],'Eff_data')
gdb(Folders[0],'CST_data')
gdb(Folders[0],'RIV_data')

FC_layers_eff = fc_path_eff(eff_gdb)
FC_layers_riv = fc_path_riv(riv_gdb)
FC_layers_cst = fc_path_cst(cst_gdb)

####------------------------------------------- Project Effective Data

bproj(Eff_Workspace,eff_gdb,coord)
arcpy.ResetProgressor()
copyFeat(eff_gdb,Folders[2])

####------------------------------------------- Extract Effective Data from S_FLD_HAZ_AR

arcpy.SetProgressor('default','Querying Effective Data...')

FL_fc(FC_layers_eff[0],CST,cst_gdb,'CST_All_Zones')
FL_fc(FC_layers_cst[0],_1pct,cst_gdb,'CST_1pct_Zones')
FL_fc(FC_layers_eff[0],RIV_all,riv_gdb,'RIV_All_Zones')
FL_fc(FC_layers_riv[0],_1pct,riv_gdb,'RIV_1pct_Zones')

FL_fc(FC_layers_riv[1],BFE,riv_gdb,'RIV_1pct_BFE_Zones')
FL_fc(FC_layers_riv[1],XS_1pct,riv_gdb,'RIV_1pct_XS_Zones')
FL_fc(FC_layers_cst[1],BFE,cst_gdb,'CST_1pct_BFE_Zones')

FL_fc(FC_layers_eff[0],Zone_02pct,eff_gdb,'All_02pct_Zones')

# Execute 0.2% spatial selection
FL_Sel(FC_layers_eff[3],FC_layers_riv[1],riv_gdb,'RIV_02pct_Zones')
FL_fc(FC_layers_riv[4],XS_02pct,riv_gdb,'RIV_02pct_XS_Zones')
FL_Sel(FC_layers_eff[3],FC_layers_cst[1],cst_gdb,'CST_02pct_Zones')

def split_zones(in_fc,out_gdb,db_name,where):
    gdb(Folders[0],db_name)
    temp_gdb = paths(Folders[0],db_name+'.gdb')

    arcpy.SplitByAttributes_analysis(in_fc, temp_gdb, 'FLD_ZONE')

    env(temp_gdb)
    rename = None
    fc_list = arcpy.ListFeatureClasses()

    for fc in fc_list:
        arcpy.SetProgressor('default','Renaming Effective data...')
        fc_name = arcpy.Describe(fc).name
        new_name = f'{db_name}_{fc_name}'
        old_path = paths(temp_gdb,fc_name)
        new_path = paths(temp_gdb,new_name)

        rename = arcpy.management.Rename(
            in_data=old_path,
            out_data=new_path
            )

    FC_out = None
    outAOIx = None
    fc_list1 = arcpy.ListFeatureClasses()

    for fc in fc_list1:
        try:
            arcpy.SetProgressor('default','Extracting Effective data...')
            fc_name = arcpy.Describe(fc).name
            FC_out = paths(out_gdb,fc_name)
            arcpy.management.CopyFeatures(
                in_features=fc,
                out_feature_class =FC_out)
            arcpy.SetProgressorPosition()
            arcpy.SetProgressor('default','Assessing potential deliverable AOI...')
            result = arcpy.GetCount_management(fc)
            fc_count = int(result.getOutput(0))
            if fc_count != 0:
                fl_AOI = arcpy.management.MakeFeatureLayer(
                    in_features=FC_out, 
                out_layer='fl_AOI')
                sel_AOI = arcpy.management.SelectLayerByAttribute(
                    in_layer_or_view=fl_AOI,
                    selection_type='NEW_SELECTION',
                    where_clause=where)

                outAOI = paths(out_gdb,'AOI_'+fc_name)
                outAOIx = arcpy.management.CopyFeatures(
                    in_features=sel_AOI,
                    out_feature_class =outAOI)
            arcpy.SetProgressorPosition()
            
        except (Exception, OSError) as e:
            arcpy.AddWarning("An unexpected error occurred: {}".format(e))                

    arcpy.Delete_management(temp_gdb)

    return rename, FC_out, outAOIx

arcpy.SetProgressor('default','Spliiting Effective data...')
split_zones(FC_layers_riv[0],riv_gdb,'RIV',AOI_Zone)
split_zones(FC_layers_cst[0],cst_gdb,'CST',AOI_Zone)

# export projected xs to riv.gdb
xs(eff_gdb,riv_gdb,FC_layers_eff[1],FC_layers_eff[2])

arcpy.SetProgressor('default','Generating Summary Report...')

out_csv = paths(Folders[0],'Effective_Data_Zone_Summary.xlsx')
eff_report(out_csv,FC_layers_eff[0])

arcpy.SetProgressor('default','Prepping deliverable data spatial layers')

# Generate S_Eff_0_2_pct_Ar
merge02(riv_gdb,FC_layers_riv[1],FC_layers_riv[4],'RIV')
merge02(cst_gdb,FC_layers_cst[1],FC_layers_cst[3],'CST')

arcpy.SetProgressor('default','Cleaning up Data...')

clean_out(riv_gdb)
clean_out(cst_gdb)

