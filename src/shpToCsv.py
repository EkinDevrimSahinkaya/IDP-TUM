from time import sleep

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qgis._gui import QgsMapCanvas
from qgis.core import *
from qgis.utils import iface
import datetime
import glob
import os
from qgis.PyQt import QtGui
import geopandas as gpd
import aiohttp
import asyncio
import csv
import pandas as pd
import time
import datetime
import glob
import os
#import shapefile
import pyproj
from pyproj import CRS
from qgis.utils import iface
from config import ROOT_DIR

rootPath = ROOT_DIR.replace("\\", "/")
path_to_csv_file = rootPath + "/LRZ/munich_loops_mapping_in_progress.csv"
path_to_shp_file = rootPath + "/LRZ/munich_loops_mapping_in_progress.shp"


df = gpd.read_file(path_to_shp_file)
df['geometry'] = df['geometry'].astype(str).str.replace('POINT (', '')
df['geometry'] = df['geometry'].astype(str).str.replace(')', '')
df[['lon','lat']] = df['geometry'].str.split(' ',expand=True)
df.rename(columns={'DETEKTO':'detid'}, inplace=True)
df.to_csv(path_to_csv_file, sep=',', encoding='utf-8')

