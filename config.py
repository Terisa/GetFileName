#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

from __future__ import absolute_import
import six
__license__ = 'GPL v3'

# Standard Python modules.
import os, traceback, json, time, copy

# PyQT4 modules (part of calibre).
try:
    from PyQt5.Qt import (Qt, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                      QAbstractItemView, QIcon, QDialog, QDialogButtonBox, QUrl, QCheckBox, QObject)
except ImportError:
    from PyQt4.Qt import (Qt, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem, QTextEdit,
                      QAbstractItemView, QIcon, QDialog, QDialogButtonBox, QUrl, QCheckBox, QObject)
try:
    from PyQt5 import Qt as QtGui
except ImportError:
    from PyQt4 import QtGui
    
from zipfile import ZipFile

# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files, choose_save_file)
from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre.constants import iswindows, isosx
# modules from this plugin's zipfile.
from calibre import prints

from calibre_plugins.getfilename.common_utils import (KeyboardConfigDialog, PrefsViewerDialog, CustomColumnComboBox)

import calibre_plugins.getfilename.prefs as prefs_a
from calibre.constants import DEBUG

BASE_TIME = None

def debug_print(*args):
    global BASE_TIME 
    
    if BASE_TIME is None:
        BASE_TIME = time.time()
    if DEBUG:
        prints('DEBUG: %6.1f'%(time.time()-BASE_TIME), *args)

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

PREFS_NAMESPACE = 'GetFileNamePlugin'
PREFS_KEY_SETTINGS = 'settings'

NAME_COLUMN = 'customColumnName'
EXT_COLUMN = 'custonColumnExtension'
PATH_COLUMN = 'customColumnPath'
DATE_COLUMN = 'customColumnDate'

NAME = 'name'
EXT = 'extension'
PATH = 'path'
DATE = 'date'
OPC_NAME = 'opc_name'

NAME_PREF = 'nom_col'
EXT_PREF = 'ext_col'
PATH_PREF = 'path_col'
DATE_PREF = 'date_col'
OPC_PREF = 'opc_name'

KEY_SCHEMA_VERSION = 'SchemaVersion'
DEFAULT_SCHEMA_VERSION = '0.3'

ALL_COLUMNS = {
  NAME: NAME_PREF,
  EXT : EXT_PREF,
  PATH: PATH_PREF,
  DATE: DATE_PREF
}

DEFAULT_LIBRARY_VALUES = {
    NAME_COLUMN: '',
    EXT_COLUMN: '',
    PATH_COLUMN: '',
    DATE_COLUMN: '',
    OPC_NAME: '',
    KEY_SCHEMA_VERSION: ''
}

DEFAULT_MIGRATION = {
    NAME_COLUMN: 'nom_col',
    EXT_COLUMN: 'ext_col',
    PATH_COLUMN: 'path_col',
    DATE_COLUMN: 'date_col',
    OPC_NAME: 'opc_name'
}

def migrate (db, aux_prefs):
    library_config = None
    
    library_config = db.prefs.get_namespaced(PREFS_NAMESPACE, PREFS_KEY_SETTINGS,
                copy.deepcopy(DEFAULT_LIBRARY_VALUES))
                
    for key, col in six.iteritems(DEFAULT_MIGRATION):
        debug_print ('col: ', col)
        aux_prefs.set (col, library_config[key])
        
    aux_prefs.set (KEY_SCHEMA_VERSION, DEFAULT_SCHEMA_VERSION)

def get_library_config(db):
    from calibre.library import current_library_name
    
    prefs = prefs_a.GetFileName_Prefs (current_library_name ())
    
    try:
        schema = prefs[KEY_SCHEMA_VERSION]
    except KeyError:
        schema = ""
        
    if (schema != DEFAULT_SCHEMA_VERSION):
        migrate (db, prefs)
        prefs.set ('configured', True)
                
        prefs.writeprefs ()

    return prefs

def set_library_config(db, library_config):
    # db.prefs.set_namespaced(PREFS_NAMESPACE, PREFS_KEY_SETTINGS, library_config)
    
    prefs_aux = prefs_a.GetFileName_Prefs()

    
