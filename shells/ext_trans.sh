PATH=$PATH:/cygdrive/c/Program\ Files\ \(x86\)/Poedit/GettextTools/bin/:/cygdrive/c/Program\ Files\ \(x86\)/Poedit/bin/:/cygdrive/c/Aplicaciones/PoeditPortable/App/Poedit/bin
ls *.py > salida
xgettext -f salida
rm salida
if [ -f messages.po ]
then
	mv messages.po translations/default.po
fi
