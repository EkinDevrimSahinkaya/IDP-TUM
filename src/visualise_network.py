import os
import glob
import subprocess

import fiona  # this import needs to happen before osmnx
import osmnx as ox
import pandas as pd
import numpy as np

from networkx import MultiDiGraph, Graph
from geopandas import GeoDataFrame
from shapely.geometry import Point
from osmnx import settings, utils_graph, io
from config import ROOT_DIR

# Use this citation when referencing OSMnx in work
# Boeing, G. 2017. OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks.
# Computers, Environment and Urban Systems 65, 126-139.

path_map_munich = ROOT_DIR + "/data/network/map_munich.graphml"
mergedDataRoot = ROOT_DIR + "/data/merged_data/"
networkDataRoot = ROOT_DIR + "/data/network/"


def find_cygwin() -> str:
    """ Iterate over all drives (in reverse) to find the cygwin root folder

    :return: path to cygwin64
    """
    cygname = "cygwin64"
    driveStr = subprocess.check_output("fsutil fsinfo drives")
    driveStr = driveStr.strip().lstrip(b'Drives: ')
    drives = driveStr.split()
    # print(drives)
    # iterate in reverse, my cygwin is in D:
    for drive in drives[::-1]:
        drive = drive.decode(encoding='UTF-8')
        for root, dirs, files in os.walk(drive, topdown=True):
            for dir in dirs:
                if dir == cygname:
                    cygname = os.path.abspath(os.path.join(root, dir))
                    # print(cygname)
                    return cygname


def save_graph_shapefile_directional(graph, filepath=None, encoding="utf-8"):
    # default filepath if none was provided
    if filepath is None:
        filepath = os.path.join(ox.settings.data_folder, "shapefile")

    # if save folder does not already exist, create it (shapefiles get saved as set of files)
    if not filepath and not os.path.exists(filepath):
        os.makedirs(filepath)
    filepath_nodes = os.path.join(filepath, "nodes.shp")
    filepath_edges = os.path.join(filepath, "edges.shp")

    # convert undirected graph to gdfs and stringify non-numeric columns
    gdf_nodes, gdf_edges = ox.utils_graph.graph_to_gdfs(graph)
    gdf_nodes = ox.io._stringify_nonnumeric_cols(gdf_nodes)
    gdf_edges = ox.io._stringify_nonnumeric_cols(gdf_edges)
    # We need a unique ID for each edge
    gdf_edges["fid"] = np.arange(0, gdf_edges.shape[0], dtype='int')
    # save the nodes and edges as separate ESRI shapefiles
    gdf_nodes.to_file(filepath_nodes, encoding=encoding)
    gdf_edges.to_file(filepath_edges, encoding=encoding)


def get_base_graphml() -> MultiDiGraph:
    """
    Create a base map of munich, add detector static_data pulled with pull_static_mobilithek.py
    and plot the resulting graph
    https://github.com/cyang-kth/osm_mapmatching
    """
    # Create/load base map
    if not os.path.exists(path_map_munich):
        graph = ox.graph_from_place("Munich, Bavaria, Germany", network_type="drive", simplify=True)
        ox.save_graphml(graph, path_map_munich)
    else:
        graph = ox.load_graphml(path_map_munich)

    save_graph_shapefile_directional(graph, filepath=networkDataRoot)

    # #graph base map
    # _ = ox.plot_graph(graph,
    #                   node_size=0, node_color="black",
    #                   edge_linewidth=0.3, edge_color="white")

    return graph


def get_detectors() -> (GeoDataFrame, [Point]):
    """
    Get the latest merged detector locations and add a geometry column containing
    Points with lon, lat values

    :return: The resulting GeoDataFrame and a list of the created Points
    """
    # load detector static_data
    latest_merged_data_csv = max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime)
    detector_df = pd.read_csv(latest_merged_data_csv)

    # create GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(detector_df['lon'], detector_df['lat'])]
    crs = {'init': 'epsg:4326'}
    detector_gdf = GeoDataFrame(detector_df, crs=crs, geometry=geometry)

    # Add the point geometry as column to points.csv for fmm in cygwin
    #detector_df.insert(11, "geom", geometry, True)
    # TODO: replace path to local cygwin64 installation or comment it out -> example result of fmm
    # in data/network/matched.csv
    detector_gdf.to_csv("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\points.csv", sep=";")

    return detector_gdf, geometry


def plot():
    """
    Get a base map of Munich using osmnx, match the merged detector locations using a map matching algorithm
    (here: fmm), add the matched location to the base map and plot the result
    """

    # get a base map and the merged detector locations
    map = get_base_graphml()
    df_detectors, coords = get_detectors()

    # https://stackoverflow.com/questions/64104884/osmnx-project-point-to-street-segments
    print("TODO: Automate the matching using fmm and copy the result into data/network")
    print("The resulting file is data/network/matched.csv")

    # get mapped points
    df_matched = pd.read_csv(networkDataRoot + "matched.csv", sep=";")
    matched_locs = df_matched["mgeom"]
    nodes = []
    # reformat detector locations from [LINESTRING(lon lat,lon lat)] to [(lat, lon)]
    for node in matched_locs:
        lon_lat = node.split(',')[0][11:].split(' ')
        nodes.append((lon_lat[1], lon_lat[0]))

    # add matched detector locations to base map and graph the result
    map.add_nodes_from(nodes)
    _ = ox.plot_graph(map, bgcolor="white",
                      node_size=3, node_color="red",
                      edge_linewidth=0.3, edge_color="black")


def main():
    plot()


if __name__ == '__main__':
    main()

