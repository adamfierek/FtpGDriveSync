from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials
from ftplib import FTP
import configparser
import time
import os.path
import shutil
from os import path

#start time
start_time = time.time()

#Arrays
gdrivelist = []
ftplist = []

#Create config parser and read config file
config = configparser.ConfigParser()
config.read('config.ini')

#Create Google Drive service
credentials = ServiceAccountCredentials.from_json_keyfile_name(config['GDrive']['KEY'], scopes=[config['GDrive']['SCOPE']])
gservice = build('drive', 'v3', credentials=credentials)
print('Created GDrive client')
#Empty trashed items
gservice.files().emptyTrash().execute()
print('Cleaned GDrive trash bin')

#Get ID of root GDrive directory (by name) 
response = gservice.files().list(q="mimeType='application/vnd.google-apps.folder' and name='"+config['GDrive']['ROOTDIR']+"'",
                                     fields='files(id, name)',
                                     pageSize=1).execute()
rootGDrive = response.get('files', [])[0]['id'];

#Get list of files on Google Drive (dir by dir)
def listGDriveFiles(dirId):
    filelist=[]
    page_token = None
    while True:
        response = gservice.files().list(q="'"+dirId+"' in parents",
                                         fields='files(id, name, mimeType)',
                                         spaces='drive',
                                         pageToken=page_token).execute()
        for file in response.get('files', []):
            if file.get('mimeType') == 'application/vnd.google-apps.folder':
                filelist.extend(listGDriveFiles(file.get('id')))
            else:
                filelist.append(file.get('name'))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            return filelist
    
gdrivelist = listGDriveFiles(rootGDrive)
print('Got GDrive file list ('+str(len(gdrivelist))+')')

#Function for search and create GDrive folder 
def getDirectoryID(path):
    rootId = rootGDrive
    names = path.split('/')
    names.remove(config['FTP']['ROOTDIR'])
    for name in names[:-1]:
        file_metadata = {
        'name': [name],
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [rootId]
        }
        response = gservice.files().list(q="mimeType='application/vnd.google-apps.folder' and name='"+name+"' and '"+rootId+"' in parents",
                                         fields='files(id, name)',
                                         pageSize=1).execute()
        files = response.get('files', [])
        if len(files) == 0: 
            file = gservice.files().create(body=file_metadata, fields='id').execute()
            rootId = file.get('id')
        else:
            rootId = files[0].get('id')
    return rootId

#Function for upload file from local path to remote path
def uploadFile(local, remote):
    dirID = getDirectoryID(remote)
    file_metadata = {
    'name': local.split('/')[-1],
    'parents': [dirID]
    }
    media = MediaFileUpload(local, resumable=True)
    try:
        gservice.files().create(body=file_metadata, media_body=media).execute()
    except:
        return False
    return True

#Recursive function for getting FTP file list
def getFTPList(dir):
    filelist = []
    for name, facts in ftp.mlsd(dir):
        if '@' in name or name == '.': 
            continue
        if facts['type'] == 'file' and name not in gdrivelist:
            filelist.append(dir + '/' + name)
        elif facts['type'] == 'dir':
            filelist.extend(getFTPList(dir + '/' + name))
    return filelist

#Open FTP and check files
ftp = FTP(config['FTP']['HOST'])
ftp.encoding = 'utf-8'
ftp.login(config['FTP']['USERNAME'],config['FTP']['PASSWORD'])
ftplist = getFTPList(config['FTP']['ROOTDIR'])
print('Got FTP file list. '+str(len(ftplist))+' to syncrhonze.')

#Download each missing file and upload to Google Drive
counter=0
errors=0
tmpdir='tmp'
if(path.exists(tmpdir)):
    shutil.rmtree(tmpdir)
os.mkdir(tmpdir)
for file in ftplist:
    filename = tmpdir+"/"+file.split("/")[-1]
    print("File: "+filename+" Downloading ", end='')
    ftp.retrbinary("RETR " + file ,open(filename, 'wb').write)
    print("- OK. Uploading ", end = '')
    res = uploadFile(filename, file)
    if res:
        print("- OK")
    else:
        print("- FAIL")
        errors=errors+1
    counter=counter+1

#Close FTP
ftp.close()
time.sleep(20)
shutil.rmtree(tmpdir)
#Print summary
print('END. Synchronized '+str(counter)+' files in '+str(time.time() - start_time)+" s")
print('Errors: '+str(errors))


