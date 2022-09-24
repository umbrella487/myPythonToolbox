# -*- coding: utf-8 -*-

import arcpy
import os

wkspace = arcpy.env.scratchWorkspace

def uniquify(file):
    _file,_ext = os.path.splitext(file)
    counter = 1
    while os.path.exists(file):
        file = _file + str(counter) + _ext
        counter+=1
    return file

defaultxlsFile = uniquify(os.path.join(os.path.dirname(wkspace),'TableToPointsExportFile.xls'))

def tabletoPolygon(table, x_field, y_field, description_field, _spatial_reference, outputfeature):

    Line = 'Line'
    arcpy.MakeXYEventLayer_management(table=table, in_x_field=x_field, in_y_field=y_field, 
                                        spatial_reference= _spatial_reference, out_layer=Line)
    polygons={}
    with arcpy.da.SearchCursor(Line,['Shape@XY',description_field]) as sc:
        for i in sc:
            if i[1] not in polygons.keys():
                polygons[i[1]] = [[i[0][0], i[0][1]]]
            else:
                polygons[i[1]].append([i[0][0], i[0][1]])
    arcpy.CreateFeatureclass_management(os.path.dirname(outputfeature),os.path.basename(outputfeature),geometry_type='POLYGON',
                                        has_m='DISABLED',has_z='DISABLED',spatial_reference=_spatial_reference)
    arcpy.AddField_management(outputfeature,field_name='Descript', field_type='TEXT', field_length='50')
    ic = arcpy.da.InsertCursor(outputfeature, ['Shape@','Descript'])
    for i in polygons:
        arr = arcpy.Array([arcpy.Point(*coords)for coords in polygons[i]])
        arr.append(arr[0])
        newpoly = arcpy.Polygon(arr, _spatial_reference)
        ic.insertRow((newpoly,i))
    return

def _gpxtoPolygon(inputGPXfile, outputFeature):
    arcpy.GPXtoFeatures_conversion(Input_GPX_File= inputGPXfile, Output_Feature_class= os.path.join(wkspace,'Points'))
    polygons={}
    with arcpy.da.SearchCursor(os.path.join(wkspace,'Points'),['Shape@XYZ','Descript']) as sc:
        for i in sc:
            if i[1] not in polygons.keys():
                polygons[i[1]] = [[i[0][0], i[0][1]]]
            else:
                polygons[i[1]].append([i[0][0], i[0][1]])
    arcpy.Delete_management(os.path.join(wkspace,'Points'))
    arcpy.CreateFeatureclass_management(os.path.dirname(outputFeature),os.path.basename(outputFeature),geometry_type='POLYGON',
                                        has_m='DISABLED',has_z='DISABLED',spatial_reference=arcpy.SpatialReference(4326))
    arcpy.AddField_management(outputFeature,field_name='Descript', field_type='TEXT', field_length='50')
    ic = arcpy.da.InsertCursor(outputFeature, ['Shape@','Descript'])
    for i in polygons:
        arr = arcpy.Array([arcpy.Point(*coords)for coords in polygons[i]])
        arr.append(arr[0])
        newpoly = arcpy.Polygon(arr, arcpy.SpatialReference(4326))
        ic.insertRow((newpoly,i))
    return

def _interpolate(in_table, x_field, y_field, interval, spatial_reference, outputfeature, export_to_file=False, exportFile = ''):
    Temp_point = 'Temp_point'
    arcpy.MakeXYEventLayer_management(table=in_table, in_x_field=x_field, in_y_field=y_field, out_layer=Temp_point, 
                                        spatial_reference=spatial_reference)
    arcpy.PointsToLine_management(Input_Features=Temp_point, Output_Feature_Class=os.path.join(wkspace,'Line'))
    arcpy.Densify_edit(in_features=os.path.join(wkspace,'Line'), densification_method='DISTANCE', distance=interval, max_angle='0.1')
    arcpy.FeatureVerticesToPoints_management(in_features=os.path.join(wkspace,'Line'), out_feature_class=outputfeature, point_location='ALL')
    arcpy.Delete_management(os.path.join(wkspace,'Line'))

    if export_to_file:
        arcpy.CopyFeatures_management(in_features=outputfeature, out_feature_class=os.path.join(wkspace,'outputcopy'))
        arcpy.AddGeometryAttributes_management(Input_Features=os.path.join(wkspace,'outputcopy'), Geometry_Properties='POINT_X_Y_Z_M',
                                            Coordinate_System=spatial_reference)
        arcpy.TableToExcel_conversion(Input_Table=os.path.join(wkspace,'outputcopy'), Output_Excel_File=exportFile, Use_field_alias_as_column_header=False,
                                        Use_domain_and_subtype_description=False)
        arcpy.Delete_management(os.path.join(wkspace,'outputcopy'))

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [GPXToPolygon,TableToPolygon,TableToPoints]

