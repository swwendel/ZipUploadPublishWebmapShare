'''
Title: ZipUploadPublishWebMapShare.py
Author: Stephanie Wendel
Date: 4/18/2014
Description:



NOTE: This script uses the request module to make http requests. The script
    should be able to access this module in order for it to work correctly. If
    it is not installed, one place it can be downloaded from is Github:
    https://github.com/kennethreitz/requests
'''

import requests, arcpy, os, zipfile, json, socket

hostname = "http://" + socket.getfqdn()
username = ""
password = ""
shp = "CH_POI.shp"
zip = "CH_POI.zip"
filename = shp[:-4]
outputFolder = r"C:\Temp"
arcpy.env.workspace = outputFolder

# Create Token
token_params ={'username': username,
               'password': password,
               'referer': hostname,
               'f':'json'}
tokenResponse = requests.post("https://www.arcgis.com/sharing/generateToken",\
                        params=token_params)
token =  json.loads(tokenResponse.text)['token']


# Make zip file
zf = zipfile.ZipFile(os.path.join(outputFolder, zip), "w")
for shpfile_part in arcpy.ListFiles(filename+"*"):
    zf.write(os.path.join(outputFolder, shpfile_part), shpfile_part,
                                zipfile.ZIP_DEFLATED)
zf.close()

# Start upload of zip file
add_zip_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/addItem".format(username)
zip_params = {'title': "{}_zip".format(filename), "type": "Shapefile",
              'f': 'json', 'token':token}
filesup = {'file':open(os.path.join(outputFolder, zip), 'rb')}
zip_response = requests.post(add_zip_url, params=zip_params, files=filesup)
zipitemid = json.loads(zip_response.text)['id']

# Analyze zip file to get layer info and record count
analyze_url = "http://www.arcgis.com/sharing/rest/content/features/analyze"
analyze_params = {'f':'json', 'itemId': zipitemid,  'file': zip, 'type':'shapefile', 'token':token}
analyze_response = requests.post(analyze_url, params=analyze_params)
response_publishParameters = json.loads(analyze_response.text)['publishParameters']
layerInfo = response_publishParameters['layerInfo']
maxRecordCount = response_publishParameters['maxRecordCount']

# Publish zip file
publish_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/publish".format(username)
publishParameters = '''{'name': 'title'}'''
publish_parameters = {'itemID': zipitemid, 'token': token, 'filetype':'shapefile','f': 'json','publishParameters': publishParameters}
publish_response = requests.post(publish_url, params=publish_parameters)
services = json.loads(publish_response.text)['services']
for item in services:
    OP_serviceurl = item['serviceurl'] + "/0"
    OP_serviceItemId = item['serviceItemId']


# create webmap with zip file service as operational layer
webmap_name = "{} Webmap".format(filename)
webmap_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/addItem".format(username)
text = json.dumps({'operationalLayers':[{'url': OP_serviceurl, 'visibility':'true',"opacity":1, 'title': filename}],"baseMap": {'baseMapLayers':[{'id':"World_Imagery_1068",'opacity':1,'visibility':'true','url':'http://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'}],'title':'Imagery'},'version':'1.9.1'})
webmap_params = {'title': webmap_name, 'type':'Web Map', 'text':text, 'f': 'json','token': token}
webmap_response = requests.post(webmap_url, params=webmap_params)
print json.loads(webmap_response.text)
webmap_id = json.loads(webmap_response.text)['id']

# Share the web map with the organziation
share_webmap_url = "http://www.arcgis.com/sharing/rest/content/users/{0}/items/{1}/share".format(username, webmap_id)
share_webmap_params = {'everyone': 'false', 'org':'true', 'f':'json', 'token':token}
share_webmap_response = requests.post(share_webmap_url, params=share_webmap_params)
print json.loads(share_webmap_response.text)
