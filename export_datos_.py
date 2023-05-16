from qgis.core import QgsVectorLayer, QgsFeatureRequest, QgsProject, QgsFeature, QgsVectorFileWriter
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog

def select_features_by_attribute(layer_path, attribute_field, attribute_value):
    layer = QgsVectorLayer(layer_path, 'layer', 'ogr')
    if not layer.isValid():
        print(f'Error: No se pudo cargar la capa "{layer_path}".')
        return

    field_index = layer.fields().lookupField(attribute_field)
    if field_index == -1:
        print(f'Error: La capa no tiene un campo llamado "{attribute_field}".')
        return

    expression = f'"{attribute_field}" LIKE \'%{attribute_value}%\''
    request = QgsFeatureRequest().setFilterExpression(expression)
    selected_features = list(layer.getFeatures(request))

    if len(selected_features) > 0:
        geometry_type = layer.geometryType()
        if geometry_type == 0:
            geometry_str = 'Point'
        elif geometry_type == 1:
            geometry_str = 'LineString'
        elif geometry_type == 2:
            geometry_str = 'Polygon'
        else:
            print(f'Error: Tipo de geometría no válido.')
            return
        uri = f'{geometry_str}?crs={layer.crs().authid()}'
        new_layer = QgsVectorLayer(uri, 'new_layer', 'memory')
        new_layer_data_provider = new_layer.dataProvider()
        new_layer_data_provider.addAttributes(layer.fields())
        new_layer.updateFields()
        new_layer_data_provider.addFeatures(selected_features)

        # Eliminar las columnas con más del 80% de filas NULL
        total_features = new_layer.featureCount()
        for field in new_layer.fields():
            if field.name() != attribute_field:
                null_count = 0
                for feature in new_layer.getFeatures():
                    if feature[field.name()] is None:
                        null_count += 1
                null_percentage = (null_count / total_features) * 100
                if null_percentage > 40:
                    new_layer_data_provider.deleteAttributes([field.index()])

        QgsProject.instance().addMapLayer(new_layer)

        new_layer_path, _ = QFileDialog.getSaveFileName(None, 'Guardar como', '', 'GeoPackage (*.gpkg)')
        if new_layer_path:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GPKG'
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            QgsVectorFileWriter.writeAsVectorFormatV2(new_layer, new_layer_path, layer.transformContext(), options)
            print(f'Se guardó la nueva capa en "{new_layer_path}".')
    else:
        print(f'No se encontraron entidades con el valor "{attribute_value}" en el campo "{attribute_field}".')

layer_path, _ = QFileDialog.getOpenFileName(None, 'Selecciona una capa', '', 'Shapefile (*.shp)')
if layer_path:
    attribute_field, ok = QInputDialog.getText(None, 'Entrada', 'Ingresa el nombre del campo de atributo:')
    if ok:
        attribute_value, ok = QInputDialog.getText(None, 'Entrada', 'Ingresa el valor de atributo a buscar:')
        if ok:
            select_features_by_attribute(layer_path, attribute_field, attribute_value)
