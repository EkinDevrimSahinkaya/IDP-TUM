import os
import glob
import subprocess

import fiona  # this import needs to happen before osmnx
import osmnx as ox
import pandas as pd
import numpy as np
import geopandas as gpd

from networkx import MultiDiGraph, Graph, write_shp
from geopandas import GeoDataFrame
from shapely.geometry import Point
from osmnx import settings, utils_graph, io
from shutil import copy
# from subprocess import Popen, PIPE
from config import ROOT_DIR
from add_layer import trafficRanges

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

    # get a base map and the merged detector locations
    map = get_base_graphml()
    df_detectors, coords = get_detectors()

    # https://stackoverflow.com/questions/64104884/osmnx-project-point-to-street-segments
    print("TODO: Automate the matching using fmm and copy the result into data/network")
    print("The resulting file is data/network/matched.csv")

    # get mapped points
    # TODO: for the server, we can just move matched.csv to the correct location instead of reading and writing the file
    copy("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\matched.csv",
         networkDataRoot+"matched.csv")

    df_matched = pd.read_csv(networkDataRoot + "matched.csv", sep=";")
    nodes = []

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

    mgeom = df_matched["mgeom"]
    s = pd.Series([_fix_linestring(ls) for ls in df_matched['mgeom']], name='mgeom')
    # df_matched.loc(len(df_matched.mgeom))
    df_matched["mgeom"] = s

    matched_locs = df_matched[["id", "mgeom"]]

    # reformat detector locations from [LINESTRING(lon lat,lon lat)] to [(lat, lon)]
    for id, node in matched_locs.values:
        lon_lat = node.split(',')[0][11:].split(' ')
        nodes.append((lon_lat[1], lon_lat[0]))
        print(node)
        map.add_node(id, x=lon_lat[0], y=lon_lat[1])
    # add Geometry column to matched.csv so we can add it to add_layer.py
    if 'lon' not in df_matched:
        # https://stackoverflow.com/questions/5917522/unzipping-and-the-operator#:~:text=25-,zip
        lats, lons = zip(*nodes)
        df_matched.insert(len(df_matched.columns), "lat", list(lats))
        df_matched.insert(len(df_matched.columns), "lon", list(lons))
    # write updated dataframe to matched.csv
    df_matched.to_csv(networkDataRoot + "matched.csv", sep=";", index=True)

    # save_graph_shapefile_directional(map, filepath=networkDataRoot)

    # remove nodes that contain empty data
    # TODO: why do some nodes contain empty data?
    _, data = zip(*map.nodes(data=True))
    for i, d in enumerate(data):
        if i == 14043:
            print(d)
        if 'x' not in d:
            print("at data location {} couldnt find 'x': {}".format(i,d))
            break

    # add matched detector locations to base map and graph the result


    print(map.nodes)

    # save_graph_shapefile_directional(map, filepath=networkDataRoot)
    print("saved shapefile after adding nodes from matched.csv")
    # digraph = map.graph
    # to_shp(map, nodes)
    # write_shp(map.digraph, networkDataRoot)
    #map.add_nodes_from(nodes)
    ox.io.save_graph_shapefile(map, networkDataRoot+"map_and_points")
    ox.io.save_graph_geopackage(map, networkDataRoot+"map_and_points.gpkg")
    # color edges between detector nodes
    for u, v, k in map.edges(keys=True):
        pass

    # _ = ox.plot_graph(map, bgcolor="white",
    #                   node_size=3, node_color="red",
    #                   edge_linewidth=0.3, edge_color="black")


def main():
    plot()


if __name__ == '__main__':
    main()
    # cygpath = find_cygwin()
    #
    # cygwin_python = "D:\\cygwin64\\bin\\bash"
    # script_path = "D:\\cygwin64\\home\\User\\run.sh"#"D:\\cygwin64\\home\\User\\fmm\\example\\python\\fmm_test.py"
    # my_env = os.environ.copy()
    # my_env["PYTHONPATH"] = f"/usr/bin/python;{my_env['PYTHONPATH']}"
    #
    # p = subprocess.Popen(cygpath+"\\bin\\bash.exe", stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='UTF-8', env=my_env)
    # # p.stdin.write("/bin/pwd && ")
    # # p.stdin.write("/bin/cygpath -w /~ &&")
    # # p.stdin.write("/bin/cd /home/User/fmm &&")
    # # p.stdin.write()
    # p.stdin.write("/bin/ls /home/User/fmm &&")
    # p.stdin.write("/bin/python /home/User/fmm/example/python/fmm_example.py")
    # p.stdin.close()
    # out = p.stdout.read()
    # print(out)

    # try:
    #     subprocess.run([cygwin_python, script_path], check=True)#, env=my_env)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error executing the script: {e}")

    # cygwin = subprocess.Popen(['bash'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    #
    # # args = ['D:/cygwin64/bin/run', '-p', 'D:/cygwin64/home/User/fmm/example/fmm_test.py', '-wait']
    # # args2 = ['uname -a']
    # # try:
    # #     subprocess.check_output(args2, shell=True, stderr=subprocess.STDOUT)
    # # except subprocess.CalledProcessError as e:
    # #     raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    #
    # result = cygwin.communicate(input="uname -a\n".encode() +
    #                                   # "/mnt/d/cygwin64/bin/python3.9.exe".encode() +
    #                                   # "import os; environ = os.environ.copy()".encode() +
    #                                   "/mnt/d/cygwin64/Cygwin.bat".encode())
    #                                   # b"D:\cygwin64\bin/python3.9.exe D:/cygwin64/home/User/fmm/example/python/fmm_test.py")
    # print(result[0].decode(encoding='UTF-8'))

    # main()
