import os
import glob
import subprocess
import time

import fiona  # this import needs to happen before osmnx
import networkx as nx
import osmnx as ox
import pandas as pd
import numpy as np

from networkx import MultiDiGraph
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from shapely.ops import split
from osmnx import settings, utils_graph, io
from shutil import copy
from config import ROOT_DIR
from copy import deepcopy
from osmnx.distance import nearest_edges
from taxicab.distance import shortest_path

# Use this citation when referencing OSMnx in work
# Boeing, G. 2017. OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks.
# Computers, Environment and Urban Systems 65, 126-139.

path_map_munich = ROOT_DIR + "/data/network/simplify_map_munich.graphml"
mergedDataRoot = ROOT_DIR + "/data/merged_data/"
xmlDataRoot = ROOT_DIR + "/data/xml_data/"
networkDataRoot = ROOT_DIR + "/data/network/"

node_size = 3  # used to define the size of map matched detector nodes; 2 is default size
ox.settings.use_cache = False
ox.settings.log_console = False


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
        graph = ox.graph_from_place("München, Bayern, Deutschland", network_type="drive", simplify=False)
        ox.save_graphml(graph, path_map_munich)
    else:
        graph = ox.load_graphml(path_map_munich)

    # TODO: this saves the nodes and edges of 'graph' to separate shapefiles, probably useless since we use gpkg now
    save_graph_shapefile_directional(graph, filepath=networkDataRoot)

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


