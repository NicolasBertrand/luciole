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

import pygtk
pygtk.require("2.0")
import os.path
import time

from lcl_gst import lcl_gst_acq as LGA
import luciole_constants as LCONST
import luciole_exceptions as M_EXCEP


class luciole_acquisition(object) :
    """ Handle the acquisition from digital devices """
 
    ALPHA_DEFAULT = LCONST.ALPHA_DEFAULT
 
    ################################################################################################
    # class properties
    ################################################################################################


    def get_IsOnionSkinActive(self) : return self.__IsOnionSkinActive
    def set_IsOnionSkinActive(self,value) : self.__IsOnionSkinActive = value
    IsOnionSkinActive = property(get_IsOnionSkinActive,set_IsOnionSkinActive,None,"Onion Skin activity " )
    
    def get_Image2Mix(self) : return self.__Image2Mix
    def set_Image2Mix(self,ImagePath) : 
        if ( os.path.isfile(ImagePath)) : 
            self.__Image2Mix = ImagePath
            if ( self.__IsOnionSkinActive) and ( self.GstObj != None ) : 
                self.GstObj.image2Mix =  self.__Image2Mix

    Image2Mix = property(get_Image2Mix,set_Image2Mix,None," Image to mix oin Mixer" )
  
    def get_IsStreamingActive(self) : return self.__IsStreamingActive
    IsStreamingActive = property(get_IsStreamingActive,None,None,"Streaming  activity " )

    def get_HardType(self) : return self.__HardType
    HardType = property(get_HardType,None,None,"Hard type for acquisition " )
  
    def __init__(self,displayWidget,IsOnionSkinActive = False,HardType=LCONST.FAKE, project_dir = None, cb_error = None, cb_capture_done = None ): 
        """ Init of class luciole_acquisition :
            inputs :
          - displayWidget : The gtk.DrawingArea object for display the acquired stream from video
          - IsOnionSkinActive : Is onion skin need to be activated
          - HardType : Type of video to acquire 
          - project_dir : path to the project dir
          - cb_error : callback to indicate gstreamer error
          - cb_capture_done :  callback to indicate is done and a file is available
        """
        self.__HardType = HardType
        self.__project_dir = project_dir

        self._ctrller_on_error = cb_error
        self._cb_capture_done = cb_capture_done


        if self.__HardType != LCONST.DIGICAM :
            # Acquisition is gstreamer based
            self.GstObj = LGA.Lcl_gst_acq(displayWidget,self.__project_dir,self._cb_on_error, self._cb_capture_done)

            self.Image2save = os.path.join(project_dir, LCONST.ACQUIRED_IMAGE_NAME)
            self.__Image2Mix = None     #No image to mix at creation

            #set Gstreamer default properties
            self.GstObj.inputType =  self.__HardType 

            # Is onion skin active ?
            self.__IsOnionSkinActive=IsOnionSkinActive     
            self.GstObj.mix = LGA.Lcl_gst_acq.NOMIX


            self.GstObj.CaptureImagePath = self.Image2save

    
        else :
            # Acquistion is based on image import
            self.__IsOnionSkinActive = False

        self.__IsStreamingActive = False
      
    def start_acquisition(self) : 
        """ start the acquisition on digital device"""

        if self.GstObj.is_playing():
            self.GstObj.stop()         # stop playing
            self.__IsStreamingActive = False
        else:
            #test if onion skin is yet requested
            if (self.__IsOnionSkinActive) and (self.__Image2Mix) :
                #set gstreamer object with onion skin
                self.GstObj.mix = LGA.Lcl_gst_acq.MIX
                self.GstObj.alphaImage = 0.4
                self.GstObj.image2Mix =  self.__Image2Mix
            self.GstObj.reset_pipe()  
            # nbd@grape : test play return failure or not
            self.GstObj.play()         # start playing
            self.__IsStreamingActive = True

    def stop_acquisition(self) :
        """ stop acquisition on video device """
        if self.GstObj.is_playing():
            self.GstObj.stop()         # stop playing
        self.__IsStreamingActive = False
     
    def capture_image(self) :
        """ capture/snapshot of an image from video device """ 
        self.GstObj.capture()
  
    def active_onion_skin(self,Img = None) : 
        """ activation of onion skin"""
        # When onion skin activation is set the image2mix have to be choosen
        # The logic of choice is :
        # first if an image was yet captured ( self.__Image2Mix Not empty)
        # if no image select, checl if an image is given as parameter  
        # if no image as parm image. get an image from stream by forcing a capture
        if ( self.__Image2Mix ) :
            self.GstObj.image2Mix =  self.__Image2Mix
        else :
            if (Img) :
                self.GstObj.image2Mix = Img
            else :
                # force image capture
                self.GstObj.capture()
                #wait acquisition is done i.e. file self.Image2save exists on dir
                # this wait is done for simplification . could be also done with 
                # callback on_capture
                while not os.path.exists(self.Image2save) :
                    time.sleep(0.01)
                self.__Image2Mix = self.Image2save
                if ( self.__Image2Mix ) :
                    self.GstObj.image2Mix =  self.__Image2Mix
              
        self.GstObj.mix = LGA.Lcl_gst_acq.MIX
        self.GstObj.alphaImage = self.ALPHA_DEFAULT
    
        if self.GstObj.is_playing(): self.GstObj.stop()
        self.GstObj.reset_pipe()  # reset pipe to take into account the mix
        self.GstObj.play() 
    
        self.__IsOnionSkinActive=True
    
    def deactive_onion_skin(self) : 
        """ deactivation of onion skin """
        self.GstObj.mix = LGA.Lcl_gst_acq.NOMIX
        self.GstObj.stop()
        self.GstObj.reset_pipe()  # reset pipe to take into account the mix
        self.GstObj.play() 
        self.__IsOnionSkinActive=False
  
    def set_alpha_onion_skin (self,value) : 
        """ Set alpha value on Image"""
        self.GstObj.alphaImage = value
 
    def _cb_on_error(self, code =0, message="") :
        """ Error detected by gstremer during acquisition """
        self.__IsStreamingActive = False
        # controller callbacl for error
        if self._ctrller_on_error : 
            self._ctrller_on_error(message)
        
  
class luciole_acquisition_digicam(luciole_acquisition) :
    """ Heritage of luciole_acquisition class to handle digicam device : Dummy class dor debug purpose only. """
  
    def __init__(self,display):
        """ constructor :
            - display : The gtk.DrawingArea object for display the image acquired from digicam. REMARK Is this needed ??
        """
        luciole_acquisition.__init__(self,display,False,LCONST.DIGICAM,None)
  
class luciole_acquisition_webcam(luciole_acquisition) :
    """ Heritage of luciole acquisition for webcam  usage """

    def __init__(self,displayWidget,IsOnionSkinActive = False,data=None, project_dir = None, cb_error = None, cb_capture_done = None): 
        """ module init as parent + new param (data) """
        luciole_acquisition.__init__( self, displayWidget, HardType = LCONST.WEBCAM ,project_dir = project_dir, cb_error = cb_error , cb_capture_done = cb_capture_done )

        # add webcam data info to gst obj
        self.GstObj.webcam_data = data
        
        

	

	
