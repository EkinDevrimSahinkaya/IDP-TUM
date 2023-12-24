import aiohttp
import asyncio
import csv
import pandas as pd
import geopandas as gpd
import time
import datetime
import glob
import os

from osgeo import gdal


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
staticDataPath = os.path.join(ROOT_DIR, "static_data", "*static.csv")
xmlDataPath = os.path.join(ROOT_DIR, "xml_data", "*.csv")


def merge_detector_locations(csv_pulledlocs: str):
    """
    Compare newly pulled and hand-labelled detector locations and fill the missing
    coordinates of the pulled locations with the hand-labelled ones

    :param csv_pulledlocs: Path to the newly pulled detector locations
    """
    # TODO: necessary?
    # gdal.SetConfigOption('SHAPE_RESTORE_SHX', 'YES')

    csv_handlabels_path = os.path.join(ROOT_DIR, "static_data", "labelled_detector_locations.csv")

    # read shapefile and transform to csv if csv file doesn't exist
    loc_crs = 4326
    if not os.path.exists(csv_handlabels_path):
        shp_path = os.path.join(ROOT_DIR, "static_data", "munich_loops_mapping_in_progress.shp")
        detectors = gpd.read_file(shp_path)
        detectors = detectors.to_crs(loc_crs)
        detectors.to_csv(csv_handlabels_path)

    # read csv file
    df_handlocs = pd.read_csv(csv_handlabels_path)
    df_pulledlocs = pd.read_csv(csv_pulledlocs)

    # create a list containing just detids from large detector csv file
    handloc_detids = df_handlocs['DETEKTO']

    # create mask
    mask = df_pulledlocs['detid'].isin(handloc_detids)

    # iterate over masked pulledlocs, update lat/lon if values are missing
    for i, row in df_pulledlocs[mask].iterrows():
        if pd.isna(row['lat']):
            # TODO: use df.set_index() to re-index the data frame using 'detid'?
            # get lon/lat values from hand-labelled detector locations
            detid = row['detid']
            geom = df_handlocs[['DETEKTO','geometry']]
            data = geom[geom['DETEKTO'] == detid]
            # TODO: looks ugly, can we do this more pretty?
            idx = data.index.values[0]
            #TODO: does 'geometry always look like 'POINT (xx yy)'?
            lon, lat = df_handlocs['geometry'][idx][7:-1].split(' ')

            # update missing lon/lat values
            df_pulledlocs.loc[i, 'lon'] = lon
            df_pulledlocs.loc[i, 'lat'] = lat

    df_pulledlocs.to_csv(csv_pulledlocs, index=False)


def output_data():
    """
    Merge static location data and traffic properties. Remove entries from the latest detector data containing
    empty entries (i.e. 0) in the lat/lon fields.
    """

    latest_xml_data_csv = max(glob.glob(xmlDataPath), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticDataPath), key=os.path.getctime)

    merge_detector_locations(latest_static_data_csv)

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
    latest_xml_data_csv = max(glob.glob(xmlDataPath), key=os.path.getctime)
    latest_static_data_csv = max(glob.glob(staticDataPath), key=os.path.getctime)

    a = pd.read_csv(latest_xml_data_csv)
    b = pd.read_csv(latest_static_data_csv)

    output = a.merge(b, on="detid", how="left").fillna(0).set_index("detid")
    zero_coords_filter = (output['lat'] == 0) | (output['lon'] == 0)
    zero_coords_filter2 = (output['lat'] == 0.0) | (output['lon'] == 0.0)
    output = output[~zero_coords_filter]
    output = output[~zero_coords_filter2]
    output.to_csv("output_data/"+datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").replace("-", "_")+"_output.csv")