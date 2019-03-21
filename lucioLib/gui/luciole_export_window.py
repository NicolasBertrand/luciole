#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
#
# Copyright Nicolas Bertrand (nico@inattendu.org), 2009-2010
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
import gtk
import os.path
import re
# for i18n
from gettext import gettext as _

import dialog as G_DIALOG
from ..lcl_export import lcl_export_video as LEXP

import logging 
module_logger = logging.getLogger('luciole')

class luciole_export_window(object) :
    """ This class manages the window used for video export"""

    ################################################################################ 
    ### PROPERTIES
    ################################################################################ 
  
    def _get_progress_bar_fraction(self): return self._progressbar.get_fraction()
    def _set_progress_bar_fraction(self, fraction): 
        if (fraction >= 0.0) and (fraction <= 1.0) :
            self._progressbar.set_fraction(fraction)
        else :
            # no value in range : just pulse
            self._progressbar.pulse()
    progress_bar_fraction = property(
                _get_progress_bar_fraction, 
                _set_progress_bar_fraction, 
                None , 
            "Progress bar fraction. value in range [0.0 .. 1.0] ")
  
    def _get_progress_bar_text(self): return self._progressbar.get_text()
    def _set_progress_bar_text(self, text): self._progressbar.set_text("%s"%text)
    progress_bar_text = property(
        _get_progress_bar_text, 
        _set_progress_bar_text, 
        None ,
        " Text to display in progress bar")

    def __init__(self,builder,windowname):
        """ Init of module """
        # init logger
        self.logger = logging.getLogger('luciole')
        self._builder=builder
        self._windowname=windowname
      
        self._dialog = self._builder.get_object(self._windowname) 
        self._dialog.connect('delete-event', self._export_close)

        self._combobox =self._builder.get_object("combobox4")
        self._combobox.set_active(0)
        # get filename entry
        self._filename = self._builder.get_object("entry1_filename")
        self._filename.set_text("export") 

        # set initial folder 
        self._filechooser = self._builder.get_object("filechooserbutton1")
        self._filechooser.connect('current-folder-changed', self._current_folder_changed)

        initial_folder = os.path.expandvars('$HOME')  
        self._filechooser.set_current_folder(initial_folder)
        self._entry_folder = self._builder.get_object("entry_folder1")
        self._entry_folder.set_text(initial_folder) 
        #expander for options
        self._expander = self._builder.get_object("expander_options1")
        self._expander.set_label('Options')

        self._export_dir = None     # export dir set up    
  
        self._progressbar =  self._builder.get_object("progressbar1_export")
 
 
    ################################################################################ 
    ### CALLBACKS
    ################################################################################ 
    def _export_close(self,widget,event) :
        """  close action """
        self._dialog.hide()
        self.exit = True
        return True

    def _current_folder_changed(self,widget) :
        """ New directory selected update folder entry."""
        self._entry_folder.set_text(widget.get_filename())
        self._export_dir = widget.get_filename()

        
    ################################################################################ 
    ### PUBLIC METHODS
    ################################################################################ 
  
    def gui_export(self , project_data = None) :
        """ export window handling """
        # a project exists and loaded, the export Window can be opened
        #Update entry folder with _project_dir
        export_dir =  os.path.join( project_data['project_dir'],project_data['export_dir'])
        # Test if export dir has changed i.e . Project has changed --> in that case update 
        # the export dir.
        if (self._export_dir != export_dir) :
            self._entry_folder.set_text(export_dir)
            self._filechooser.set_current_folder(export_dir)
            self._export_dir = export_dir

        # clear progress bar .
        self._progressbar.set_fraction(0.0)
        self._progressbar.set_text('')
        
        # create an export object : Need the poroject tmp dir and widget to interact with 
        expObj = LEXP.lcl_export_video(os.path.join(project_data['project_dir'],project_data['tmp_dir']), self)
        
        # create export_data dictionnary who goes to collect data needed for export tools
        export_data = {}
        
        export_data['fpi'] = project_data['fpi'] #set nb of frame per Image
        export_data['export_dir'] = self._export_dir
        
        # loop on exit for aplly button , when apply is clicked
        # the video export is done but the window is not closed
        # other reponse from gui can be handled
        self.exit = False
        while (self.exit == False) : 
            response = self._dialog.run()  #wait for a response 
            
            if response == gtk.RESPONSE_CANCEL:
                if expObj.export_on_progress == False : 
                    # no export close export window
                    self._dialog.hide()
                    self.exit = True
                else :
                    # export stop export progression
                    expObj.cancel_export()

            elif response == gtk.RESPONSE_APPLY:
                # export is requested : collect info for export

                #
                # get image list from chrono/montage
                #
                
                export_data['image_input']= LEXP.IMAGE_LIST      # export data is type IMAGE_LIST
                
                # Verify that a video name is entered and correct
                l_pattern = re.compile(r'^\w+$') 
                l_video_name = self._filename.get_text()
                if l_pattern.match(l_video_name) :
                    # format is correct 
                    export_data['video_name'] = l_video_name 
                else :
                    msg = _("%s is not valid. Not valid video name. It should be a combination of alphanumeric and '_' characters ")%l_video_name 
                    G_DIALOG.Dialog.ErrorMessage(self._dialog,msg)
                    # by pass loop
                    continue
            
                # creation of image list  In  chrono_images the image names are listed, but the full path is need by export module
                # so each file is concated with abasolute pathname to rush_dir
                export_data['image_list'] = [ os.path.join( project_data['project_dir'], project_data['rush_dir'],image_name) for image_name in project_data['chrono_images'] ]
          
                # get the type of export requested form the combobox
                comboVal = self._combobox.get_active()
                if comboVal == 0 :
                    exportType= LEXP.EXPORT_DV
                elif comboVal == 1 :
                    #export do dvd  
                    exportType= LEXP.EXPORT_DVD
                elif comboVal == 2 :
                    #export do xvid
                    exportType= LEXP.EXPORT_XVID
                else :
                    self.logger.info('unknown video export command')
                    exportType=None
                export_data['export_type'] = exportType
               

                # update export dir
                export_data['export_dir'] =self._export_dir
                # launch Export action

                ForceExport = False     # by default overide of export filename is not allowed
                (ResExport, videopath) = expObj.export(export_data , False)
                if (ResExport == LEXP.ERR_FILE_EXIST) :
                    # Launch Dialog window to ask if export file can be overide
                    msg =_("File %s already exists. Replace file ?") % videopath
                    ForceExport = G_DIALOG.Dialog.QuestionMessage(self._dialog,msg)
                    # if response is True replace file, else do nothing.
                    if ForceExport== True :
                        (ResExport, videopath) = expObj.export(export_data , True)
            
            elif response == gtk.RESPONSE_CLOSE :
                #close export window
                self._dialog.hide()
                self.exit = True
 
    
      


