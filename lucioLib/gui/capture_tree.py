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
#
import luciole_tree as LT

import gtk

class Capture_tree(LT.Luciole_tree) :
    # Allow only Drag  On app  
    targets_source = [
                ("text/x-luciole-images", gtk.TARGET_SAME_APP, 1)
                ]
    # Disallow all type of Drop in capture, the image sequence cannot be changed
    targets_dest = []
    

    def __init__(self, capture_list , images_source , cb_on_treeview_change, cb_on_image_preview):
        super(Capture_tree,self).__init__(capture_list , images_source , cb_on_treeview_change, cb_on_image_preview)
        self.tvcolumn.set_property('title',"  Capture ")     
        self.set_name('luciole_capture_tree')
    def images_to_move(self) :
        model, pathlist = self._get_selected_rows()
        images = None
        if pathlist :
            images = [model[path][1] for path in pathlist]
        return images

