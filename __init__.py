#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function
import six
__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'


# Configuration:
# Check out the plugin's configuration settings by clicking the "Customize plugin"
# button when you have the "GetFileName" plugin highlighted (under Preferences->
# Plugins->File type plugins). Once you have the configuration dialog open, you'll
# see a Help link on the top right-hand side.
#
# Revision history:
#   0.0.1 - Initial release

"""
Store the filename.
"""

PLUGIN_NAME = u"GetFileName"
# Include an html helpfile in the plugin's zipfile with the following name.

import sys, os, re, time, json, ast
import datetime
import zipfile
import traceback
from zipfile import ZipFile
from calibre.constants import DEBUG
from calibre import prints
from calibre.utils.lock import ExclusiveFile

class GetFileNameError(Exception):
    pass

from calibre.customize import FileTypePlugin
from calibre.constants import iswindows, isosx
from calibre.gui2 import is_ok_to_use_qt
from calibre.utils.config import config_dir
from calibre.utils.date import UNDEFINED_DATE

BASE_TIME = None

#columns = [cfg.NAME_COLUMN, cfg.EXT_COLUMN, cfg.PATH_COLUMN, cfg.DATE_COLUMN]

def debug_print(*args):
    global BASE_TIME
    if BASE_TIME is None:
        BASE_TIME = time.time()
    if DEBUG:
        prints('DEBUG: %6.1f'%(time.time()-BASE_TIME), *args)
        
dict_fmt = {'azw3':'azw','mobi':'azw','cbz':'zip','cbr':'rar', 'zip':'htm'}


try:
    debug_print("GetFileName::__init__.py - loading translations")
    load_translations()
except NameError:
    debug_print("GetFileName::__init__.py - exception when loading translations")
    pass # load_translations() added in calibre 1.9


