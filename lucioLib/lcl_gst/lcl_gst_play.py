#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
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
import lcl_gst_base as LG


import fractions

class lcl_gst_play(LG.lcl_gstreamer) :
    """ implementation of image per image video playing with gstreamer .
       Description of pipeline : 
           _______________________________________________________________________________________________________
          |                                                                                                       | 
    -->-- | multifilesrc --> capsfilter(framerate, image ratio) --> decodebin --> ffmpegcolorspace -->xvimagesink |
          |_______________________________________________________________________________________________________|
      """

    _filter_caps_string = "image/jpeg, framerate=(fraction)%s ,width=360,height=288 "
    
    def _get_nbImages(self): return self._nbImages
    def _set_nbImages(self, value):
        if isinstance(value, int) and self.MyImageSrc :
            self._nbImages = value   
            self.MyImageSrc.set_property('num-buffers', self._nbImages)
    nbImages = property(_get_nbImages, _set_nbImages, "Number of image to play")
 
    def _get_framerate(self): return self._framerate
    def _set_framerate(self, value):
        if isinstance(value, str) and self.ImageFilter :
            caps_string = self._filter_caps_string % (fractions.Fraction(value))
            caps = LG.Caps(caps_string)
            self.ImageFilter.set_property("caps", caps)
            self._framerate = value   
    framerate = property(_get_framerate, _set_framerate, "Framerate for displaying image ")

  
    def __init__(self, videowidget, location, framerate="5", nbImages= -1, start_buf=0, on_eos_cb=None) :
        """ init of gstreamer player 
          inputs :
        - videowidget : Drawing area widgert, in gstreamer style for playing video
        - location : where the image are stored 
        - framerate : the video framerate
        - nbImages  : Number of images to play
        - start_buf : index of the first image to play  
        - on_eos_cb : callback for EOS signal
        """
        LG.lcl_gstreamer.__init__(self,video_widget =videowidget, pipe_name = 'Play pipe', cb_on_eos = on_eos_cb  )

        ElementList = []
        
        self._location = location
        self._nbImages = nbImages
        self._framerate = framerate
        self._start_buf = start_buf


        # image load
        self.MyImageSrc = LG.element_factory_make('multifilesrc')
        self.MyImageSrc.set_property('location', self._location)
        self.MyImageSrc.set_property('num-buffers', self._nbImages)
        self.MyImageSrc.set_property('index', self._start_buf)
        ElementList.append(self.MyImageSrc)
    
        # filter
        self.ImageFilter = LG.element_factory_make("capsfilter")
        caps_string = self._filter_caps_string % self._framerate
        caps = LG.gst.Caps(caps_string)
        self.ImageFilter.set_property("caps", caps)
        ElementList.append(self.ImageFilter)
    
        # decodebin
        self.dec = LG.element_factory_make('decodebin')
        # Connect handler for 'new-decoded-pad' signal
        self.dec.connect('new-decoded-pad', self.on_new_decoded_pad)
        ElementList.append(self.dec)
    
        # ffmpegclorspace
        self.Myffmpeg = LG.element_factory_make('ffmpegcolorspace')
        # Reference used in self.on_new_decoded_pad()
        self.vpad = self.Myffmpeg.get_pad('sink')
        ElementList.append(self.Myffmpeg)
    
        # Image sink
        MyImageSink = LG.element_factory_make('xvimagesink')
        ElementList.append(MyImageSink)
        #
        # Add elements to pipeline
        #
        for elem in ElementList : self.pipe.add(elem)
    
        # link all elements
        LG.element_link_many(self.MyImageSrc, self.ImageFilter)
        self.ImageFilter.link(self.dec)
        LG.element_link_many(self.Myffmpeg, MyImageSink)
       
        LG.lcl_gstreamer.connect_bus(self)
     
    def on_new_decoded_pad(self, element, pad, last):
        """ call back to connect decodebin to videopad """
        caps = pad.get_caps()
        name = caps[0].get_name()
        if  name == 'video/x-raw-yuv':
            if not self.vpad.is_linked(): # Only link once
                pad.link(self.vpad)
        
  
    def stop(self):
        """ Stop the video """
        # call upper class stop
        LG.lcl_gstreamer.stop(self)

        self.MyImageSrc.set_property('index', 0)
      
    
 
