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

class Montage_tree(LT.Luciole_tree) :
    
    # redefinition of targets to allow DnD only inside the treeview
    
    # Drag only on treeview 
    targets_source = [ ('tree_model', gtk.TARGET_SAME_WIDGET, 0),
                ]
    
    # Drop from treeview or montage treeview
    targets_dest = [ ('tree_model', gtk.TARGET_SAME_WIDGET, 0),
                ("text/x-luciole-images", gtk.TARGET_SAME_APP, 1),
               ]
                
                        
    def __init__(self, capture_list, images_source, cb_on_treeview_change, cb_on_image_preview):
        super(Montage_tree,self).__init__(capture_list , images_source, cb_on_treeview_change, cb_on_image_preview)
        self.tvcolumn.set_property('title',"  Montage ")
        
        selection = self.get_selection()
        # This signal is used to manage the selection of a row and display image preview 
        selection.connect('changed', self._on_selection_changed)


   
   
    def move_up(self) :
        """ Move up one position a selection in treeview"""
        model, pathlist = self._get_selected_rows()
        if pathlist :
            # Move one position : get the path of the previous row in selection if exist
            path = pathlist[0]
            if path[0] > 0 :
                path = (path[0]-1,)
            else :
                path = None
            # to indicate insetion before
            position = gtk.TREE_VIEW_DROP_BEFORE

            self._move_rows(pathlist,path,position,model)

    def move_down(self) :
        """ Move down one position a selection in treeview"""
        model, pathlist = self._get_selected_rows()
        if pathlist :
            # Move one position : get the path of the last row in selection if exist
            path = pathlist[-1]
            if path[0] < ( len(model) -1 )  :
                path = (path[0]+ 1,)
            else :
                path = None
            # to indicate insetion after
            position = gtk.TREE_VIEW_DROP_AFTER

            self._move_rows(pathlist,path,position,model)
   
    def get_position_selected_row(self):
        """ Get the position/index of a selected row. Only if one image is selected"""
        model, pathlist = self._get_selected_rows()
        l_pos = 0
        if len(pathlist) == 1 :
            # only one row selected
            # return the index
            l_pos = pathlist[0][0]
        return l_pos

    def _on_selection_changed(self,selection) :
        """ selction changed :  display image preview.  only if one image is selected  """
        (model, pathlist) = selection.get_selected_rows()
        if len(pathlist) == 1 :
            path =pathlist[-1]
            self.cb_on_image_preview(self._images_source.get_image(self.model[path][1]))

