from mappymatch import package_root
from mappymatch.constructs.trace import Trace
import pandas as pd
from config import ROOT_DIR
import glob
import os
from mappymatch.utils.plot import plot_trace
from mappymatch.constructs.geofence import Geofence
from mappymatch.utils.plot import plot_geofence
from mappymatch.maps.nx.nx_map import NxMap, NetworkType
from mappymatch.utils.plot import plot_map
from mappymatch.matchers.lcss.lcss import LCSSMatcher
def nler():
    mergedDataRoot = ROOT_DIR + "/data/merged_data/"
    latest_merged_data_csv = max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime)

    df = pd.read_csv(package_root() /latest_merged_data_csv)
    print(df.loc[:,['lon', 'lat']].head())
    trace = Trace.from_csv(package_root() / latest_merged_data_csv, lat_column="lat", lon_column="lon", xy=True)
    plot_trace(trace, point_color="black", line_color="yellow")
    geofence = Geofence.from_trace(trace, padding=1e3)
    plot_trace(trace, point_color="black", m=plot_geofence(geofence))
    nx_map = NxMap.from_geofence(geofence, network_type=NetworkType.DRIVE)
    # plot_map(nx_map)
    matcher = LCSSMatcher(nx_map)
    matches = matcher.match_trace(trace)
    df = matches.matches_to_dataframe()
    df.to_csv(r'C:\Users\TR1\PycharmProjects\IDP-TUM\src\data\nler\export_dataframe.csv', index=None, header=True)


if __name__ == '__main__':
    nler()
    print("End of Program")
