#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

#from __future__ import with_statement
#from __future__ import absolute_import
#from __future__ import print_function
__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib
import json
import traceback

from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre.constants import iswindows, isosx
from calibre.utils.date import UNDEFINED_DATE
from calibre.ptempfile import PersistentTemporaryFile, PersistentTemporaryDirectory

class GetFileName_Prefs():
    def __init__(self, current_library = ""):
        import calibre_plugins.getfilename.config as cfg
        
        PLUGIN_NAME = u"GetFileName"

        JSON_PATH = os.path.join(u"plugins", PLUGIN_NAME.strip().lower().replace(' ', '_') + '.json')
        self.getfilenameprefs = JSONConfig(JSON_PATH)
        
        # print "Prefs: ", self.getfilenameprefs
        
        self.def_lib = {}
        self.def_lib['configured'] = False
        self.def_lib['nom_col'] = ""
        self.def_lib['ext_col'] = ""
        self.def_lib['path_col'] = ""
        self.def_lib['opc_name'] = "file"
        self.def_lib['date_col'] = ""
        self.def_lib[cfg.KEY_SCHEMA_VERSION] = ""
        self.current_library = current_library
        
        self.getfilenameprefs.defaults['nom_col'] = ""
        self.getfilenameprefs.defaults['ext_col'] = ""
        self.getfilenameprefs.defaults['path_col'] = ""
        self.getfilenameprefs.defaults['opc_name'] = "file"
        self.getfilenameprefs.defaults['date_col'] = ""
        self.getfilenameprefs.defaults[cfg.KEY_SCHEMA_VERSION] = ""
        
        self.getfilenameprefs.defaults['configured'] = False
        self.getfilenameprefs.defaults['pref_lib'] = {}
        self.getfilenameprefs.defaults['file_name'] = ""
        
        if 'pref_lib' not in self.getfilenameprefs:
            self.getfilenameprefs['pref_lib'] = {}        

        try:
            del self.getfilenameprefs['procesados']
        except KeyError:
            pass    
        
    def __getitem__(self,kind = None):
        if self.current_library == "":
            from calibre.library import current_library_name
            self.current_library = current_library_name ()
            
        try:
            pref_lib = self.getfilenameprefs['pref_lib'][self.current_library]
        except KeyError:
            for item in self.def_lib:
                self.def_lib[item] = self.getfilenameprefs[item]
            self.getfilenameprefs['pref_lib'][self.current_library] = self.def_lib
            pref_lib = self.def_lib # Aqui leer la primera vez de base de datos
            pref_lib['configured'] = False
                    
        print ("Prefs: ", pref_lib)
        
        if kind is not None:
            try:
                return pref_lib[kind]
            except KeyError:
                return None
        return pref_lib

    def __setitem__ (self, kind, value):
        if self.current_library == "":
            from calibre.library import current_library_name
            self.current_library = current_library_name ()
        
        try:
            self.getfilenameprefs['pref_lib'][self.current_library][kind] = value
        except KeyError:
            self.getfilenameprefs['pref_lib'][self.current_library] = self.def_lib
            self.getfilenameprefs['pref_lib'][self.current_library][kind] = value
            self.getfilenameprefs['pref_lib'][self.current_library]['configured'] = True

    def set(self, kind, value):
        if self.current_library == "":
            from calibre.library import current_library_name
            self.current_library = current_library_name ()
        
        try:
            self.getfilenameprefs['pref_lib'][self.current_library][kind] = value
        except KeyError:
            self.getfilenameprefs['pref_lib'][self.current_library] = self.def_lib
            self.getfilenameprefs['pref_lib'][self.current_library][kind] = value
            self.getfilenameprefs['pref_lib'][self.current_library]['configured'] = True

    def writeprefs(self,value = True):
        if (self.current_library == ""):
            from calibre.library import current_library_name
            self.current_library = current_library_name ()
            
        self.getfilenameprefs['configured'] = value
        
    def getTemporaryFile (self):
        if (self.getfilenameprefs['file_name'] == "") or (not (os.path.exists (self.getfilenameprefs['file_name']))):
            aux = PersistentTemporaryDirectory ("GetFileName")
            self.getfilenameprefs['file_name'] = os.path.join (aux, 'Dict.txt')

        return self.getfilenameprefs['file_name']
