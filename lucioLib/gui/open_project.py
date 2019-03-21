#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vi:si:ai:et:sw=4:sts=4:ts=4
#
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
open_project.py :
   Open project window
"""
import gtk
import os.path

class Open_file(object) :
    """ class to manage open file action """
    
    def __init__(self) :
        pass
    
    def open(cls) :
        """ Class method for opening a file """

        filename = None

        # create a filechooser Dialog window
        dialog = gtk.FileChooserDialog(title='Select a luciole file',
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=( gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                                    gtk.STOCK_OPEN,gtk.RESPONSE_OK)
                                        )
        # defulat action is OK
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        # set $HOME as default folder
        dialog.set_current_folder(os.path.expandvars('$HOME'))

        # set a filter on xml files 
        filter = gtk.FileFilter()
        filter.set_name("Luciole files (*.xml)")
        filter.add_mime_type("xml/luciole")
        filter.add_pattern("*.xml")
        dialog.add_filter(filter)
        
        # launch wait for reponse
        response = dialog.run()

        # check response
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
        
        dialog.destroy()

        return filename 
    
    open = classmethod(open)







