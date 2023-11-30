from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qgis._gui import QgsMapCanvas
from qgis.core import *
from qgis.utils import iface
def mapAndPoint():
    prefixPath = r'C:\Program Files\QGIS 3.34.0\bin'  # TODO: change prefix path to your QGIS root directory
    QgsApplication.setPrefixPath(prefixPath, True)
    qgs = QgsApplication([], True)
    project = QgsProject.instance()

    qgs.initQgis()

    #Adding Map
    tms = '	crs=EPSG:3857&format&type=xyz&url=https://tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0'
    rlayer = QgsRasterLayer(tms,'OSM', 'wms')
    print(rlayer.crs())
    if rlayer.isValid():
        print("Layer loaded1!")
        project.addMapLayer(rlayer)
    else:
        print('invalid layer')
        print(rlayer.error().summary())

    #Adding Points
    absolute_path_to_csv_file = 'C:/Users/okann/PycharmProjects/pythonProject1/Datas/2023_11_15_18_30_21_15min_static.csv'
    options = '?delimiter=,&xField=lon&yField=lat&crs=epsg:4326'
    uri = "file:///{}{}".format(absolute_path_to_csv_file, options)

    csvlayer = QgsVectorLayer(uri, "Points", "delimitedtext")
    if not csvlayer.isValid():
        print("Layer failed to load!")
    else:
        print("Layer loaded!")
        print(iface)
        QgsProject.instance().addMapLayer(csvlayer)
        # QTimer.singleShot(1000, set_project_crs)
        # csvlayer.triggerRepaint()

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:3857'), True)
    canvas = QgsMapCanvas()
    canvas.setCurrentLayer(rlayer)
    canvas.setExtent(rlayer.extent())
    canvas.refresh()
    project.write(filename="mapAndPoints.qgs")

def set_project_crs():
    # Set CRS to EPSG:3857
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:3857'))

def main():
    mapAndPoint()


if __name__ == '__main__':
    main()
    print("End of Program")