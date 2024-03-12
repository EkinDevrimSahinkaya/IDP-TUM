var wms_layers = [];


        var lyr_OSM_0 = new ol.layer.Tile({
            'title': 'OSM',
            'type': 'base',
            'opacity': 1.000000,
            
            
            source: new ol.source.XYZ({
    attributions: ' ',
                url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            })
        });
var format_OSMnxedges_1 = new ol.format.GeoJSON();
var features_OSMnxedges_1 = format_OSMnxedges_1.readFeatures(json_OSMnxedges_1, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_OSMnxedges_1 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_OSMnxedges_1.addFeatures(features_OSMnxedges_1);
var lyr_OSMnxedges_1 = new ol.layer.Vector({
                declutter: true,
                source:jsonSource_OSMnxedges_1, 
                style: style_OSMnxedges_1,
                popuplayertitle: "OSMnx edges",
                interactive: true,
    title: 'OSMnx edges<br />\
    <img src="styles/legend/OSMnxedges_1_0.png" /> No Data<br />\
    <img src="styles/legend/OSMnxedges_1_1.png" /> Very Low Traffic<br />\
    <img src="styles/legend/OSMnxedges_1_2.png" /> Low Traffic<br />\
    <img src="styles/legend/OSMnxedges_1_3.png" /> Normal Traffic<br />\
    <img src="styles/legend/OSMnxedges_1_4.png" /> Busy Traffic<br />\
    <img src="styles/legend/OSMnxedges_1_5.png" /> Very Busy Traffic<br />'
        });

lyr_OSM_0.setVisible(true);lyr_OSMnxedges_1.setVisible(true);
var layersList = [lyr_OSM_0,lyr_OSMnxedges_1];
lyr_OSMnxedges_1.set('fieldAliases', {'fid': 'fid', 'u': 'u', 'v': 'v', 'key': 'key', 'osmid': 'osmid', 'name': 'name', 'highway': 'highway', 'maxspeed': 'maxspeed', 'oneway': 'oneway', 'reversed': 'reversed', 'length': 'length', 'from': 'from', 'to': 'to', 'lanes': 'lanes', 'ref': 'ref', 'bridge': 'bridge', 'access': 'access', 'tunnel': 'tunnel', 'width': 'width', 'junction': 'junction', 'est_width': 'est_width', 'OSMnx nodes_osmid': 'OSMnx nodes_osmid', 'OSMnx nodes_y': 'OSMnx nodes_y', 'OSMnx nodes_x': 'OSMnx nodes_x', 'OSMnx nodes_street_count': 'OSMnx nodes_street_count', 'OSMnx nodes_size': 'OSMnx nodes_size', 'OSMnx nodes_ref': 'OSMnx nodes_ref', 'OSMnx nodes_highway': 'OSMnx nodes_highway', 'OSMnx nodes_flow': 'OSMnx nodes_flow', });
lyr_OSMnxedges_1.set('fieldImages', {'fid': '', 'u': '', 'v': '', 'key': '', 'osmid': '', 'name': '', 'highway': '', 'maxspeed': '', 'oneway': '', 'reversed': '', 'length': '', 'from': '', 'to': '', 'lanes': '', 'ref': '', 'bridge': '', 'access': '', 'tunnel': '', 'width': '', 'junction': '', 'est_width': '', 'OSMnx nodes_osmid': '', 'OSMnx nodes_y': '', 'OSMnx nodes_x': '', 'OSMnx nodes_street_count': '', 'OSMnx nodes_size': '', 'OSMnx nodes_ref': '', 'OSMnx nodes_highway': '', 'OSMnx nodes_flow': '', });
lyr_OSMnxedges_1.set('fieldLabels', {'fid': 'no label', 'u': 'no label', 'v': 'no label', 'key': 'no label', 'osmid': 'no label', 'name': 'no label', 'highway': 'no label', 'maxspeed': 'no label', 'oneway': 'no label', 'reversed': 'no label', 'length': 'no label', 'from': 'no label', 'to': 'no label', 'lanes': 'no label', 'ref': 'no label', 'bridge': 'no label', 'access': 'no label', 'tunnel': 'no label', 'width': 'no label', 'junction': 'no label', 'est_width': 'no label', 'OSMnx nodes_osmid': 'no label', 'OSMnx nodes_y': 'no label', 'OSMnx nodes_x': 'no label', 'OSMnx nodes_street_count': 'no label', 'OSMnx nodes_size': 'no label', 'OSMnx nodes_ref': 'no label', 'OSMnx nodes_highway': 'no label', 'OSMnx nodes_flow': 'no label', });
lyr_OSMnxedges_1.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});