from time import sleep

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qgis._gui import QgsMapCanvas
from qgis.core import *
from qgis.utils import iface
import datetime
import glob
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
new_string = ROOT_DIR.replace("\\", "/")
outputRoot = new_string + "/IDP-TUM/output_data/*.csv"
dataRoot = new_string + "/IDP-TUM/Datas/mapAndPoints.qgs"

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
    print("Layer loaded1!")
    project.addMapLayer(rlayer)
else:
    print('invalid layer')
    print(rlayer.error().summary())
def mapAndPoint():


    #Adding Points
    latest_output_data_csv = max(glob.glob(outputRoot), key=os.path.getctime)
    absolute_path_to_csv_file = 'C:/Users/TR1/PycharmProjects/IDP-TUM/Datas/test.csv'
    options = '?delimiter=,&xField=lon&yField=lat&crs=epsg:4326'
    uri = "file:///{}{}".format(latest_output_data_csv, options)

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
    project.write(filename=dataRoot)

def set_project_crs():
    # Set CRS to EPSG:3857
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:3857'))

def layer():

    if os.listdir(new_string + "/IDP-TUM/Datas") == []:
        print("No files found in the directory.")
        mapAndPoint()
    else:
        delete_files_in_directory(new_string + "/IDP-TUM/Datas")
        mapAndPoint()

def delete_files_in_directory(directory_path):
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