#Version: 1.0
#Author: Francis Dowuona

import os
import arcpy

wkspace = arcpy.env.scratchWorkspace

defaultxLSfile = os.path.join(os.path.dirname(wkspace),'TableToFeature.xls')

def uniquefileName(filepath):
    filename, extension = os.path.splitext(filepath)
    counter = 1

    while os.path.exists(filepath):
        filepath = filename  + str(counter)  + extension
        counter += 1

    return filepath


def getexportfileFormat(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0]

    file = os.path.join(os.path.dirname(wkspace), filename + '_ExportFile.xls') 

    return uniquefileName(file)

def gpxtopolygon(inputGPXfile, outputFeature):
            try:
                arcpy.conversion.GPXtoFeatures(inputGPXfile,arcpy.os.path.join(wkspace,'WayPoints'))

                polygons={}
                with arcpy.da.SearchCursor(arcpy.os.path.join(wkspace,'WayPoints'), ['Shape@XYZ','Descript']) as sc:
                    for x in sc:
                        if x[1] not in polygons.keys():
                            polygons[x[1]] = [[x[0][0],x[0][1]]]
                        else:
                            polygons[x[1]].append([x[0][0],x[0][1]])
                            
                arcpy.management.Delete(arcpy.os.path.join(wkspace,'WayPoints'))

                arcpy.management.CreateFeatureclass(arcpy.os.path.dirname(outputFeature),arcpy.os.path.basename(outputFeature),
                                                    'POLYGON','','DISABLED','DISABLED',arcpy.SpatialReference(4326))
                arcpy.management.AddField(outputFeature,'Descript', 'TEXT','','','50','Descript', 'NULLABLE', 'NON_REQUIRED','')

                with arcpy.da.InsertCursor(outputFeature, ['Shape@','Id','Descript']) as ic:
                    for x in polygons:
                        arr = arcpy.Array(arcpy.Point(*coord)for coord in polygons[x])
                        _newpoly = arcpy.Polygon(arr, arcpy.SpatialReference(4326))
                        desc_ = x
                        _id = 0
                        ic.insertRow((_newpoly,_id,desc_))
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)


def tableToFeature(table, _x_field, y_field, interval, spatialreference, outputFeature, 
                    export_to_file= False, exportfile=''):
            try:
                #Process: Make XY Event Layer of input Table
                table_Layer = "table_Layer"
                arcpy.management.MakeXYEventLayer(table, _x_field, y_field, 'table_Layer', spatialreference)

                #Process: Make Line Feature from Event Layer
                arcpy.management.PointsToLine(table_Layer, arcpy.os.path.join(wkspace,'PointsToLine'), '', '', 'NO_CLOSE')

                arcpy.edit.Densify(arcpy.os.path.join(wkspace,'PointsToLine'), 'DISTANCE', interval, '', '')

                arcpy.management.FeatureVerticesToPoints(arcpy.os.path.join(wkspace,'PointsToLine'), outputFeature, 'ALL')

                arcpy.management.Delete(arcpy.os.path.join(wkspace,'PointsToLine'))

                arcpy.management.AddGeometryAttributes(outputFeature, 'POINT_X_Y_Z_M', '', '', spatialreference)

                if export_to_file:
                    arcpy.conversion.TableToExcel(outputFeature, exportfile)
                
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [GPXToPolygon,TableToFeature]

class TableToFeature(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Table To Feature"
        self.description = "Geoprocessing script tool for creating interpolated point features from x-and y- coordinates in a table"
        self.canRunInBackground = True
        self.category = "Interpolation"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='table',
                                displayName='XY Table',
                                direction='Input',
                                datatype='GPTableView',
                                parameterType='Required')
        param1 = arcpy.Parameter(name='x_field',
                                displayName='X Field',
                                datatype='Field',
                                direction='Input',
                                parameterType='Required')
        param1.parameterDependencies = [param0.name]
        param2 = arcpy.Parameter(name='y_field',
                                displayName='Y Field',
                                datatype='Field',
                                direction='Input',
                                parameterType='Required')
        param2.parameterDependencies = [param0.name]
        param3 = arcpy.Parameter(name='interval',
                                displayName='Interval',
                                datatype='GPLinearUnit',
                                direction='Input',
                                parameterType='Required')
        param3.value = '10 METERS'
        param4 = arcpy.Parameter(name='_spatialreference',
                                        displayName='Spatial Reference',
                                        direction='Input',
                                        datatype='GPCoordinateSystem',
                                        parameterType='Optional')
        param4.value = 'PROJCS["WGS_1984_UTM_Zone_30N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'
        param5 = arcpy.Parameter(name='outputFeature',
                                        displayName='Output Feature Class',
                                        datatype='DEShapefile',
                                        parameterType='Required',
                                        direction='Output')
        param6 = arcpy.Parameter(name='export_to_file',
                                        displayName='Export to File',
                                        datatype='GPBoolean',
                                        direction='Input',
                                        parameterType='Optional')
        param6.value = 'False'
        param7 = arcpy.Parameter(name='Export_file',
                                    displayName='Output Excel File',
                                    datatype='DEFile',
                                    enabled='False',
                                    parameterType='Required',
				                    direction='Output')
        param7.filter.list = ['xls']
        #param7.value = getexportfileFormat(defaultxLSfile)
        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        params[7].enabled = params[6].value

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, params, messages):
        """The source code of the tool."""
        if __name__ == '__main__':
            tableToFeature(params[0].valueAsText, params[1].valueAsText, params[2].valueAsText, params[3].valueAsText,
                            params[4].valueAsText, params[5].valueAsText, params[6].value, params[7].valueAsText)
        return

class GPXToPolygon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "GPX To Polygon"
        self.description = "Geoprocessing script tool for creating polygon features from gpx file"
        self.canRunInBackground = True
        self.category = "Conversion"
    
    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='input_gpxFile',
                                displayName='Input GPX File',
                                direction='Input',
                                datatype='DEFile',
                                parameterType='Required')
        param0.filter.list = ['gpx']
        param1 = arcpy.Parameter(name='OutputFeatureClass',
                                displayName='Output Feature Class',
                                datatype='DEShapefile',
                                parameterType='Required',
                                direction='Output')
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
            gpxtopolygon(params[0].valueAsText, params[1].valueAsText)
        return