def connect_detector_nodes(G: MultiDiGraph, detector_nodes: [(float, float)], detector_ids: [int]):
    """
    Connects a list of (lon, lat) values of detector nodes to the graph G by splitting edges up and reconnecting them
    using the detector nodes

    :param G: A MultiDiGraph containing nodes and edges for a road network
    :param detector_nodes: a list of (lat, lon) = (y, x) values of detector nodes
    :param detector_ids: a list containing the  osmid of the detector node corresponding to the entry in detector_nodes
    """
    # TODO: (un)install scikit-learn
    y, x = zip(*detector_nodes)
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    start = time.time_ns()
    edges = nearest_edges(G, list(x), list(y), return_dist=False)
    end = time.time_ns()
    print("{}s to execute nearest_edges()".format((end - start) / 1e9))

    len_edges = len(edges)
    count = 0
    delete = []

    start = time.time_ns()
    for idx, e in enumerate(edges):
        if count > 1:
            # skip this edge because it has been processed
            count -= 1
            continue

        # save info about current edge, necessary for end of loop
        cur_edge = e
        # count the number of detector nodes on the current edge
        if idx < len_edges:
            count = 1
            # check if the next detector nodes are on top of cur_edge
            while idx + count < len_edges and cur_edge == edges[idx+count]:
                # count number of edges that are the same == number of detector on the same edge
                count += 1

        # create list of [lon, lat, osmid, flow] info of each detector node on the current edge
        dets = [[lon, lat, osmid, flow]
                for osmid, (lat, lon), flow
                in zip(detector_ids[idx:idx+count],  # for osmid
                       detector_nodes[idx:idx+count],  # for (lat, lon)
                       [G.nodes(data='flow')[x] for x in detector_ids[idx:idx+count]])
                ]

        u, v, key = e
        edge_attrs = G[u][v]

        if G.has_edge(u, v, key):
            delete.append((u, v, key))

        start_node = G.nodes[u]
        end_node = G.nodes[v]
        if 'geometry' not in edge_attrs[0]:
            # create trivial geometry for start and end point
            edge_attrs[0]['geometry'] = LineString([[start_node['x'], start_node['y']], [end_node['x'], end_node['y']]])

        # append distance of each detector node from the start of the current edge
        for i, p in enumerate([Point(det[0], det[1]) for det in dets]):
            dets[i].append(edge_attrs[0]['geometry'].project(p))
        # sort current detector nodes according to their distance from starting point of current edge
        sorted_dets = sorted(dets, key=lambda det: det[-1])

        # calculate geometry of new edges
        line = edge_attrs[0]['geometry']  # retrieve LineString stored in geometry of current edge
        new_geoms = []
        # create [Point(x, y)] of the detector nodes to use for line splitting
        for i, split_point in enumerate([Point(sd[0], sd[1]) for sd in sorted_dets]):
            dist_along_line = line.project(split_point)  # get distance from start of line to split_point
            # if a detector node is too close to the start point of the current edge, give it a small distance
            if dist_along_line == 0.0:
                dist_along_line = 1e-15
            point_on_line = line.interpolate(dist_along_line)  # find point on line that is exactly dist_along_line away from start
            # From (start, end) we want to get [(start, split_point), (split_point, end)]
            # But we get [(start, left), (left, right), (right, end)] because of to .buffer(1e-8) creating
            # a circle aroung split_point which intersects the Linestring twice (left and right side of circle)
            # We need to close the resulting holes in the new Linestring by including split_line in split1 and split2
            split_line = split(line, point_on_line.buffer(1e-8))
            split1, split2 = list(split_line.geoms[0].coords), list(split_line.geoms[-1].coords)
            split1 = LineString(split1[:-1] + [point_on_line])
            split2 = LineString([point_on_line] + split2[1:])
            # append new geometry to new_geoms, iterate over the rest of linestring
            new_geoms.append(split1)
            line = split2
        # split2 now contains geometry for last detector node connected to end of the original edge
        new_geoms.append(line)  # new_geoms[i] now contains an edge with detector i and i+1 as start and end point

        # create train of edges
        # TODO: sometimes edge_attrs looks like {0: ..., 1: ..., 2: ...} -> what does this mean? do we just need the first one?
        for i in range(count):
            # https://stackoverflow.com/questions/72523683/#:~:text=Then%20you%20could%20e.g.%20define%20the%20new%20edge%20like%20this
            if i == 0:
                dist = shortest_path(G, (start_node['y'], start_node['x']), (float(sorted_dets[i][1]), float(sorted_dets[i][0])), e, e)[0]
                G.add_edge(u_for_edge=u, v_for_edge=sorted_dets[i][2], **{**edge_attrs[0], 'geometry': new_geoms[i], 'length': round(dist, 3)})
            else:
                dist = shortest_path(G, (float(sorted_dets[i-1][1]), float(sorted_dets[i-1][0])), (float(sorted_dets[i][1]), float(sorted_dets[i][0])), e, e)[0]
                G.add_edge(u_for_edge=sorted_dets[i-1][2], v_for_edge=sorted_dets[i][2], **{**edge_attrs[0], 'geometry': new_geoms[i], 'length': round(dist, 3), 'flow': sorted_dets[i-1][3]})
            if i == count - 1:
                dist = shortest_path(G, (float(sorted_dets[i][1]), float(sorted_dets[i][0])), (end_node['y'], end_node['x']), e, e)[0]
                G.add_edge(u_for_edge=sorted_dets[i][2], v_for_edge=v, **{**edge_attrs[0], 'geometry': new_geoms[i+1], 'length': round(dist, 3), 'flow': sorted_dets[i][3]})  # TODO: love the IDIOT SANDWICH <3

    G.remove_edges_from(delete)
    count = 0
    for u, v, key in delete:
        if G.has_edge(u, v, key):
            count += 1
    print("THERE ARE STILL {} ORIGINAL EDGES LEFT ".format(count))

    end = time.time_ns()
    print("{}s to execute loop".format((end-start) / 1e9))


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
    df_matched["mgeom"] = df_matched["mgeom"].apply(_fix_linestring)

    # get id and mgeom columns from matched detector locations
    matched_detector_locations = df_matched[["id", "mgeom"]]

    # get detector flows
    latest_xml_data_csv = max(glob.glob(xmlDataRoot + "*.csv"), key=os.path.getctime)
    df_xml = pd.read_csv(latest_xml_data_csv)
    flows = df_xml[["detid", "flow"]].set_index('detid')

    # reformat detector locations from [LINESTRING(lon lat,lon lat)] to [(lat, lon)]
    detector_ids = []  # useful to map detector nodes to existing edges
    for id, node in matched_detector_locations.values:
        lon_lat = node.split(',')[0][11:].split(' ')
        flow = flows.loc[id, 'flow']
        flow_list.append(flow)
        nodes_list.append((lon_lat[1], lon_lat[0]))
        detector_ids.append(id)
        # add x, y, flow information to new detector nodes in an osmnx network
        nodes_map.add_node(id, x=lon_lat[0], y=lon_lat[1], flow=flow)

    # create a node dict that sets the size of a node depending on its flow value -> effectively hide non-detector nodes
    nodes_sizes_dict = {n[0]: 0 if n[1] == "NULL" else node_size for n in nodes_map.nodes(data='flow', default="NULL")}
    nx.set_node_attributes(nodes_map, nodes_sizes_dict, "size")

    # add lon, lat columns to matched.csv so we can add it to add_layer.py
    if 'lon' not in df_matched:
        # https://stackoverflow.com/questions/5917522/unzipping-and-the-operator#:~:text=25-,zip
        lats, lons = zip(*nodes_list)
        # add lon and lat info to the end of the dataframe
        df_matched.insert(len(df_matched.columns), "lon", list(lons))
        df_matched.insert(len(df_matched.columns), "lat", list(lats))
    if 'flow' not in df_matched:
        df_matched.insert(len(df_matched.columns), "flow", flow_list)
    # write updated dataframe to matched.csv
    df_matched.to_csv(networkDataRoot + "coords_matched.csv", sep=";", index=True)

    # connect matched detector locations to base map and graph the result
    print("start timer")
    start = time.time_ns()
    connect_detector_nodes(nodes_map, nodes_list, detector_ids)
    end = time.time_ns()
    print("{}s to execute connect_detector_nodes with {} nodes".format((end-start)/1e9, len(nodes_list)))

    # save the graph after connecting the detector nodes to the map
    ox.io.save_graph_geopackage(nodes_map, networkDataRoot + "detector_nodes.gpkg")


def main():
    plot()


if __name__ == '__main__':
    main()
