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

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
outputDataPath = os.path.join(ROOT_DIR, "output_data", "*.csv")
projectDataRoot = os.path.join(ROOT_DIR, "project_data")
trafficRanges = [(0.0, 100.0),
                 (100.1, 200.0),
                 (200.1, 300.0),
                 (300.1, 400.0),
                 (400.1, 1000.0)]

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
    print("Layer loaded!")
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
    :param label: Label the amount of traffic
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
    absolute_path_to_csv_file = os.path.join(projectDataRoot, "test.csv")
    # TODO: ':=' available for python >= 3.8 -> compatibility issues?
    latest_output_data_csv = (csv_path
                              if (csv_path := max(glob.glob(outputDataPath), key=os.path.getctime))
                              else absolute_path_to_csv_file)
    options = '?delimiter=,&xField=lon&yField=lat&crs=epsg:4326'
    uri = "file:///{}{}".format(latest_output_data_csv, options)

    csvlayer = QgsVectorLayer(uri, "Points", "delimitedtext")
    if not csvlayer.isValid():
        print("CSV Layer failed to load!")
    else:
        print("Layer loaded!")
        print(iface)
        project.addMapLayer(csvlayer)

    # color detector locations according to traffic
    target_field = 'flow'
    range_list = []
    geom_type = csvlayer.geometryType()

    # TODO: can pack the color groups into some sort of enum/list/dict and iterate over that
    # First group 0-100
    color_range = add_color(trafficRanges[0], 'Very Low Traffic', QtGui.QColor('#008000'), geom_type)
    range_list.append(color_range)

    # Second Group 100-200
    color_range = add_color(trafficRanges[1], 'Low Traffic', QtGui.QColor('#00a500'), geom_type)
    range_list.append(color_range)

    # Third Group 200-300
    color_range = add_color(trafficRanges[2], 'Normal Traffic', QtGui.QColor('#f5ff09'), geom_type)
    range_list.append(color_range)

    # Fourth Group 300-400
    color_range = add_color(trafficRanges[3], 'Busy Traffic', QtGui.QColor('#ffa634'), geom_type)
    range_list.append(color_range)

    # Fifth Group 400-1000
    color_range = add_color(trafficRanges[4], 'Very Busy Traffic', QtGui.QColor('#ff2712'), geom_type)
    range_list.append(color_range)

    # render the colored csvlayer
    renderer = QgsGraduatedSymbolRenderer('', range_list)
    classification_method = QgsApplication.classificationMethodRegistry().method("EqualInterval")
    renderer.setClassificationMethod(classification_method)
    renderer.setClassAttribute(target_field)
    csvlayer.setRenderer(renderer)
    print("Classify eklendi.", csvlayer)
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
