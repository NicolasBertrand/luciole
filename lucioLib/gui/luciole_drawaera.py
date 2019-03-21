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
luciole_drawaera.py 

Started on  ven 28 déc 2007 12:57:52 @USER-NAME@
Last update ven 28 déc 2007 12:57:52 @USER-NAME@

@Author Nico 
@version 1
"""

from .. import luciole_tools as LT
from .. import luciole_exceptions as L_EXCEP
import gtk

class PreviewPixbuf(LT.Singleton) :
    """ Class for mamaging the display of image/pixbuf in the Preview window (drawing area)"""

    def f_get_pixbufToDisplay(self) :
        """ getter of pixbufToDisplay""" 
        return  self.__pixbufToDisplay
    def f_set_pixbufToDisplay(self,x):
        """ setter of pixbufToDisplay""" 
        if x :
            self.__pixbufToDisplay=x
            self._PreviewImage(self.__pixbufToDisplay)     
        else :
            # nothing to display
            self.displayDefault()
            self.__pixbufToDisplay = None
    pixbufToDisplay = property(f_get_pixbufToDisplay,f_set_pixbufToDisplay,None,"Pixbuf to display")

    def f_get_isDisplayAllowed(self) :
        """ getter of isDisplayAllowed""" 
        return  self.__isDisplayAllowed
    def f_set_isDisplayAllowed(self,x):
        """ setter of isDisplayAllowed""" 
        self.__isDisplayAllowed=x
        if self.__isDisplayAllowed == True :
            #force image view
            self.on_expose_event(self.__DAwidget,None)

    isDisplayAllowed = property(f_get_isDisplayAllowed,f_set_isDisplayAllowed,"Is display allowed")

    def __init__(self,DAwidget):
        """ init of module PreviewPixbuf"""
        if DAwidget == None :
            # raise exception no drawarea widget given
            raise L_EXCEP.LucioException,"No Drawing area defined"
        else :         
            self.__DAwidget = DAwidget      #drawingArea widget 
            self.__DAwidget.connect("expose-event",self.on_expose_event)
            self.splash = gtk.gdk.pixbuf_new_from_file("images/luciole_default.png")        
        self.__pixbufToDisplay=None
        self.__isDisplayAllowed = True


    ############################################################
    ### PUBLIC METHODS
    ############################################################
  
    def on_expose_event(self,widget,event) :
        """ Called when expose event signal is emitted by the preview drawing area widget.
        Used to refresh the widget with the image to display"""
        if (self.__isDisplayAllowed == True ): 
            if (self.__pixbufToDisplay):
                self._PreviewImage(self.__pixbufToDisplay)
            else :
                self.displayDefault()

    def displayDefault(self) :
        """ When no image/pixbuf need to be displayed, a black background scren is displayed"""
        gc = self.__DAwidget.window.new_gc()
        width = self.__DAwidget.allocation.width
        height = self.__DAwidget.allocation.height
        image = self.splash.scale_simple(width,height,gtk.gdk.INTERP_BILINEAR)
        self.__DAwidget.window.draw_pixbuf(gc,image,0, 0, 0, 0, -1, -1, gtk.gdk.RGB_DITHER_NORMAL, 0, 0)
  
  
    ############################################################
    ### PRIVATE METHODS
    ############################################################
    def _PreviewImage(self,pixbuf):
        """ Display of the pixbuf image in the preview drawing area."""
        if (self.__isDisplayAllowed):  
            if (pixbuf) :
                gc = self.__DAwidget.window.new_gc() 
                width = self.__DAwidget.allocation.width
                height = self.__DAwidget.allocation.height
                image = pixbuf.scale_simple(width,height,gtk.gdk.INTERP_BILINEAR)
                self.__DAwidget.window.draw_pixbuf(gc,image,0, 0, 0, 0, -1, -1, gtk.gdk.RGB_DITHER_NORMAL, 0, 0)
            else :
                self.displayDefault()
 


