import pandas as pd
import datetime
import glob
import os
from config import ROOT_DIR

rootPath = ROOT_DIR.replace("\\", "/")
lrzRoot = rootPath + "/LRZ/munich_loops_mapping_in_progress.csv"
outputDataRoot = rootPath + "/output_data/"
comparedDataRoot = rootPath + "/comparedData/"
mergedDataRoot = rootPath + "/mergedData/"


def compareCsvFile():
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


if __name__ == "__main__":
    latest_outputdata_data_csv = max(glob.glob(outputDataRoot+"*.csv"), key=os.path.getctime)

    a = pd.read_csv(lrzRoot)
    b = pd.read_csv(latest_outputdata_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat_x'] == 0) | (output['lon_x'] == 0)
    output = output[~zero_coords_filter]
    output.to_csv("comparedData/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")

    latest_compared_data_csv = max(glob.glob(comparedDataRoot), key=os.path.getctime)
    df = pd.read_csv(latest_compared_data_csv)
    df = df.rename(columns=({'lon_x': 'lon'}))
    df = df.rename(columns=({'lat_x': 'lat'}))
    del df['lon_y']
    del df['lat_y']
    del df['geometry']
    df.to_csv("mergedData/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_merged.csv", sep=',', encoding='utf-8')
