import datetime
import glob
import os

from time import sleep
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qgis._gui import QgsMapCanvas
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt import QtGui
from shapely import GeometryType
from config import ROOT_DIR

mergedDataRoot = ROOT_DIR + "/data/merged_data/"
projectDataRoot = ROOT_DIR + "/data/project_data/"
trafficRanges = [[(0.0, 100.0), 'Very Low Traffic', QtGui.QColor('#008000')],
                 [(100.1, 200.0), 'Low Traffic', QtGui.QColor('#00a500')],
                 [(200.1, 300.0), 'Normal Traffic', QtGui.QColor('#f5ff09')],
                 [(300.1, 400.0), 'Busy Traffic', QtGui.QColor('#ffa634')],
                 [(400.1, 1000.0), 'Very Busy Traffic', QtGui.QColor('#ff2712')]]

prefixPath = r'C:\Program Files\QGIS 3.34.0\bin'  # TODO: change prefix path to your QGIS root directory
QgsApplication.setPrefixPath(prefixPath, True)
qgs = QgsApplication([], True)
project = QgsProject.instance()
qgs.initQgis()

# Adding Map
tms = '	crs=EPSG:3857&format&type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'
rlayer = QgsRasterLayer(tms, 'OSM', 'wms')
print(rlayer.crs())
if rlayer.isValid():
    print("Base Layer loaded!")
    project.addMapLayer(rlayer)
else:
    print('invalid layer')
    print(rlayer.error().summary())


def add_color(traffic_range: (float, float),
              label: str,
              color: QColor,
              geom_type: GeometryType,
              opacity: float = 1.0) -> QgsRendererRange:
    """
    Colorize the detector data according to the measured traffic flow

    :param traffic_range: Lower and upper bounds for heaviness of traffic
    :param label: Label the amount of traffic flow
    :param color: Color corresponding to the measured traffic
    :param geom_type: GeometryType of the loaded detector data
    :param opacity: Opacity of the corresponding points
    :return: QgsRendererRange instance
    """

    (lower, upper) = traffic_range
    symbol = QgsSymbol.defaultSymbol(geom_type)
    symbol.setColor(color)
    symbol.setOpacity(opacity)

    return QgsRendererRange(lower, upper, symbol, label)


def mapAndPoint():
    """
    Define a base map using OSM and load previously pulled detector location data. Color the detector points
    according to the measured traffic flow and map the points on top of the base map. Save the resulting .qgs file
    in project_data.
    """

    # Adding Points
    # TODO: ':=' available for python >= 3.8 -> compatibility issues?
    if not (latest_merged_data_csv := max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime)):
        print("No files found in {}".format(mergedDataRoot))
    # TODO: include line below to use map matched detector locations
    latest_merged_data_csv = ROOT_DIR + "/data/network/matched.csv"
    # matched.csv uses ';' as delimiter -> check if we use the matched detector locations as the csvlayer
    delim = ';' if "matched.csv" in latest_merged_data_csv[-11:] else ','
    options = '?delimiter={}&xField=lon&yField=lat&crs=epsg:4326'.format(delim)
    uri = "file:///{}{}".format(latest_merged_data_csv, options)

    csvlayer = QgsVectorLayer(uri, "Points", "delimitedtext")
    if csvlayer.isValid():
        print("Detector Layer loaded!")
        print(iface)
        project.addMapLayer(csvlayer)
    else:
        print("CSV Layer failed to load!")

    # color detector locations according to traffic
    target_field = 'flow'
    range_list = []
    geom_type = csvlayer.geometryType()

    for traffic_range in trafficRanges:
        color_range = add_color(*traffic_range, geom_type)
        range_list.append(color_range)

    # render the colored csvlayer
    renderer = QgsGraduatedSymbolRenderer('', range_list)
    classification_method = QgsApplication.classificationMethodRegistry().method("EqualInterval")
    renderer.setClassificationMethod(classification_method)
    renderer.setClassAttribute(target_field)
    csvlayer.setRenderer(renderer)
    print("Classification of detectors done.", csvlayer)
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:3857'), True)

    # Center QGIS on the rlayer
    canvas = QgsMapCanvas()
    canvas.setCurrentLayer(rlayer)
    canvas.setExtent(rlayer.extent())
    canvas.refresh()

    # save the created QGIS project
    project.write(filename=os.path.join(projectDataRoot, "mapAndPoint.qgs"))


def layer():
    """
    If projectDataRoot is not empty, delete its files before mapping the detector data onto a base map
    """

    # https://stackoverflow.com/questions/53513/how-do-i-check-if-a-list-is-emptyhttps://stackoverflow.com/questions/53513/how-do-i-check-if-a-list-is-empty
    if os.listdir(projectDataRoot):
        delete_files_in_directory(projectDataRoot)
    else:
        print("No files found in the directory.")
    mapAndPoint()


def delete_files_in_directory(directory_path):
    """
    Delete all files in a given directory, ignores sub-directories

    :param directory_path: Absolute path of the directory
    """

    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("All files deleted successfully.")
    except OSError:
        print("Error occurred while deleting files.")


def main():
    layer()


if __name__ == '__main__':
    main()
    print("End of Program")
