import os
import glob
import subprocess

import fiona  # this import needs to happen before osmnx
import networkx as nx
import networkx.classes.filters
import osmnx as ox
import pandas as pd
import numpy as np
import geopandas as gpd

from networkx import MultiDiGraph
from geopandas import GeoDataFrame
from shapely.geometry import Point
from osmnx import settings, utils_graph, io
from shutil import copy
# from subprocess import Popen, PIPE
from config import ROOT_DIR
from copy import deepcopy

# Use this citation when referencing OSMnx in work
# Boeing, G. 2017. OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks.
# Computers, Environment and Urban Systems 65, 126-139.

path_map_munich = ROOT_DIR + "/data/network/map_munich.graphml"
mergedDataRoot = ROOT_DIR + "/data/merged_data/"
xmlDataRoot = ROOT_DIR + "/data/xml_data/"
networkDataRoot = ROOT_DIR + "/data/network/"

node_size = 3  # used to define the size of map matched detector nodes; 2 is default size


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


def save_graph_shapefile_directional(graph: MultiDiGraph, filepath=None, encoding="utf-8"):
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

    # save_graph_shapefile_directional(graph, filepath=networkDataRoot)

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
    # TODO: replace path to local cygwin64 installation or comment it out -> contains example result of fmm
    #  in data/network/matched.csv
    detector_gdf.to_csv("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\points.csv", sep=";")

    return detector_gdf, geometry


def to_shp(map: MultiDiGraph, nodes: [(str, str)]):
    # TODO: delete, probably useless
    # Convert nodes to a GeoDataFrame
    node_attributes = {node: map.nodes[node] for node in map.nodes()}
    node_coords = {node: data.get("pos", None) for node, data in map.nodes(data=True)}
    node_geometries = [Point(coords) for coords in node_coords.values()]
    gdf_nodes = gpd.GeoDataFrame(node_attributes.values(), geometry=node_geometries)

    # Specify the output shapefile path
    output_shapefile = networkDataRoot+"map_nodes.shp"

    # Write the GeoDataFrame to a shapefile
    gdf_nodes.to_file(output_shapefile)


def plot():
    """
    Get a base map of Munich using osmnx, match the merged detector locations using a map matching algorithm
    (here: fmm), add the matched location to the base map and plot the result
    """
    nodes_list = []
    flow_list = []

    # get a base map and the merged detector locations
    map = get_base_graphml()
    nodes_map = deepcopy(map)
    df_detectors, coords = get_detectors()

    # https://stackoverflow.com/questions/64104884/osmnx-project-point-to-street-segments
    print("TODO: Automate the matching using fmm and copy the result into data/network")
    print("The resulting file is data/network/matched.csv")

    # get mapped points
    # TODO: for the server, we can just move matched.csv to the correct location instead of reading and writing the file
    copy("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\matched.csv",
         networkDataRoot+"matched.csv")
    df_matched = pd.read_csv(networkDataRoot + "matched.csv", sep=";")

    # fmm seems to sometimes write out wrong information:
    # LINESTRING(lon lat) instead of LINESTRING(lon lat,lon lat) -> fix those entries:
    def _fix_linestring(ls: str):
        ls_split = ls.split(',')
        # if ls contains a valid linestring, return ls
        if len(ls_split) == 2:
            return ls
        # else ls is of form LINESTRING(lon lat)
        else:
            lon, lat = ls[11:-1].split(' ')
            return ls[:-1] + ",{} {})".format(lon, lat)

    # some matched detector locations are broken -> fix them and add them back to the 'mgeom' column
    df_matched["mgeom"] = pd.Series([_fix_linestring(ls) for ls in df_matched['mgeom']], name='mgeom')

    # get id and mgeom columns from matched detector locations
    matched_detector_locations = df_matched[["id", "mgeom"]]

    # get detector flows
    latest_xml_data_csv = max(glob.glob(xmlDataRoot + "*.csv"), key=os.path.getctime)
    df_xml = pd.read_csv(latest_xml_data_csv)
    flows = df_xml[["detid", "flow"]].set_index('detid')

    # reformat detector locations from [LINESTRING(lon lat,lon lat)] to [(lat, lon)]
    for id, node in matched_detector_locations.values:
        lon_lat = node.split(',')[0][11:].split(' ')
        flow = flows.loc[id, 'flow']
        nodes_list.append((lon_lat[1], lon_lat[0]))
        flow_list.append(flow)
        # add x, y, flow information to new detector nodes in an osmnx network
        nodes_map.add_node(id, x=lon_lat[0], y=lon_lat[1], flow=flow)

    # create a node dict that sets the size of a node depending on its flow value -> effectively hide non-detector nodes
    nodes_sizes_dict = {n[0]: 0 if n[1] == "NULL" else node_size for n in nodes_map.nodes(data='flow', default="NULL")}
    nx.set_node_attributes(nodes_map, nodes_sizes_dict, "size")

    # ox.graph_to_gdfs(nodes_map, nodes=False).explore()

    # add lon, lat columns to matched.csv so we can add it to add_layer.py
    if 'lon' not in df_matched:
        # https://stackoverflow.com/questions/5917522/unzipping-and-the-operator#:~:text=25-,zip
        lats, lons = zip(*nodes_list)
        df_matched.insert(len(df_matched.columns), "lon", list(lons))
        df_matched.insert(len(df_matched.columns), "lat", list(lats))
    df_matched.insert(len(df_matched.columns), "flow", flow_list)
    # write updated dataframe to matched.csv
    df_matched.to_csv(networkDataRoot + "coords_matched.csv", sep=";", index=True)

    # add matched detector locations to base map and graph the result
    # ox.io.save_graph_shapefile(map, networkDataRoot+"map_and_points")
    ox.io.save_graph_geopackage(map, networkDataRoot+"map_and_points.gpkg")
    ox.io.save_graph_geopackage(nodes_map, networkDataRoot+"detector_nodes.gpkg")

    # TODO: color edges between detector nodes
    for u, v, k in map.edges(keys=True):
        pass

    # map.add_nodes_from(nodes)
    # _ = ox.plot_graph(map, bgcolor="white",
    #                   node_size=3, node_color="red",
    #                   edge_linewidth=0.3, edge_color="black")


def main():
    plot()


if __name__ == '__main__':
    main()
