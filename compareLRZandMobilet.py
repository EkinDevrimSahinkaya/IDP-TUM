import aiohttp
import asyncio
import csv
import pandas as pd
import time
import datetime
import glob
import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
new_string = ROOT_DIR.replace("\\", "/")
lrzRoot = new_string + "/IDP-TUM/LRZ/munich_loops_mapping_in_progress.csv"
outputDataRoot = new_string + "/IDP-TUM/output_data/*.csv"
comparedDataRoot = new_string + "/IDP-TUM/comparedData/*.csv"


def compareCsvFile():
    latest_outputdata_data_csv = max(glob.glob(outputDataRoot), key=os.path.getctime)

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


if __name__ == "__main__":
    import sys

    latest_outputdata_data_csv = max(glob.glob(outputDataRoot), key=os.path.getctime)

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
