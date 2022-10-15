import arcpy
import os
import ConversionUtils

def getExt(path):
    bname = os.path.basename(path)

    return '.shp' if bname.endswith('.shp') else ''

def wks(path):
    return os.path.dirname(path)

def bname(path):
    b_name =  os.path.basename(path).split('.')[0]
    for x in b_name:
        if x =='-':
            b_name = b_name.replace('-','_')
    return b_name

def tabletopolygon(xytable, x_field, y_field, descipt_field, in_coord_sys, project_condtion, out_coord_sys, outputfeature):

    try:
        polygons={}
        Line='Line'
        arcpy.SetProgressorLabel('Creating event layer of {}.........'.format(bname(xytable)))
        arcpy.MakeXYEventLayer_management(xytable,x_field,y_field,Line,in_coord_sys,'')

        arcpy.SetProgressorLabel('Creating point Features from {} event layer.........'.format(bname(xytable)))
        output = arcpy.FeatureToPoint_management(Line, r"in_memory\{}_points".format(bname(xytable)))

        if project_condtion == 'PROJECTION':
            sr1,sr2 = arcpy.SpatialReference(),arcpy.SpatialReference()
            sr1.loadFromString(in_coord_sys)
            sr2.loadFromString(out_coord_sys)
            arcpy.SetProgressorLabel('Projecting points from {} to {}.........'.format(sr1.name, sr2.name))
            arcpy.AddMessage('Projecting points from {} to {}.........'.format(sr1.name, sr2.name))
            arcpy.Project_management(output,os.path.join(wks(outputfeature),'{}_proj{}'.format(bname(xytable),getExt(outputfeature))),
                                        out_coord_sys,'',in_coord_sys)
            
            output = os.path.join(wks(outputfeature),'{}_proj{}'.format(bname(xytable),getExt(outputfeature)))

        with arcpy.da.SearchCursor(output,['Shape@XY', descipt_field]) as sc:
            for row in sc:
                if row[1] not in polygons.keys():
                    polygons[row[1]]=[[row[0][0],row[0][1]]]
                else:
                    polygons[row[1]].append([row[0][0],row[0][1]])

        srref = in_coord_sys if project_condtion == 'NO_PROJECTION' else out_coord_sys

        arcpy.CreateFeatureclass_management(os.path.dirname(outputfeature), os.path.basename(outputfeature), 'POLYGON', '' , '', '',srref )
        arcpy.AddField_management(outputfeature, descipt_field, 'TEXT')
        with arcpy.da.InsertCursor(outputfeature, ['Shape@',descipt_field]) as ic:
            for name in polygons:
                arr = arcpy.Array([arcpy.Point(*coord)for coord in polygons[name]])
                arr.append(arr[0])
                newpoly = arcpy.Polygon(arr, srref)
                ic.insertRow((newpoly, name))
        pass
    except arcpy.ExecuteError as err:
        arcpy.AddError(err)
    finally:
        if arcpy.Exists(polygons):
            arcpy.Delete_management(polygons)
        if arcpy.Exists(output):
            arcpy.Delete_management(output)
    return

def gpx_to_polygon(GPXFiles, name_desc_col, in_coord_sys, outputFeature, compute_area='', area_unit=''):
    try:
        polygons={}
        gpxFiles = ConversionUtils.SplitMultiInputs(GPXFiles)

        for gpxfile in gpxFiles:
            arcpy.GPXtoFeatures_conversion(gpxfile, r"in_memory\{}_points".format(bname(gpxfile)))
            output = r"in_memory\{}_points".format(bname(gpxfile))

            arcpy.Project_management(output, os.path.join(wks(outputFeature), '{}_project{}'.format(bname(gpxfile),getExt(outputFeature))),
                                        in_coord_sys,'',arcpy.SpatialReference(4326),'PRESERVE_SHAPE')
            if arcpy.Exists(r"in_memory\{}_points".format(bname(gpxfile))):
                arcpy.Delete_management(r"in_memory\{}_points".format(bname(gpxfile)))
            output = os.path.join(wks(outputFeature), '{}_project{}'.format(bname(gpxfile),getExt(outputFeature)))

            with arcpy.da.SearchCursor(output, ['Shape@XYZ',name_desc_col]) as sc:
                for row in sc:
                    if row[1] not in polygons.keys():
                        polygons[row[1]]=[[row[0][0],row[0][1]]]
                    else:
                        polygons[row[1]].append([row[0][0],row[0][1]])
            if arcpy.Exists(output):
                arcpy.Delete_management(output)

        arcpy.CreateFeatureclass_management(wks(outputFeature), os.path.basename(outputFeature), 'POLYGON', '', '', '', in_coord_sys)
        arcpy.AddField_management(outputFeature, name_desc_col, 'TEXT')
        with arcpy.da.InsertCursor(outputFeature, ['Shape@',name_desc_col]) as ic:
            for name in polygons:
                arr = arcpy.Array([arcpy.Point(*coord)for coord in polygons[name]])
                arr.append(arr[0])
                newpoly = arcpy.Polygon(arr, in_coord_sys)
                ic.insertRow((newpoly, name))
        if compute_area == 'AREA':
            area_field = 'Area_{}'.format(area_unit.capitalize())
            area_field = area_field[0:10]
            arcpy.AddField_management(outputFeature, area_field, 'DOUBLE')
            arcpy.CalculateField_management(outputFeature, area_field, '!shape.area@{}!'.format(area_unit.lower()),'PYTHON')
        pass
    except arcpy.ExecuteError as err:
        arcpy.AddError(err)
    finally:
        if arcpy.Exists(polygons):
            arcpy.Delete_management(polygons)
    return

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [TableToPolygon,GPXToPolygon]


