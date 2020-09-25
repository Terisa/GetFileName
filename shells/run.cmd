del "GetFileName.zip"
"c:\Program Files\7-Zip\7z.exe" a "GetFileName.zip" __init__.py common_utils.py prefs.py config.py plugin-import-name-getfilename.txt translations/*
mode 165,999
calibre-debug -s
calibre-customize -a "GetFileName.zip"
REM SET CALIBRE_DEVELOP_FROM=D:\Herramientas\calibre\Codigo\oficial\src
calibre-debug  -g



