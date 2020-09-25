NomF=GetFileName.zip
rm -r "$NomF"
zip "$NomF" __init__.py common_utils.py prefs.py config.py plugin-import-name-getfilename.txt translations/*

if [ "$ZIP_DEST" != "" ]
then
  cp "$NomF" "$ZIP_DEST"
  rm "$NomF"
fi
