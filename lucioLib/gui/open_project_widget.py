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
    widgets who propose open/new project when no project are loaded
"""

import gtk
from gettext import gettext as _

class Gui_open_project_widget(gtk.HButtonBox) :
    """ widget for diplay New/open project buttons """

    # some constants for widget
    _WIDTH_REQUEST =-1
    _HEIGHT_REQUEST = 51        # same value as hbox_acquisition in glade
    _IMAGE_POS = gtk.POS_TOP

    def __init__(self,cb_new,cb_open) :
        super(Gui_open_project_widget,self).__init__()
       
        # ste widget properties
        self.set_name('hbox_open_project')
        self.set_size_request(self._WIDTH_REQUEST, self._HEIGHT_REQUEST)
        self.set_layout(gtk.BUTTONBOX_SPREAD)
        self.set_spacing(25)
        self.set_homogeneous(True)

        # create New button project
        msg = _('Create a new project')
        Button = gtk.Button(msg)
        Button.set_image(gtk.image_new_from_stock(gtk.STOCK_NEW,gtk.ICON_SIZE_BUTTON))
        Button.set_property('image-position',self._IMAGE_POS)
        Button.connect('clicked',cb_new)
        self.pack_start(Button,expand = False, fill = False)
        Button.show()

        # create open button project
        msg = _('Open an existing project')
        Button = gtk.Button(msg)
        Button.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN,gtk.ICON_SIZE_BUTTON))
        Button.set_property('image-position',self._IMAGE_POS)
        Button.connect('clicked',cb_open)
        self.pack_start(Button,expand = False, fill = False)
        Button.show()
        
        # show widget 
        self.show()

