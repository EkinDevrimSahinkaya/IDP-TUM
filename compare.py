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
staticRoot = new_string + "/IDP-TUM/static_data/*.csv"
xmlRoot = new_string + "/IDP-TUM/xml_data/*.csv"

def output_data():
    latest_xml_data_csv = max(glob.glob(xmlRoot), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticRoot), key=os.path.getctime)

    a = pd.read_csv(latest_xml_data_csv)
    b = pd.read_csv(latest_static_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat'] == 0) | (output['lon'] == 0)
    output = output[~zero_coords_filter]
    output.to_csv("output_data/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")


if __name__ == "__main__":
    import sys

    print(sys.path)
    # compare_csv("2023_11_15_12_32_42_15min.csv", "2023_11_15_14_51_03_15min_static.csv")
    latest_xml_data_csv = max(glob.glob(xmlRoot), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticRoot), key=os.path.getctime)

    a = pd.read_csv(latest_xml_data_csv)
    b = pd.read_csv(latest_static_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat'] == 0) | (output['lon'] == 0)
    output = output[~zero_coords_filter]
    output.to_csv("output_data/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")