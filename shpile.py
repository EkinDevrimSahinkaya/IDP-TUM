from qgis.core import *
from osgeo import gdal
from qgis.core import (
    Qgis,
    QgsProject,
    QgsPathResolver
)
from qgis.gui import (
    QgsLayerTreeMapCanvasBridge,
)

gdal.SetConfigOption('SHAPE_RESTORE_SHX', 'YES')
QgsApplication.setPrefixPath("C:\\Program Files\\QGIS 3.34.0", True)
qgs = QgsApplication([], True)
project = QgsProject.instance()

# project.read('./okan.qgz')

qgs.initQgis()
path_to_airports_layer = "./munich_loops_mapping_in_progress.shp"
vlayer = QgsVectorLayer(path_to_airports_layer, "Airports layer", "ogr")

if not vlayer.isValid():

    print("Layer failed to load!")

else:

    QgsProject.instance().addMapLayer(vlayer)
# Finally, exitQgis() is called to remove the

# provider and layer registries from memory
# Save the project to the same
project.write()
# ... or to a new file
project.write('./my_new_qgis_project.qgz')
qgs.exitQgis()