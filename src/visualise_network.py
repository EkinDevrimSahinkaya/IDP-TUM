import os
import glob
import subprocess

import fiona  # this import needs to happen before osmnx
import osmnx as ox
import pandas as pd
import numpy as np

from networkx import MultiDiGraph, Graph
from geopandas import GeoDataFrame
from shapely.geometry import Point, Polygon, MultiPoint, LineString
from osmnx import settings, utils_graph, io
#from subprocess import Popen, PIPE
from config import ROOT_DIR


# Use this citation when referencing OSMnx in work
# Boeing, G. 2017. OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks.
# Computers, Environment and Urban Systems 65, 126-139.

path_map_munich = ROOT_DIR + "/data/network/map_munich.graphml"
mergedDataRoot = ROOT_DIR + "/merged_data/"
networkDataRoot = ROOT_DIR + "/data/network/"


def find_cygwin() -> str:
    """ Iteratre over all drives (in reverse) to find the cygwin root folder

    :return: path to cygwin64
    """
    cygname = "cygwin64"
    driveStr = subprocess.check_output("fsutil fsinfo drives")
    driveStr = driveStr.strip().lstrip(b'Drives: ')
    drives = driveStr.split()
    #print(drives)
    # iterate in reverse, my cygwin is in D:
    for drive in drives[::-1]:
        drive = drive.decode(encoding='UTF-8')
        for root, dirs, files in os.walk(drive, topdown=True):
            for dir in dirs:
                if dir == cygname:
                    cygname = os.path.abspath(os.path.join(root, dir))
                    #print(cygname)
                    return cygname


def save_graph_shapefile_directional(graph, filepath=None, encoding="utf-8"):
    # default filepath if none was provided
    if filepath is None:
        filepath = os.path.join(ox.settings.data_folder, "shapefile")

    # if save folder does not already exist, create it (shapefiles
    # get saved as set of files)
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
    # load detector static_data
    latest_merged_data_csv = max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime)
        # (csv_path
        #                       if (csv_path := max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime))
        #                       else absolute_path_to_csv_file)

    detector_df = pd.read_csv(latest_merged_data_csv)

    # create GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(detector_df['lon'], detector_df['lat'])]
    crs = {'init': 'epsg:4326'}
    detector_gdf = GeoDataFrame(detector_df, crs=crs, geometry=geometry)

    # Add the point geometry as column to points.csv for fmm in cygwin
    detector_df.insert(11, "geom", geometry, True)
    detector_df.to_csv("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\points.csv", sep=";")

    return detector_gdf, geometry


def plot():
    map = get_base_graphml()
    edges = ox.graph_to_gdfs(map, nodes=False)
    df_detectors, coords = get_detectors()
    # Add detector static_data to map
    # lat_lon = [(p.x, p.y) for p in coords]
    # # fill lat_lon
    # points = LineString(lat_lon)
    # print(str(points.wkt).replace(" ", "", 1))
    # with open("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\points.txt", "w") as f:
    #     f.write(str(points.wkt).replace(" ", "", 1))

    # with open("D:\\cygwin64\\home\\User\\fmm\\matching\\network\\points.txt", "r") as f:
    #     points = f.read()

    # https://stackoverflow.com/questions/64104884/osmnx-project-point-to-street-segments
    df_matched = pd.read_csv(networkDataRoot+"matched.csv", )
    # combined = edges.join(df_matched)
    #
    # fig, ax = ox.plot_graph(combined,
    #                         node_size=0.5, node_color="black",
    #                         edge_linewidth=0.3, edge_color="white",
    #                         show=False)
    # points.plot()
    # plt.show()

    print("Automate the matching using fmm and copy the result into data/network")
    print("The resulting file is data/network/matched.csv")

    # get mapped points
    df_matched = pd.read_csv(networkDataRoot+"matched.csv", sep=";")
    edges = df_matched["mgeom"]
    nodes = []
    for p in edges:
        lon_lat = p[11:-1].split(' ')
        nodes.append((lon_lat[1], lon_lat[0]))

    # #graph base map
    # g = Graph()
    map.add_nodes_from(nodes)
    _ = ox.plot_graph(map,
                      node_size=0.5, node_color="red",
                      edge_linewidth=0.3, edge_color="white")


def main():
    plot()


if __name__ == '__main__':
    plot()
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
    #print(result[0].decode(encoding='UTF-8'))

    # main()
