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
import logging 
module_logger = logging.getLogger('luciole')


import sys

#
# gst import
# 
import pygst
pygst.require('0.10')
from gst import *
import gst.interfaces


import gobject
import pygtk
pygtk.require('2.0')
import gtk


#
# constants
# 




#
# FUNCTIONS
#


#
# CLASSES
#

class Pipeline(gst.Pipeline) :
    """ Interface class for gst pipeline """

    def __init__(self, *args,**kwargs) :
        super(Pipeline, self).__init__(*args,**kwargs)

class Bin(gst.Bin) :
    """ Interface class for gst Bin  """
    
    def __init__(self, *args,**kwargs) :
        super(Bin, self).__init__(*args,**kwargs)
        self.__gobject_init__()
        self.logger = logging.getLogger('luciole')


class VideoWidget(object):
    """ class usage to be understood """    
    def __init__(self,DrawingArea):
        """ init videwWidget : update Drawingarea widget with gstreamer propoerties """
        self.VideoArea = DrawingArea
        self.VideoArea.imagesink = None
        self.VideoArea.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        """ nbd@grape : with gstreamer is this function useful . Get from player.py example in pygst """
        if self.VideoArea.imagesink:
            self.VideoArea.imagesink.expose()
            return False
        else:
            return True
    
    def set_sink(self, sink):
        assert self.VideoArea.window.xid
        self.VideoArea.imagesink = sink
        self.VideoArea.imagesink.set_xwindow_id(self.VideoArea.window.xid)




class lcl_gstreamer(object) :
    

    def __init__(self,video_widget = None, pipe_name=None, cb_on_error = None, cb_on_eos = None ):
        # init logger
        self.logger = logging.getLogger('luciole')
    
        #
        # link display window widget with gstreamer 
        #
        self.video_widget = video_widget
        if video_widget != None :
             self.video_widget = VideoWidget(video_widget)  

        self.playing = False
        self._cb_on_error = cb_on_error
        self._cb_on_eos = cb_on_eos
        
        self.pipe = Pipeline(pipe_name)
        self.logger.debug(self.pipe)
        
    def connect_bus(self) :
        """ Connect to bus """
        bus = self.pipe.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        bus.connect('sync-message::element', self.on_sync_message)
        bus.connect('message', self.on_message)


    def on_sync_message(self, bus, message) :
        """ Gstreamer sync Message callback. """    
        if message.structure is None:
            return
        if message.structure.get_name() == 'prepare-xwindow-id':
            # Assign the viewport
		    # all this is needed to sync with the X server before giving the
		    # x id to the sink
            if self.video_widget != None :
		        gtk.gdk.threads_enter()
		        gtk.gdk.display_get_default().sync()
                self.video_widget.set_sink(message.src)
                message.src.set_property('force-aspect-ratio', True)
		        gtk.gdk.threads_leave()

    def on_message(self,bus,message) :
        """ Gstreamer message callback"""
        t = message.type
        if t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            error_message = "%s : %s" %(err.copy(),err.message)
            
            self.pipe.set_state(gst.STATE_NULL)
            self.playing = False        # usage tbd
            if self._cb_on_error != None :
                self._cb_on_error(err.code,error_message)
                self.playing = False        # usage tbd
        elif t == gst.MESSAGE_EOS:
            if self._cb_on_eos:
                self._cb_on_eos()
            self.playing = False     # usage tbd
            self.pipe.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_STATE_CHANGED :
            pass

    def pause(self):
        gst.info("pausing pipe")
        self.pipe.set_state(gst.STATE_PAUSED)
        state = self.pipe.get_state(timeout=1000) # wait the state to GST_STATE_CHANGE_NO_PREROLL with a timeout od 1 micro second
        self.playing = False

    def play(self):
        gst.info("playing pipe")
        self.pipe.set_state(gst.STATE_PLAYING)
        self.playing = True
    
    def stop(self):
        self.pipe.set_state(gst.STATE_NULL)
        gst.info("stopped pipe")
        self.playing = False
    
    def get_state(self, timeout=1):
        return self.pipe.get_state(timeout=timeout)

    def is_playing(self):
        return self.playing



if __name__ == '__main__' :
    pipe =  Pipeline('toto')

