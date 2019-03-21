#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
#
# Copyright Nicolas Bertrand (nico@inattendu.org), 2010
#
# This file is part of Luciole.
#
#    Luciole is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Luciole is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Luciole.  If not, see <http://www.gnu.org/licenses/>.
#
#



# for i18n
from gettext import gettext as _

import gtk 
import os.path

from ..lcl_export import lcl_export_cinelerra as LEC
from ..lcl_export import lcl_export_pitivi as LEP
from ..lcl_export import lcl_export_kdenlive as LEK

import dialog as G_DIALOG

# TODO : base dir. should be provided by luciole . Not computed here
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = 'templates'
GLADE_DIR = 'ui'

class SimpleBuilderApp(gtk.Builder):
    def __init__(self):
        self.GLADE_DIR = GLADE_DIR 
        gtk.Builder.__init__(self)


class dialog_export_file(SimpleBuilderApp):
    
    EXPORTERS = {
                'cinelerra' : { 
                    'ext' : '.xml',
                    'template' : os.path.join(TEMPLATE_DIR, "cinelerra_template.xml"),
                    'func' :  LEC.lcl_export_cinelerra
                    },
                'pitivi': { 
                    'ext' : '.xptv',
                    'template' : os.path.join(TEMPLATE_DIR,"pitivi_template.xptv"),
                    'func' :   LEP.lcl_export_pitivi
                    },
                'kdenlive' : { 
                    'ext' : '.kdenlive',
                    'template' : os.path.join(TEMPLATE_DIR,"kdenlive_template.kdenlive"),
                    'func' :   LEK.lcl_export_kdenlive
                    },
                'openshot' : {
                    'ext' : '.osp',
                    'template' : os.path.join(TEMPLATE_DIR,"openshot_template"),
                    'func' : None
                    },
                }

    
    def __init__(self, path="export_file.glade", root="dialog_export_file", domain="", form=None, project=None, **kwargs):
        """ init dialog_export_file class : Manage the export tool window 
            path : the path to the glade file to use
            root : main window name
            domain : i18n TBD / Not used
            form : TBD / Not used
            project : luciole project data


        """ 
		
        self.project=project
        
        #
        # initialize window
        #
        SimpleBuilderApp.__init__(self)
        self.add_from_file(os.path.join(self.GLADE_DIR,path))
        self.connect_signals(self)
        self.window = self.get_object(root)
        
        
        # Default Export type
        self.export_type = "cinelerra"

        #
        # widgets configuration
        #
        self._fn_widget = self.get_object("entry_fn")
        self._fn_widget.set_text("export.xml")
        
        initial_folder = os.path.expandvars('$HOME')  
        self._filechooser = self.get_object("filechooserbutton1")
        self._filechooser.set_current_folder(initial_folder)
       
        # Status bar initialization
        self._status_bar_widget = self.get_object("statusbar1")
        self._status_bar_widget_cid = 1
        msg = _("Select an application and a file name for export")
        self._status_bar_widget.push(self._status_bar_widget_cid,msg)
        
        # show window
        self.window.show()

        #
        # SIGNAL methods
        #
    
    def on_dialog_export_file_destroy(self, widget, data=None):
        """ Signal destroy : close window """
        self.window.destroy()

    def on_dialog_export_file_close(self, widget, data=None):
        """ Signal close window : close window """
        self.window.destroy()

    
    def on_filechooserbutton1_file_set(self, widget, data=None):
        """ Signal filechooser : get filename """
        self.export_folder = widget.get_filename()


    def on_radio_cine_toggled(self, widget, data=None):
        """ Signal cinelerra button toggled : set the export type 
            and update filename window """
        self.export_type ="cinelerra"
        self.__update_fn_ext()

    def on_radio_kdenlive_toggled(self, widget, data=None):
        """ Signal kdenlive button toggled : set the export type 
            and update filename window """
        self.export_type ="kdenlive"
        self.__update_fn_ext()

    
    def on_radio_pitivi_toggled(self, widget, data=None):
        """ Signal pitivi button toggled : set the export type 
            and update filename window """
        self.export_type ="pitivi"
        self.__update_fn_ext()

    def on_radio_openshot_toggled(self, widget, data=None):
        """ Signal openshot button toggled : set the export type 
            and update filename window """
        self.export_type ="openshot"
        self.__update_fn_ext()

    def __update_fn_ext(self) :
        """ update filename entry with the correct extension """
        (filename, extension)=os.path.splitext(self._fn_widget.get_text())
        if extension != self.EXPORTERS[self.export_type]['ext'] :
             self._fn_widget.set_text(filename+self.EXPORTERS[self.export_type]['ext'] )
    

    def __make_export(self) :
        """ Render export, according export type, folder, and filename"""
        
        # clear status bar 
        self._status_bar_widget.pop(self._status_bar_widget_cid)
        
        # get filename from entry object
        (self.filename, __extension)=os.path.splitext(self._fn_widget.get_text())

        # get folder
        self.export_folder = self._filechooser.get_filename()

        # correct extension if needed
        if __extension != self.EXPORTERS[self.export_type]['ext'] :
            __extension =  self.EXPORTERS[self.export_type]['ext']
            self._fn_widget.set_text(self.filename+__extension )


        self.full_export_path = os.path.join(self.export_folder,self.filename+__extension)
        
        ForceExport = True     # by default override of export filename is allowed
        
        # display a message to allow overwrite or not
        if  os.path.exists(self.full_export_path):
            # add message display 
            msg =_("File %s already exists. Replace file ?") % self.full_export_path
            ForceExport = G_DIALOG.Dialog.QuestionMessage(self.window,msg)

        
        if ForceExport == True :
            # launch export according retrieved data 
            X = self.EXPORTERS[self.export_type]['func'](
                lcl_project = self.project,
                template= self.EXPORTERS[self.export_type]['template'],
                export_file = self.full_export_path
                )
            X.generate()
        
            msg = _("Export Done")
            self._status_bar_widget.push(self._status_bar_widget_cid,msg)
    
        
    def run(self) :
        """ main function in window, wait for an action of the user"""
        exit_loop = False
        while (exit_loop == False) : 
            response = self.window.run() #wait for a response
            if response == 2 :
                # export button
                self.__make_export()
            else :
                # exit
                exit_loop = True
        
        #exit export window
        self.window.destroy()