class GetFileName(FileTypePlugin):
    #name                    = PLUGIN_NAME
    name                    = u"GetFileName"
    description             = _('Store the filename of the imported book in a custom column')
    supported_platforms     = ['linux', 'osx', 'windows']
    author                  = u"Anonimo"
    version                 = (0, 2, 0)
    minimum_calibre_version = (2, 79, 0)  # Qt5.
    file_types              = set(['*'])
    on_import               = True
    on_postimport            = True
    on_postprocess            = False
    on_preprocess            = False
    priority                = 1
    
    actual_plugin           = 'calibre_plugins.getfilename.action:GetFileNameAction'
    
    def initialize (self):
        import calibre_plugins.getfilename.prefs as prefs
    
    def run(self, path_to_ebook):        
        '''
        Se llama si on_import tiene el valor TRUE
        '''
        print ("GetFileType::run - ", path_to_ebook)
        import calibre_plugins.getfilename.prefs as prefs

        self.prefs = prefs.GetFileName_Prefs()
        fich = os.path.basename (self.original_path_to_file)
        
        fich_name = self.prefs.getTemporaryFile ()
        print ("GetFileType::run - Fich name: ", fich_name)
        
        with ExclusiveFile(fich_name) as file:
            try:
                print ("GetFileType::run - Have file")
                dictio_aux = json.load(file)
            except Exception as e:
                print ("GetFileType::run - error opening file:", e)
                dictio_aux = {}
            dictio_aux[fich] = self.original_path_to_file
            data = json.dumps (dictio_aux)
            if not isinstance(data, bytes):
                data = data.encode('utf-8')
            file.seek(0)
            file.write(data)
            file.truncate()
            
        print ("GetFileType::run-fich")
        return path_to_ebook
        
    def postimport( self, book_id, book_format, db):
        pass
        
    def postadd (self, book_id, fmt_map, db):
        import calibre_plugins.getfilename.prefs as prefs
        import calibre_plugins.getfilename.config as cfg
        from calibre.library import current_library_name
        current_library = current_library_name ()
        
        '''
        Se llama si on_postimport tiene el valor True
        '''
        
        fich_temp = False
        # debug_print (traceback.format_stack())
        for llamada in traceback.format_stack ():
            if (llamada.find ("add_empty") != -1) or (llamada.find ("copy_to_library") != -1) or (llamada.find ("my_tools") != -1):
                if DEBUG:
                    if (llamada.find ("add_empty") != -1):
                        print(("Libro vacio:", llamada))
                    elif (llamada.find ("copy_to_library") != -1):
                        print(("Copia a biblioteca:", llamada))
                    elif (llamada.find ("my_tools") != -1):
                        print(("Mis herramientas:", llamada))
                    else:
                        print(("Error:", llamada))
                fich_temp = True
                        
        if not (fich_temp):
            config_col = {}
            value_col = {}
            all_cols = db.field_metadata.custom_field_metadata()
            try:
                prefs_value = prefs.GetFileName_Prefs (current_library)
                if (prefs_value['configured'] == False):
                    prefs_value = cfg.get_library_config(db)
            except:
                debug_print ("Error reading config for:")
                for fmt, file in six.iteritems(fmt_map):
                    debug_print ("- ", file)
                return

            for col, val in six.iteritems(cfg.ALL_COLUMNS):
                nom_column = prefs_value[val]
                if (nom_column != '') and not (nom_column in all_cols):
                    nom_column = ''
                
                config_col[col] = {'nom':nom_column, 'empty':''}
                    
                value_col[col] = config_col[col]['empty']
                
            # debug_print (config_col)
                            
            if (config_col[cfg.NAME]['nom'] != ''):    
                get_original_file = False
                if (prefs_value[cfg.OPC_PREF] == 'path'):
                    include_path = True
                    get_original_file = True
                else:
                    include_path = False
                    if (config_col[cfg.DATE]['nom'] != ''):
                        get_original_file = True
                    
                nom_fich = ''
                ext_fich = ''
                path_fich = ''
                date_fich = UNDEFINED_DATE
            
                if (get_original_file):            
                    fich_name = prefs_value.getTemporaryFile ()
                    # print "Name postadd: ", fich_name
            
                    dictio_archi = {}
                    with ExclusiveFile(fich_name) as file:
                        try:
                            dictio = json.load(file)
                        except Exception as e:
                            debug_print ("Skipping invalid temporary file. Excepton: ", e)
                            dictio = {}
                        #debug_print ('Dict buil: ', dictio)
                    
                    #archivos = self.prefs['procesados']
                    # debug_print ("archivos: ", archivos)
            
                for fmt, file in six.iteritems(fmt_map):
                    #
                    # Check original_path_to_file in plugin
                    #

                    list_ext = ['rar','zip']
                    if (get_original_file):
                        debug_print ("File: ", file, " - Format: ", fmt)
                        try:
                            list_ext.append(dict_fmt[fmt])
                        except KeyError:
                            pass
                            
                        nombre_ar = os.path.basename (file)
                        try:
                            path_ori = dictio [nombre_ar]
                        except KeyError:
                            for extFile in list_ext:
                                lis_datos = nombre_ar.split ('.')
                                aux = lis_datos.pop ()
                                lis_datos.append (extFile)
                                nombre_ar = '.'.join (lis_datos)
                                try:
                                    path_ori = dictio [nombre_ar]
                                    break
                                except KeyError:
                                    pass
                            else:
                                path_ori = file
                                    
                        debug_print ("Fich ori: ", path_ori)
        
                    if (include_path):                
                        if (config_col[cfg.PATH]['nom'] != ''):
                            path_fich = os.path.dirname (path_ori)
                            path_fich = os.path.normpath (path_fich)
                            nom_fich = os.path.basename (path_ori)
                            
                            debug_print ("NF: ", nom_fich)

                            value_col[cfg.PATH] = path_fich
                        else:
                            nom_fich = os.path.abspath (path_ori)
                            nom_fich = os.path.normpath (nom_fich)
                            
                        value_col[cfg.NAME] = nom_fich        
                    else:
                        value_col[cfg.NAME] = os.path.basename(file)
                        nom_fich = value_col[cfg.NAME]
                        #path_ori = file
                            
                    if (config_col[cfg.EXT]['nom'] != ''):
                        lis_datos = nom_fich.split ('.')
                        ext_fich = ''
                    
                        if (len (lis_datos) > 1):
                            value_col[cfg.EXT] = lis_datos.pop ()
                            value_col[cfg.NAME] = '.'.join (lis_datos)
                                
                    if (config_col[cfg.DATE]['nom'] != ''):
                        debug_print ("Ori: ", path_ori)
                        #value_col[cfg.DATE] = datetime.datetime.utcfromtimestamp (os.path.getmtime(file))
                        value_col[cfg.DATE] = datetime.datetime.utcfromtimestamp (os.path.getmtime(path_ori))
                    else:
                        value_col[cfg.DATE] = ''
                        
                    debug_print ("File: ", nom_fich)
                    dbA = db.new_api
                    try:
                        for col, column in six.iteritems(config_col):
                            # debug_print ('col: ', col)
                            # debug_print ('column: ', column)
                            # debug_print ('value: ', value_col[col])
                            if ((value_col[col] != column['empty']) and (column['nom'] != '')):
                                val_db = dbA.field_for (column['nom'], book_id, "")
                                #debug_print ('Updating value:', val_db)
                                if (val_db == column['empty']):
                                    debug_print ("Updating column ", column['nom'], "for book id: ", book_id, " with value: ", value_col[col])
                                    numF = dbA.set_field(column['nom'], {book_id:value_col[col]})    
                            
                    except Exception as inst:
                        print((type(inst)))    # the exception instance
                        print((inst.args))     # arguments stored in .args
                        print(inst)
                        print("There was some problem updating metadata")
                        debug_print ("There was some problem updating metadata")
                        debug_print ("* instance: ", type(inst))
                        debug_print ("* args: ", inst.args)
                        debug_print ("* Eception: ", inst)

    def is_customizable(self):
        # return true to allow customization via the Plugin->Preferences.
        return True
        
    def config_widget(self):
        import calibre_plugins.getfilename.config as config
        return config.ConfigWidget()
        
    def save_settings(self, config_widget):
        config_widget.save_settings()
