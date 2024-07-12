import arcpy, os, sys, requests, logging, errno, datetime, time, argparse, pathlib
import pandas as pd
import numpy as np
from arcpy.sa import*

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

def env(x):
    arcpy.env.workspace = x
    return arcpy.env.workspace

def paths(x,y):
    path = os.path.join(x,y)
    return path

def datasets(gdb):
    datasets = []
    ds_paths = []
    env(gdb)

    feature_datasets = arcpy.ListDatasets()
    for dataset in feature_datasets:
        datasets.append(dataset)

    for ds in datasets:
        ds_path = paths(gdb,ds)
        ds_paths.append(ds_path)
    
    return ds_paths