class GPXToPolygon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "GPX To Polygon"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Conversion'

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='gpxfile',displayName='Input GPX File',
                                direction='Input',parameterType='Required',
                                datatype='DEFile')
        param0.filter.list=['gpx']
        param1 = arcpy.Parameter(name='outputFeature',displayName='Output Feature Class',
                                direction='Output',parameterType='Required',
                                datatype='DEFeatureClass')
        params = [param0,param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, params, messages):
        """The source code of the tool."""
        if __name__ == '__main__':
            try:
                _gpxtoPolygon(params[0].valueAsText, params[1].valueAsText)
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)
        return

class TableToPolygon(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Table To Polygon"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Conversion'

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='XY_table',displayName='XY Table',
                                direction='Input',parameterType='Required',
                                datatype='DEFile')
        param0.filter.list = ['csv','txt']
        param1 = arcpy.Parameter(name='x_field',displayName='X Field',
                                direction='Input',parameterType='Required',
                                datatype='Field')
        param2 = arcpy.Parameter(name='y_field',displayName='Y Field',
                                direction='Input',parameterType='Required',
                                datatype='Field')
        param1.filter.list = param2.filter.list = ['Short','Long','Float','Double']
        param3 = arcpy.Parameter(name='desc_field',displayName='Description Field',
                                direction='Input',parameterType='Required',
                                datatype='Field')
        param3.filter.list=['OID','Text']
        param1.parameterDependencies = param2.parameterDependencies = param3.parameterDependencies = [param0.name]
        param4 = arcpy.Parameter(name='spatial_ref',displayName='Spatial Reference',
                                direction='Input',parameterType='Optional',
                                datatype='GPSpatialReference')
        param4.value = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        param5 = arcpy.Parameter(name='OutputFeature',displayName='Output Feature Class',
                                direction='Output',parameterType='Required',
                                datatype='DEFeatureClass')
        params = [param0,param1,param2,param3,param4,param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, params, messages):
        """The source code of the tool."""
        if __name__ == '__main__':
            try:
                tabletoPolygon(params[0].valueAsText,params[1].valueAsText,params[2].valueAsText,params[3].valueAsText,
                                params[4].valueAsText,params[5].valueAsText)
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)
        return

class TableToPoints(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Table To Point"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Interpolation'

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='XY_table',displayName='XY Table',
                                direction='Input',parameterType='Required',
                                datatype='DEFile')
        param0.filter.list = ['csv','txt']
        param1 = arcpy.Parameter(name='x_field',displayName='X Field',
                                direction='Input',parameterType='Required',
                                datatype='Field')
        param2 = arcpy.Parameter(name='y_field',displayName='Y Field',
                                direction='Input',parameterType='Required',
                                datatype='Field')
        param1.filter.list = param2.filter.list = ['Short','Long','Float','Double']
        param1.parameterDependencies = param2.parameterDependencies = [param0.name]
        param3 = arcpy.Parameter(name='interval',displayName='Interval',
                                direction='Input',parameterType='Required',
                                datatype='GPLinearUnit')
        param3.value = '10 METERS'
        param4 = arcpy.Parameter(name='spatial_ref',displayName='Spatial Reference',
                                direction='Input',parameterType='Optional',
                                datatype='GPSpatialReference')
        param4.value = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        param5 = arcpy.Parameter(name='OutputFeature',displayName='Output Feature Class',
                                direction='Output',parameterType='Required',
                                datatype='DEFeatureClass')
        param6 = arcpy.Parameter(name='export_to_file',displayName='Export To File',
                                direction='Input',parameterType='Optional',
                                datatype='GPBoolean')
        param7 = arcpy.Parameter(name='export_file',displayName='Export To File',
                                direction='Output',parameterType='Required',
                                datatype='DEFile', enabled='False')
        param7.filter.list=['xls']
        param7.value = defaultxlsFile
        params = [param0,param1,param2,param3,param4,param5,param6,param7]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        params[7].enabled = params[6].value
        return

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, params, messages):
        """The source code of the tool."""
        if __name__ == '__main__':
            try:
                _interpolate(in_table=params[0].valueAsText,x_field=params[1].valueAsText, y_field=params[2].valueAsText,
                            interval=params[3].valueAsText, spatial_reference=params[4].valueAsText,outputfeature=params[5].valueAsText,
                            export_to_file=params[6].value, exportFile=params[7].valueAsText)
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)
        return