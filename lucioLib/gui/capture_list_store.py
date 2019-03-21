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
"""
capture_list_store.py :
    ListStore class for Treeviews capture and monatge.
"""

import pygtk
pygtk.require('2.0')
import gtk


class capture_list_store(gtk.ListStore) :

    def __init__(self,capture_list, images_source, column_type,*args) :
        self._capture_list = capture_list
        super(capture_list_store,self).__init__(column_type,*args)
        for capture in self._capture_list :
            image = images_source.get_image(capture)
            self.append([image.pixbuf_thumb,image.name])

    def swap(self,a,b) :
        # update treeview
        super(capture_list_store,self).swap(a,b)
        # update image list
        a_path = self.get_path(a)[0]
        b_path = self.get_path(b)[0]
        self._capture_list.swap(a_path,b_path)