class ConfigWidget(QWidget):
    def __init__(self):
        from calibre.library import current_library_name
    
        QWidget.__init__(self)

        actual_plugin = 'calibre_plugins.getfilename.action:GetFileNameAction'
        self.plugin_action = actual_plugin

        # get the prefs
        self.prefs = prefs_a.GetFileName_Prefs(current_library_name ())
        if (self.prefs['configured'] == False):
            try:
                from calibre.gui2.ui import get_gui
                db = get_gui().current_db
                self.prefs = get_library_config (db)
            except:
                try:
                    from calibre.library import db

                    self.prefs = get_library_config(db())
                except:
                    self.prefs = prefs_a.GetFileName_Prefs (current_library_name ())    
                    for key, col in six.iteritems(DEFAULT_MIGRATION):
                        self.prefs.set (col, DEFAULT_LIBRARY_VALUES[key])
                    self.prefs.set ('OPC_PREF', 'name')

                    self.prefs.set ('configured', True)
                    self.prefs.set (KEY_SCHEMA_VERSION, DEFAULT_SCHEMA_VERSION)

                    self.prefs.writeprefs ()
                    
        self.filename_col = self.prefs[NAME_PREF]
        self.extension_col = self.prefs[EXT_PREF]
        self.path_col = self.prefs[PATH_PREF]
        self.date_col = self.prefs[DATE_PREF]
        self.option_name = self.prefs[OPC_PREF]

        # Start Qt Gui dialog layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        # -- Options -- #
        
        
        # --- File ---
        
        avail_columns_text = self.get_custom_columns_text()
        avail_columns_date = self.get_custom_columns_date()
            
        filename_group_box = QGroupBox(_('File name options:'), self)
        layout.addWidget(filename_group_box)
        filename_group_box_layout = QGridLayout()
        filename_group_box.setLayout(filename_group_box_layout)
        
        pos = 0

        self.path_checkbox = QCheckBox(_("Include folder"), self)
        self.path_checkbox.setTristate (False)
        self.path_checkbox.setToolTip(_("It indicates it stores the folder with the filename."))
        self.path_checkbox.stateChanged.connect(self.path_checkbox_clicked)
        filename_group_box_layout.addWidget(self.path_checkbox, pos, 0, 1, 1)
        
        pos = pos + 1

        fname_column_label = QLabel(_('&File name:'), self)
        fname_column_label.setToolTip(_('Custom text column for storing the filename and folder if included'))
        fname_col = self.filename_col
        self.fname_column_combo = CustomColumnComboBox(self, avail_columns_text, fname_col)
        fname_column_label.setBuddy(self.fname_column_combo)
        filename_group_box_layout.addWidget(fname_column_label, pos, 0, 1, 1)
        filename_group_box_layout.addWidget(self.fname_column_combo, pos, 1, 1, 2)
        self.fname_column_combo.currentIndexChanged.connect (self.filename_changed)
        
        pos = pos + 1

        fexten_column_label = QLabel(_('File &Extension:'), self)
        fexten_column_label.setToolTip(_('Custom text column for storing the extension (if empty the filename is not splited). Not used if file name column is empty'))
        fexten_col = self.extension_col
        self.fexten_column_combo = CustomColumnComboBox(self, avail_columns_text, fexten_col)
        fexten_column_label.setBuddy(self.fexten_column_combo)
        filename_group_box_layout.addWidget(fexten_column_label, pos, 0, 1, 1)
        filename_group_box_layout.addWidget(self.fexten_column_combo, pos, 1, 1, 2)
        if (self.filename_col == ""):
            self.fexten_column_combo.setEnabled (False)
        else:
            self.fexten_column_combo.setEnabled (True)
            
        pos = pos + 1
                    
        fpath_column_label = QLabel(_('File &Folder:'), self)
        fpath_column_label.setToolTip(_('Custom text column for storing the folder (if empty the filename is not splited). Not used if file name column is empty'))
        fpath_col = self.path_col
        self.fpath_column_combo = CustomColumnComboBox(self, avail_columns_text, fpath_col)
        fpath_column_label.setBuddy(self.fpath_column_combo)
        filename_group_box_layout.addWidget(fpath_column_label, pos, 0, 1, 1)
        filename_group_box_layout.addWidget(self.fpath_column_combo, pos, 1, 1, 2)

        date_column_group = QGroupBox(self)
        layout.addWidget(date_column_group)
        date_layout = QGridLayout()
        date_column_group.setLayout(date_layout)

        fdate_column_label = QLabel(_('File &Date:'), self)
        fdate_column_label.setToolTip(_('Custom date column for storing the last modified date (if empty the date is not stored)'))
        fdate_col = self.date_col
        self.fdate_column_combo = CustomColumnComboBox(self, avail_columns_date, fdate_col)
        fdate_column_label.setBuddy(self.fdate_column_combo)

        date_layout.addWidget(fdate_column_label, 2, 0, 1, 1)
        date_layout.addWidget(self.fdate_column_combo, 2, 1, 1, 2)
        
        if (self.option_name == 'path'):
            self.path_checkbox.setChecked (True)
            if (self.fname_column_combo.currentIndex () == 0):
                self.fpath_column_combo.setEnabled (False)            
            else:
                self.fpath_column_combo.setEnabled (True)
        else:
            self.path_checkbox.setChecked (False)
            self.fpath_column_combo.setEnabled (False)

        layout.addStretch(1)
        

    def save_settings(self):        
        self.prefs.set (NAME_PREF, self.fname_column_combo.get_selected_column())
        self.prefs.set (EXT_PREF, self.fexten_column_combo.get_selected_column())
        self.prefs.set (PATH_PREF, self.fpath_column_combo.get_selected_column())
        self.prefs.set (DATE_PREF, self.fdate_column_combo.get_selected_column())
        
        if (self.path_checkbox.isChecked ()):
            self.prefs.set (OPC_PREF, 'path')
        else:
            self.prefs.set (OPC_PREF, 'name')
            
        self.prefs.writeprefs()

    def get_custom_columns_text(self):
        try:
            from calibre.gui2.ui import get_gui
            db = get_gui().current_db
        except:
            return None
        
        column_types = ['text','enumeration','custom','comments']
        custom_fields = set (db.custom_field_keys())
        available_columns = {}
        
        for field in list (custom_fields):
            column = db.field_metadata[field]
            typ = column['datatype']
            if typ in column_types:
                available_columns[field] = column
                
        return available_columns
        
    def get_custom_columns_date(self):
        try:
            from calibre.gui2.ui import get_gui
            db = get_gui().current_db
        except:
            return None
        
        column_types = ['date','datetime']
        custom_fields = set (db.custom_field_keys())
        available_columns = {}
        
        for field in list (custom_fields):
            column = db.field_metadata[field]
            typ = column['datatype']
            if typ in column_types:
                available_columns[field] = column
                
        return available_columns
        
    def file_radiobutton_clicked (self):
        self.fpath_column_combo.setEnabled (False)
        
    def path_radiobutton_clicked (self):
        if (self.fname_column_combo.get_selected_column() == ""):
            self.fpath_column_combo.setEnabled (True)
        
    def path_checkbox_clicked (self):
        if self.path_checkbox.isChecked ():
            if (self.fname_column_combo.currentIndex() != 0):
                self.fpath_column_combo.setEnabled (True)
            self.option_name = 'path'
            debug_print ("Checkbox activado: ", self.fname_column_combo.currentIndex())
        else:
            self.fpath_column_combo.setEnabled (False)
            self.option_name = 'name'
            debug_print ("Checkbox desactivado")
        
    def filename_changed (self):
        if (self.fname_column_combo.currentIndex() == 0):
            self.fexten_column_combo.setEnabled (False)
            self.fpath_column_combo.setEnabled (False)
            debug_print ("Vaciado nombre")
        else:
            self.fexten_column_combo.setEnabled (True)
            if (self.option_name == 'path'):
                self.fpath_column_combo.setEnabled (True)
            debug_print ("Completado nombre: ", self.option_name)
