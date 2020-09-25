version=`grep version __init__.py | grep -v calibre | sed 's/^.*(//
						  s/).*$//
                                                  s/, */\./g'`
echo $version
NomF="GetFileName_"$version".zip"
zip "versiones/$NomF" __init__.py common_utils.py prefs.py config.py plugin-import-name-getfilename.txt translations/*
git add "versiones/$NomF"
