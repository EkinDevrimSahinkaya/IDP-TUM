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
from qgis.core import QgsVectorLayer, QgsProject, QgsApplication, QgsVectorFileWriter
import json, tempfile, os

edgesData = ROOT_DIR + "/data/network/edges.shp"
# gpkgData = ROOT_DIR + "/data/network/map_and_points.gpkg"
nodesData = ROOT_DIR + "/data/network/detector_nodes.gpkg"
mergedDataRoot = ROOT_DIR + "/data/merged_data/"
projectDataRoot = ROOT_DIR + "/data/project_data/"
trafficRanges = [[(0.0, 1.0), 'No Data', QtGui.QColor('#afafaf'), 0.26],
                 [(1.1, 100.0), 'Very Low Traffic', QtGui.QColor('#008000'), 0.66],
                 [(100.1, 200.0), 'Low Traffic', QtGui.QColor('#00a500'), 0.66],
                 [(200.1, 300.0), 'Normal Traffic', QtGui.QColor('#f5ff09'), 0.66],
                 [(300.1, 400.0), 'Busy Traffic', QtGui.QColor('#ffa634'), 0.66],
                 [(400.1, 1000.0), 'Very Busy Traffic', QtGui.QColor('#ff2712'), 0.66]]

prefixPath = r'C:\Program Files\QGIS 3.34.0\bin'  # TODO: change prefix path to your QGIS root directory
QgsApplication.setPrefixPath(prefixPath, True)
qgs = QgsApplication([], True)
project = QgsProject.instance()
qgs.initQgis()

# Adding Map
tms = '    crs=EPSG:3857&format&type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'
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
              line_width: float,
              geom_type: GeometryType,
              opacity: float = 1.0,
               ) -> QgsRendererRange:
    """
    Colorize the detector data according to the measured traffic flow

    :param traffic_range: Lower and upper bounds for heaviness of traffic
    :param label: Label the amount of traffic flow
    :param color: Color corresponding to the measured traffic
    :param geom_type: GeometryType of the loaded detector data
    :param opacity: Opacity of the corresponding points
    :param line_width: thickness of line
    :return: QgsRendererRange instance
    """
    (lower, upper) = traffic_range
    symbol = QgsSymbol.defaultSymbol(geom_type)
    line_layer = QgsSimpleLineSymbolLayer()
    line_layer.setWidth(line_width)
    symbol.changeSymbolLayer(0, line_layer)
    symbol.setColor(color)
    symbol.setOpacity(opacity)

    return QgsRendererRange(lower, upper, symbol, label)


def add_vector_layer(layer: QgsVectorLayer):
    """
    Adds the given QgsVectorLayer to the current QGIS project if the layer is valid. Otherwise, print the error summary

    :param layer: A QgsVectorLayer object
    """
    if layer.isValid():
        print(layer.name() + " loaded successfully!")
        project.addMapLayer(layer)
    else:
        print(layer.name() + " failed to load")
        print(layer.error().summary())


