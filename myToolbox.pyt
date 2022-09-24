import arcpy
import os

wkspace = arcpy.env.scratchWorkspace

def gpxtoPolygon(Inputgpxfile, outputfeature):
    arcpy.GPXtoFeatures_conversion(Input_GPX_File=Inputgpxfile, Output_Feature_class= os.path.join(wkspace,'tempPoints'))
    polygons={}
    with arcpy.da.SearchCursor(os.path.join(wkspace,'tempPoints'), ['Shape@XYZ','Descript']) as sc:
        for i in sc:
            if i[1] not in polygons.keys():
                polygons[i[1]] = [[i[0][0], i[0][1]]]
            else:
                polygons[i[1]].append([i[0][0], i[0][1]])
    arcpy.Delete_management(os.path.join(wkspace,'tempPoints'))
    arcpy.CreateFeatureclass_management(os.path.dirname(outputfeature),os.path.basename(outputfeature),geometry_type='POLYGON',
                                        has_m='DISABLED',has_z='DISABLED',spatial_reference=arcpy.SpatialReference(4326))
    arcpy.AddField_management(outputfeature,field_name='Descript', field_type='TEXT', field_length='50')
    ic = arcpy.da.InsertCursor(outputfeature, ['Shape@','Descript'])
    for i in polygons:
        arr = arcpy.Array([arcpy.Point(*coords)for coords in polygons[i]])
        arr.append(arr[0])
        newpoly = arcpy.Polygon(arr, arcpy.SpatialReference(4326))
        ic.insertRow((newpoly,i))

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "myGISToolbox"
        self.alias = "myGISToolbox"

        # List of tool classes associated with this toolbox
        self.tools = [GPXToPolygon]


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
                gpxtoPolygon(Inputgpxfile=params[0].valueAsText, outputfeature=params[1].valueAsText)
            except arcpy.ExecuteError as err:
                arcpy.AddError(err)
        return
