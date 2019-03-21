#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
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

import lcl_gst_base as LG

class Lcl_gst_sound(LG.lcl_gstreamer) :
	"""  gstreamer  : play a sound  """

	def __init__(self,soundfile,cb_error = None) :
		"""
		soundfile : The soundfile to play
		cb_error : callback arror function
		"""
        LG.lcl_gstreamer.__init__(self,video_widget = None, pipe_name = 'Sound pipe', cb_on_error = cb_error  )
		
        self._soundfile = soundfile
		# 
		# Creation of gstreamer pipeline
		#

		# Create elements
		self.src = LG.element_factory_make('filesrc')
		self.src.set_property('location', self._soundfile)
		
		self.dec = LG.element_factory_make('decodebin')
		# Connect handler for 'new-decoded-pad' signal 
		self.dec.connect('new-decoded-pad', self.on_new_decoded_pad)

		self.conv = LG.element_factory_make('audioconvert')
		self.rsmpl = LG.element_factory_make('audioresample')
		self.sink = LG.element_factory_make('alsasink')

		#
		# Add elements to pipeline
		#
		self.pipe.add(self.src, self.dec, self.conv, self.rsmpl, self.sink)
   
		# Linkelements 
		self.src.link(self.dec)
		LG.element_link_many(self.conv, self.rsmpl, self.sink)
    
		
		# Reference used in self.on_new_decoded_pad()
		self.apad = self.conv.get_pad('sink')
		
		self._on_error = False
   
		# connect bus
        LG.lcl_gstreamer.connect_bus(self)


	def on_new_decoded_pad(self, element, pad, last):
		caps = pad.get_caps()
		name = caps[0].get_name()
		if name == 'audio/x-raw-float' or name == 'audio/x-raw-int':
			if not self.apad.is_linked(): # Only link once
				pad.link(self.apad)
	    
  