def mapAndPoint():
    """
    Define a base map using OSM and load previously pulled detector location data. Color the detector points
    according to the measured traffic flow and map the points on top of the base map. Save the resulting .qgs file
    in project_data.
    """

    # Adding Points 14748 osmn point, 21bin osmn edges,  36 bin testlayer
    # TODO: ':=' available for python >= 3.8 -> compatibility issues?
    if not (merged_points_data_csv := max(glob.glob(mergedDataRoot + "*.csv"), key=os.path.getctime)):
        print("No files found in {}".format(mergedDataRoot))
    # TODO: include line below to use map matched detector locations
    merged_points_data_csv = ROOT_DIR + "/data/network/coords_matched.csv"
    # matched.csv uses ';' as delimiter -> check if we use the matched detector locations as the csvlayer
    delim = ';' if "matched.csv" in merged_points_data_csv[-11:] else ','
    options = '?delimiter={}&xField=lon&yField=lat&crs=epsg:4326'.format(delim)
    uri = "file:///{}{}".format(merged_points_data_csv, options)

    add_vector_layer(layer          := QgsVectorLayer(edgesData, "testlayer_shp", "ogr"))
    add_vector_layer(gpkg_edgelayer := QgsVectorLayer(nodesData + "|layername=edges", "OSMnx edges", "ogr"))
    add_vector_layer(gpkg_nodelayer := QgsVectorLayer(nodesData + "|layername=nodes", "OSMnx nodes", "ogr"))
    add_vector_layer(csvlayer       := QgsVectorLayer(uri, "Points", "delimitedtext"))

    shpField = 'fid'
    csvField = 'fid'
    joinObject = QgsVectorLayerJoinInfo()
    joinObject.setJoinFieldName(csvField)
    joinObject.setTargetFieldName(shpField)
    joinObject.setJoinLayerId(gpkg_nodelayer.id())
    joinObject.setUsingMemoryCache(True)
    joinObject.setJoinLayer(gpkg_nodelayer)
    gpkg_edgelayer.addJoin(joinObject)

    # set the size of the points from gpkg_nodelayer to be data driven using the "size" attribute
    # create a new symbol for rendering the points of the node layer
    size_symbol = QgsSymbol.defaultSymbol(gpkg_nodelayer.geometryType())
    # set a data-defined override for the size, based on the 'size' attribute
    size_symbol.setDataDefinedSize(QgsProperty.fromField("size"))
    # set the renderer to the layer
    gpkg_nodelayer.setRenderer(QgsSingleSymbolRenderer(size_symbol))
    # refresh the layer to apply changes -> not necessary I think since we dont have a QGIS instance running
    # gpkg_nodelayer.triggerRepaint()

    # color detector locations stored in csvlayer according to traffic flow
    target_field = 'flow'
    range_list = []
    range_listforSHP = []
    geom_type = csvlayer.geometryType()
    geom_typeforSHP = gpkg_edgelayer.geometryType()

    for traffic_range in trafficRanges:
        color_range = add_color(*traffic_range, geom_type)
        range_list.append(color_range)
        color_rangeforSHP = add_color(*traffic_range, geom_typeforSHP)
        range_listforSHP.append(color_rangeforSHP)

    # render the colored csvlayer
    renderer = QgsGraduatedSymbolRenderer('', range_list)
    classification_method = QgsApplication.classificationMethodRegistry().method("EqualInterval")
    renderer.setClassificationMethod(classification_method)
    renderer.setClassAttribute(target_field)
    csvlayer.setRenderer(renderer)
    print("Classification of detectors done.", csvlayer)
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:3857'), True)

    # render the colored GEOPACKAGE
    renderer = QgsGraduatedSymbolRenderer('', range_listforSHP)
    classification_method = QgsApplication.classificationMethodRegistry().method("EqualInterval")
    renderer.setClassificationMethod(classification_method)
    # renderer.setClassAttribute("OSMnx nodes_flow")
    expression = 'case when "OSMnx nodes_flow" IS NULL then 0 else "OSMnx nodes_flow" end'
    field = expression
    renderer.setClassAttribute(field)
    gpkg_edgelayer.setRenderer(renderer)
    print("Classification of detectors done.", gpkg_edgelayer)
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:3857'), True)

    # Center QGIS on the rlayer
    canvas = QgsMapCanvas()
    canvas.setCurrentLayer(rlayer)
    canvas.setExtent(rlayer.extent())
    canvas.refresh()

    # save the created QGIS project
    project.write(filename=os.path.join(projectDataRoot, "mapAndPoint.qgs"))
    updateDataforWebsite(gpkg_edgelayer)


def updateDataforWebsite(gpkg_edgelayer):
    #update folder path to "/layers/" change github website
    websiteFolder = ROOT_DIR + "/layers/"

    (temp_fd, temp_path) = tempfile.mkstemp(suffix=".geojson")
    os.close(temp_fd)
    _writer = QgsVectorFileWriter.writeAsVectorFormat(gpkg_edgelayer, temp_path, "utf-8", driverName="GeoJSON")

    # read GeoJSON file and save content in a Javascript variable
    with open(temp_path, 'r') as geojson_file:
        geojson_content = geojson_file.read()
        js_content = f"var json_OSMnxedges_1 = {geojson_content};"

    # Write to gpkg data to JavaScript file
    js_path = websiteFolder + "OSMnxedges_1.js"
    with open(js_path, "w") as js_file:
        js_file.write(js_content)

    # Delete temporary folder
    os.remove(temp_path)

    print("Convert process done, file saved.")

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