class TableToPolygon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Table To Polygon"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Conversion'

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='param0', displayName='XY Table',parameterType='Required',
                                    datatype='GPTableView', direction='Input')
        param1 = arcpy.Parameter(name='param1', displayName='X Field',parameterType='Required',
                                    datatype='Field', direction='Input')
        param2 = arcpy.Parameter(name='param2', displayName='Y Field',parameterType='Required',
                                    datatype='Field', direction='Input')   
        param3 = arcpy.Parameter(name='param3', displayName='Decription Field',parameterType='Required',
                                    datatype='Field', direction='Input')
        param1.filter.list = param2.filter.list = ['LONG','DOUBLE','FLOAT']   
        param3.filter.list = ['TEXT','OID']                          
        param1.parameterDependencies = param2.parameterDependencies =param3.parameterDependencies= [param0.name]
        #
        param4 = arcpy.Parameter(name='param4', displayName='In Coordinate System',parameterType='Required',
                                    datatype='Coordinate System', direction='Input')
        param4.value = '4326'
        param5 = arcpy.Parameter(name='param5', displayName='Project Coordinate System',parameterType='Optional',
                                    datatype='String', direction='Input')
        param5.filter.type = 'ValueList'
        param5.filter.list = ['NO_PROJECTION','PROJECTION']
        param5.value = param5.filter.list[0]
        param6 = arcpy.Parameter(name='param6', displayName='Out Coordinate System',parameterType='Optional',
                                    datatype='Coordinate System', direction='Input')
        param6.value = '32630'
        param7 = arcpy.Parameter(name='param7', displayName='Output FeatureClass', datatype='DEFeatureClass',
                                    direction='Output', parameterType='Required')
        params = [param0,param1,param2,param3,param4,param5,param6,param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        params[6].enabled = 'True' if params[5].valueAsText == 'PROJECTION' else 'False'
        return

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if params[0].value:
            if not ((params[0].valueAsText).endswith('.csv') or (params[0].valueAsText).endswith('.txt')):
                params[0].setErrorMessage('Invalid Table Feature')

        return

    def execute(self, params, messages):
        """The source code of the tool."""
        tabletopolygon(params[0].valueAsText,params[1].valueAsText,params[2].valueAsText,params[3].valueAsText,
                        params[4].valueAsText,params[5].valueAsText,params[6].valueAsText,params[7].valueAsText)
        return

class GPXToPolygon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "GPX To Polygon"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Conversion'

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(name='param0', displayName='XY Table',parameterType='Required',
                                    datatype='DEFile', direction='Input', multiValue='True')
        param0.filter.list = ['gpx']
        param1 = arcpy.Parameter(name='param1', displayName='Name|Description',parameterType='Required',
                                    datatype='String', direction='Input')
        param1.filter.type = 'ValueList'
        param1.filter.list = ['Name','Descript'] 
        param1.value = param1.filter.list[0]

        param2 = arcpy.Parameter(name='param2', displayName='Coordinate System',parameterType='Required',
                                    datatype='Coordinate System', direction='Input')
        param2.value = '4326'

        param3 = arcpy.Parameter(name='param3', displayName='Output FeatureClass', datatype='DEFeatureClass',
                                    direction='Output', parameterType='Required')
        #
        param4 = arcpy.Parameter(name='param4', displayName='Compute Area',parameterType='Optional',
                                    datatype='String', direction='Input')
        param4.filter.type = 'ValueList'
        param4.filter.list = ['NO_AREA','AREA'] 
        param4.value = param4.filter.list[0]   
        param5 = arcpy.Parameter(name='param5', displayName='Area Unit',parameterType='Optional',
                                    datatype='String', direction='Input')
        param5.filter.type = 'ValueList'
        param5.filter.list = ['ACRES','ARES','HECTARES'] 
        param5.value = param5.filter.list[0] 

        params = [param0,param1,param2,param3,param4,param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, params):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        params[5].enabled = 'True' if params[4].valueAsText == 'AREA' else 'False'
        return

    def updateMessages(self, params):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if params[2].value:
            wkt = params[2].valueAsText
            sr = arcpy.SpatialReference()
            sr.loadFromString(wkt)
            if params[4].value == 'AREA' and str(sr.type) == 'Geographic':
                params[4].setErrorMessage('Area cannot be computed with geographic coordinate system')

        return

    def execute(self, params, messages):
        """The source code of the tool."""
        gpx_to_polygon(params[0].valueAsText,params[1].valueAsText,
                        params[2].valueAsText,params[3].valueAsText,
                        params[4].valueAsText,params[5].valueAsText)
        return
