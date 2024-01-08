import aiohttp
import asyncio
import csv
import pandas as pd
import geopandas as gpd
import time
import datetime
import glob
import os

from config import ROOT_DIR

rootPath = ROOT_DIR.replace("\\", "/")
lrzRoot = rootPath + "/LRZ/munich_loops_mapping_in_progress.csv"
outputDataRoot = rootPath + "/output_data/"
comparedDataRoot = rootPath + "/comparedData/"
mergedDataRoot = rootPath + "/mergedData/"
staticDataRoot = rootPath + "/static_data/"
xmlDataRoot = rootPath + "/xml_data/"

lrz_csv_file_path = rootPath + "/LRZ/munich_loops_mapping_in_progress.csv"
lrz_shp_file_path = rootPath + "/LRZ/munich_loops_mapping_in_progress.shp"

# read LRZ shapefile and convert to csv file
df = gpd.read_file(lrz_shp_file_path)
df['geometry'] = df['geometry'].astype(str).str.replace('POINT (', '')
df['geometry'] = df['geometry'].astype(str).str.replace(')', '')
df[['lon','lat']] = df['geometry'].str.split(' ',expand=True)
df.rename(columns={'DETEKTO':'detid'}, inplace=True)
df.to_csv(lrz_csv_file_path, sep=',', encoding='utf-8')


def compare_csv_files():
    latest_outputdata_data_csv = max(glob.glob(outputDataRoot+"*.csv"), key=os.path.getctime)

    a = pd.read_csv(lrzRoot)
    b = pd.read_csv(latest_outputdata_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat_x'] == 0) | (output['lon_x'] == 0)
    output = output[~zero_coords_filter]
    output.to_csv(comparedDataRoot+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")

    latest_compared_data_csv = max(glob.glob(comparedDataRoot+"*.csv"), key=os.path.getctime)
    df = pd.read_csv(latest_compared_data_csv)
    df = df.rename(columns=({'lon_x': 'lon'}))
    df = df.rename(columns=({'lat_x': 'lat'}))
    del df['lon_y']
    del df['lat_y']
    del df['geometry']
    df.to_csv(mergedDataRoot+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_merged.csv", sep=',', encoding='utf-8')

def output_data():
    """
    Merge static location data and traffic properties. Remove entries from the latest detector data containing
    empty entries (i.e. 0) in the lat/lon fields.
    """

    latest_xml_data_csv = max(glob.glob(xmlDataRoot + "*.csv"), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticDataRoot + "*static.csv"), key=os.path.getctime)

    # merge_detector_locations(latest_static_data_csv)

    a = pd.read_csv(latest_xml_data_csv)
    b = pd.read_csv(latest_static_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat'] == 0) | (output['lon'] == 0)
    zero_coords_filter2 = (output['lat'] == 0.0) | (output['lon'] == 0.0)
    output = output[~zero_coords_filter]
    output = output[~zero_coords_filter2]

    output.to_csv(
        os.path.join(
            ROOT_DIR, "output_data",
            datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_") + "_output.csv"
        )
    )

    print("end of compare")


if __name__ == "__main__":
    import sys

    print(sys.path)
    # compare_csv("2023_11_15_12_32_42_15min.csv", "2023_11_15_14_51_03_15min_static.csv")
    latest_xml_data_csv = max(glob.glob(xmlDataRoot + "*.csv"), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticDataRoot + "*.csv"), key=os.path.getctime)

    a = pd.read_csv(latest_xml_data_csv)
    b = pd.read_csv(latest_static_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat'] == 0) | (output['lon'] == 0)
    zero_coords_filter2 = (output['lat'] == 0.0) | (output['lon'] == 0.0)
    output = output[~zero_coords_filter]
    output = output[~zero_coords_filter2]
    output.to_csv("output_data/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")