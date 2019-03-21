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
dialog_preferences.py
"""
import gtk
import pango
import copy

from .. import luciole_constants as LCONST

class Luciole_preferences(object) :
    _Dialog_name = 'Dialog_preferences'
    _Label_preferences = 'label_preferences'
    _Viewport_title = 'viewport3'
    _Checkbox_trash = 'checkbutton_trash'
    _Combobox_theme = 'combobox_theme'
   
    _Combo_Table = ['Default.rc','Tropical.rc']

    def __init__(self,builder) :
        """ 
        
        """
        self.conf_options = None
        self.cb_on_apply = None 
        self.builder = builder
        self.wdg_dict = dict() 
        self.dialog = self.builder.get_object(self._Dialog_name)
        #self.dialog.add_parent(parent)
        self.dialog.add_buttons( gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_CLOSE,gtk.RESPONSE_CLOSE,
                                            gtk.STOCK_APPLY,gtk.RESPONSE_APPLY)


        self.dialog.connect("delete-event", self._cb_on_exit)

    def _update_widgets(self) :
        
        # set title in bold
        self.title = self.builder.get_object(self._Label_preferences)
        attrs = pango.AttrList()
        attrs.insert( pango.AttrWeight(pango.WEIGHT_BOLD,0, -1))
        self.title.set_attributes(attrs)
        
        # Change Title background colour
        viewport = self.builder.get_object(self._Viewport_title)
        map = viewport.get_colormap()
        colour = map.alloc_color("#9DDDC8") # firefly grey
        style = viewport.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = colour
        viewport.set_style(style)

        # Theme Combo box 
        combo = self.builder.get_object(self._Combobox_theme)
        combo.set_active(self._Combo_Table.index(self.conf_options['Theme']))     # Tropical Theme active by default 
        self.wdg_dict['Theme'] = combo

        # Trash Check Box 
        checkBox = self.builder.get_object(self._Checkbox_trash)
        if ( self.conf_options['CaptureTrashDisplay'] == 'yes' ) :
            checkBox.set_active(True)
        else :
            checkBox.set_active(False)

        self.wdg_dict['CaptureTrashDisplay'] = checkBox
        

    def run(self,conf_options,cb_on_apply ) :
        """ run dialog : Dialog defined in glade so __init__ makes glade stuff init; so called once. 
            run function cnd called multiple, and so param conf_options and cb_on_apply is given in run function insteaf of __init__"""
        self.conf_options = conf_options 
        self.cb_on_apply = cb_on_apply

        self._update_widgets()
        
        self.dialog.show_all()
        self._exit = False
        while (self._exit == False) : 
            # run dialog
            result = self.dialog.run()
            # wait for reponse
            if result == gtk.RESPONSE_CANCEL :
                self.dialog.hide()
                self._exit = True
            elif result == gtk.RESPONSE_CLOSE :
                self.dialog.hide()
                self._exit = True

            elif result == gtk.RESPONSE_APPLY :
                # parse configurations widgets
                self.modif_options = copy.copy(self.conf_options)
                for (key,wdg) in self.wdg_dict.iteritems() :
                    # parse each option and udpate modified 
                    if key == 'CaptureTrashDisplay' : 
                        if wdg.get_active() == True :
                            self.modif_options['CaptureTrashDisplay'] = 'yes'
                        else :
                            self.modif_options['CaptureTrashDisplay'] = 'no'
                    if key == 'Theme' :
                        if wdg.get_active() != -1 :
                            self.modif_options['Theme'] = self._Combo_Table[wdg.get_active()]
                #callback call
                if self.cb_on_apply != None :  self.cb_on_apply(self.modif_options)

    def _cb_on_exit(self,widget,event) :
        self.dialog.hide()
        self._exit = True
        return True

   

