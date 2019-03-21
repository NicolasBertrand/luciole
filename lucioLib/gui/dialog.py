#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vi:si:ai:et:sw=4:sts=4:ts=4
#
# Copyright Nicolas Bertrand (nico@inattendu.org), 2009
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
""" 
Display a dialog window 
"""

import gtk
import os.path

import gettext
_ = gettext.gettext

class Dialog(object):
    """ Dialog display """    
        
    def ErrorMessage(cls,parent = None ,message = None ):
        """ Display an Error message """
        dialog = gtk.MessageDialog(parent = parent,
                                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                    type = gtk.MESSAGE_ERROR,
                                    buttons = gtk.BUTTONS_CLOSE,
                                    message_format = message)
        dialog.show_all()
        result = dialog.run()
        if result == gtk.RESPONSE_CLOSE:
            dialog.destroy()
    ErrorMessage = classmethod(ErrorMessage)
            
    def QuestionMessage(cls,parent = None ,message = None ):
        """ Display a question message. return True if reponse is YES , FALSE if response is NO. None
        if window closed without reponse. """
        dialog = gtk.MessageDialog(parent = parent,
                                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                    type = gtk.MESSAGE_QUESTION,
                                    buttons = gtk.BUTTONS_YES_NO ,
                                    message_format = message)
        dialog.show_all()
        result = dialog.run()
        r_val = None
        if result == gtk.RESPONSE_YES:
            r_val = True
        elif result == gtk.RESPONSE_NO:  
            r_val = False
        dialog.destroy()
        return r_val    
    QuestionMessage = classmethod(QuestionMessage)
    
    def ImportDialog(cls , parent):
        """ Import file chooser dialog"""
        l_filenames = []
        
        dialog = gtk.FileChooserDialog(    title=_('Select files to import'),
                                           parent = parent,
                                           action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                           buttons=( gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                                    gtk.STOCK_OPEN,gtk.RESPONSE_OK)
                                        )
        # default action is OK
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        # allow multiple selection 
        dialog.set_select_multiple(True)
        
        # set $HOME as default folder
        dialog.set_current_folder(os.path.expandvars('$HOME'))
         
        filter = gtk.FileFilter()
        filter.add_mime_type("image/jpeg") 
        filter.set_name("Images ( jpeg  )")
        dialog.add_filter(filter)

        # all files
        filter = gtk.FileFilter()
        filter.add_pattern("*")
        filter.set_name("All files")
        dialog.add_filter(filter)
        
        #  start dialog 
        response=dialog.run() 
       
        if response == gtk.RESPONSE_OK:
            # OK clicked get selected filenames
            l_filenames = dialog.get_filenames()
        # close dialog
        dialog.destroy()
        
        # return filename list
        return l_filenames
    ImportDialog = classmethod(ImportDialog)

    def DirChooserDialog(cls, parent) :
        """ Select a directory """ 
        dialog = gtk.FileChooserDialog(    title=_('Select a Folder'),
                                           parent = parent,
                                           action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                           buttons=( gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                                    gtk.STOCK_OPEN,gtk.RESPONSE_OK)
                                        )

        # default action is OK
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        # set $HOME as default folder
        dialog.set_current_folder(os.path.expandvars('$HOME'))

        #  start dialog 
        response=dialog.run() 
       
        if response == gtk.RESPONSE_OK:
            # OK clicked get selected dir
            l_dir = dialog.get_filename()
        # close dialog
        dialog.destroy()
        
        # return dir
        return l_dir
    DirChooserDialog = classmethod(DirChooserDialog)
    
        
