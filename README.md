# FtpGDriveSync
   Python script for copying files from FTP to Google Drive using Google service account and Google API v3

## config.ini
    [FTP] 
  
    USERNAME: xxx
  
    PASSWORD: xxx
  
    HOST: ftp.xxx
  
    ROOTDIR: ABC
  
    [GDrive]
  
    SCOPE: https://www.googleapis.com/auth/drive
  
    KEY: credentials.json
  
    ROOTDIR: XYZ
  
## credentials.json
   Google service account API key. [Documentation](https://cloud.google.com/iam/docs/service-accounts)
 
## TO DO:
* Exception handling
* More accurate GDrive file listing (dir by dir)
* Code refactoring
* Handle files bigger than 50M (API limitation)
