#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
#
# Copyright Nicolas Bertrand (nico@inattendu.org), 2009-2011
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
pygtk.require('2.0')
import gtk

import sys

import gobject

import lcl_gst_base as LG

from .. import luciole_constants as MCONST
from .. import luciole_tools as MT
import os.path


class PhotoSaveBin(LG.Bin) :
    """ Bin Pad to save in jpeg format image from stream. Stream alyays encoded but the result will be saved to file only when a capture is done """
    
    # Do jpeg encoding with a framerate of 5 images per second used to reduce cpu
    JPEG_CAPS_FILTER =  " video/x-raw-rgb, framerate=1/1, bpp=24, depth=24"
    #JPEG_CAPS_FILTER =  " video/x-raw-yuv, framerate=5/1"
    
    def __init__(self, _cb_capture_done) :
        """
        Description of pipeline :
        sink pad | videorate --> csp --> capsfilter -->  fakesink |
        Jpeg conversion is done on demand, when a capture is requested,
        on the caalback. Jpeg conversion is done only when necessary
        from a pixbuf.
         
        """

        super(PhotoSaveBin,self).__init__()
        self._cb_capture_done = _cb_capture_done
        self.capture_handler_id = 0
        ImageBinElems=[]
        
        Myvideorate = LG.element_factory_make('videorate','ImageRate')                    #  rate transformation
        ImageBinElems.append(Myvideorate)
        
        #  csp transformation
        csp = LG.element_factory_make('ffmpegcolorspace','ImageCsp')
        ImageBinElems.append(csp)                    
        
        MyJpegFilter = LG.element_factory_make("capsfilter", "JpegFilter")
        # create caps string according, width, height and framerate
        caps = LG.Caps(self.JPEG_CAPS_FILTER)

        self.logger.debug(" Webcam cap : %s"%caps.to_string())
        MyJpegFilter.set_property("caps", caps)
        ImageBinElems.append(MyJpegFilter)

        #MyJpegenc = LG.element_factory_make("jpegenc","MyJpegenc")                 # jpeg encoding
        #ImageBinElems.append(MyJpegenc)   
        
        self.photosink = LG.element_factory_make("fakesink","PhotoSink")
        self.photosink.set_property("signal-handoffs", 'true')
        ImageBinElems.append(self.photosink)   
        
        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(Myvideorate, csp, MyJpegFilter, self.photosink)
        
        self.add_pad(LG.GhostPad('sink', Myvideorate.get_pad('sink')))

    def capture(self, filename =None ) :
        """ capture a frame / data with handoff signals """

        if self.capture_handler_id != 0 :
            self.warning('Skipping capture request. Capture on progress')
            return
               
        self.capture_handler_id = \
                self.photosink.connect('handoff', self.process_data_cb, filename )
        return

    def process_data_cb(self, gbin ,data_buffer, pad, filename ) :
        _bits_per_pixel = 8
                
        _caps = data_buffer.get_caps()
        _structure = _caps[0]
        _width = _structure["width"]
        _height = _structure["height"]
        # generate pixbuf
        self.photosink.disconnect(self.capture_handler_id)
        self.capture_handler_id = 0
        
        # save to file 
        _file = open(filename,'w')
        _file.write(data_buffer)
        _file.close()

        _pixbuf = gtk.gdk.pixbuf_new_from_data(
            data_buffer.copy_on_write(),
            gtk.gdk.COLORSPACE_RGB,
            False,
            _bits_per_pixel,
            _width,
            _height,
            data_buffer.size / _height)
        
              
        # save pixbuf to file
        if filename != None :
            _pixbuf.save(filename, "jpeg", {"quality":"100"})
        
        self.debug('Write Jpeg on %s'%(filename))         
        self._cb_capture_done()    

class InputImageBin(LG.Bin):
    """ Load image to mix with stream"""
    def get_image2Mix(self): return self.__image2Mix
    def set_image2Mix(self, value): 
        if ( os.path.isfile(value) ):
            self.__image2Mix = value
            image2Mix = property(get_image2Mix, set_image2Mix, None, " Path to Image To Mix ")
  
    def get_framerate(self): return self.__framerate
    def set_framerate(self, value): 
        if ( os.path.isfile(value) ):
            self.__framerate = value
    framerate = property(get_framerate, set_framerate, None, " Framerate for displaying input image ")

    def get_alphaValueImage(self): return self.__alphaValueImage
    def set_alphaValueImage(self, value): 
        self.__alphaValueImage = value
        self.MyAlpha.set_property("alpha",self.__alphaValueImage)    
    alphaValueImage = property(get_alphaValueImage, set_alphaValueImage, None, " Framerate for displaying input image ")

    def __init__(self,image,alphaValue,framerate=1) :
        """
        Description of pipeline :
        | multifilesrc --> capsfilter --> jpegdec --> videoscale --> capsfilter --> alpha --> | src pad
        """

        super(InputImageBin,self).__init__()
        self.__image2Mix = image
        self.__framerate =  framerate
        self.__alphaValueImage = alphaValue
        ImageBinElems=[]
    
        # load input image
        self.InputImage= LG.element_factory_make('multifilesrc')
        self.InputImage.set_property('location',self.__image2Mix)
        ImageBinElems.append(self.InputImage)
       

        # filter to set frame rate
        self.ImageFilter = LG.element_factory_make("capsfilter")
        self._filter_caps_string = "image/jpeg, framerate=(fraction)%s/1 ,width=%s,height=%s "
        
        caps_string = self._filter_caps_string%(self.__framerate,MCONST.VIDEO_PAL_RES[0],MCONST.VIDEO_PAL_RES[1])
        caps = LG.Caps(caps_string)
        self.ImageFilter.set_property("caps", caps)
        ImageBinElems.append(self.ImageFilter)
     
        # dec jpeg as stream
        MyJpecdec = LG.element_factory_make('jpegdec')
        ImageBinElems.append(MyJpecdec)
    
        # scale image
        Myvideoscale = LG.element_factory_make('videoscale') 
        ImageBinElems.append(Myvideoscale)
        
        # needed again for setting aspect ratio
        InputImageFilter = LG.element_factory_make('capsfilter',"InputImageFilter")    # set filter on scale
        caps2 = LG.Caps("video/x-raw-yuv, width=%s,height=%s"%(MCONST.VIDEO_PAL_RES[0],MCONST.VIDEO_PAL_RES[1]))
        InputImageFilter.set_property("caps", caps2)
        ImageBinElems.append(InputImageFilter)
    
        self.MyAlpha = LG.element_factory_make("alpha")                             # set alpha of image
        self.MyAlpha.set_property("alpha",self.__alphaValueImage )    
        ImageBinElems.append(self.MyAlpha)
        
        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(self.InputImage,self.ImageFilter, MyJpecdec, Myvideoscale,InputImageFilter, self.MyAlpha)
        
        self.add_pad(LG.GhostPad('src', self.MyAlpha.get_pad('src'))) 



class MixStreamAndImage(LG.Bin) :
    """ Mix the input stream with an image """
    
    def get_image2Mix(self): return self.__image2Mix
    def set_image2Mix(self, value): 
        if ( os.path.isfile(value) ):
            self.__image2Mix = value
            self.ImageBin.image2Mix = self.__image2Mix
    image2Mix = property(get_image2Mix, set_image2Mix, None, " Path to Image To Mix ")

    def get_alphaValueImage(self): return self.__alphaValueImage
    def set_alphaValueImage(self, value):
        self.__alphaValueImage = value
        self.ImageBin.alphaValueImage = self.__alphaValueImage
    alphaValueImage = property(get_alphaValueImage, set_alphaValueImage, None, " alpha value to change. ")

    def __init__(self,alphaValueStream, image, alphaValueImage) :
        """
        Description of pipeline :
        sink pad | --> queue --> videorate --> videoscale --> capsfilter --> videobox --> videoMixer | src pad
        """
        super(MixStreamAndImage,self).__init__()
        
        self.__image2Mix = image
        self.__alphaValueImage=alphaValueImage
        ImageBinElems=[]
        
        queueB2 = LG.element_factory_make("queue","queueB2")                   # queue of branch 2
        ImageBinElems.append(queueB2)
        
        Myvideorate = LG.element_factory_make('videorate')                    #  rate transformation
        ImageBinElems.append(Myvideorate)
        
        Myvideoscale = LG.element_factory_make('videoscale')                   # scale image
        ImageBinElems.append(Myvideoscale)
        
        VideoFilter = LG.element_factory_make("capsfilter")
        caps = LG.Caps("video/x-raw-yuv, framerate=(fraction)10/1, width=720,height=576") # scale image with caps
        VideoFilter.set_property("caps", caps)
        ImageBinElems.append(VideoFilter)
    
        MyVideoBox = LG.element_factory_make('videobox', "MyVideoBox")         # videoBox where input video stream is displayed
        MyVideoBox.set_property('border-alpha', 0)
        MyVideoBox.set_property('alpha', alphaValueStream)
          
        ImageBinElems.append(MyVideoBox)
        
        # Video mixer : mix input in videobox with image
        MyVideomixer = LG.element_factory_make('videomixer', "MyVideomixer")   # video mixer
        ImageBinElems.append(MyVideomixer)
      
        # input image to mix
        # create Bin for input Image
        self.ImageBin = InputImageBin(self.__image2Mix,alphaValueImage);
        ImageBinElems.append(self.ImageBin)
        
        for elem in ImageBinElems : self.add(elem)
        
        #input stream
        LG.element_link_many(queueB2,Myvideorate,Myvideoscale,VideoFilter,MyVideoBox,MyVideomixer)
        # mix with image
        self.ImageBin.link(MyVideomixer)
    
        # this module has a sink pad and a src pad
        self.add_pad(LG.GhostPad('sink', queueB2.get_pad('sink'))) 
        self.add_pad(LG.GhostPad('src', MyVideomixer.get_pad('src')))  




class ScaleBin(LG.Bin) :
    """ This Bin allow to fit a display in fixed size with preserving aspect ratio """
    
    def __init__(self,width=640,height=480) :
        """
        Description of pipeline : 
        sink pad | --> videoscale -->  capsfilter  --> videobox -->  | src pad
        """

        super(ScaleBin,self).__init__()
        ImageBinElems=[]
       
        # compute the image size if neeeded    
        image_size_d = self.calc_video_size(float(width),float(height),MCONST.VIDEO_PAL_RES[0],MCONST.VIDEO_PAL_RES[1])
        
        Myvideoscale = LG.element_factory_make('videoscale')                   # scale image
        ImageBinElems.append(Myvideoscale)
        
        MyVideoFilter = LG.element_factory_make("capsfilter")
        caps = LG.Caps("video/x-raw-yuv,width=%s,height=%s"%(image_size_d['width'],image_size_d['height'])) # scale image with caps
        MyVideoFilter.set_property("caps", caps)
        ImageBinElems.append(MyVideoFilter)
    
        MyVideoBox = LG.element_factory_make('videobox', "MyVideoBox")         # videoBox where input video stream is displayed
        MyVideoBox.set_property('fill',0 )        # fill with black
        # borders are negative values for videobox . postive value used dor crop
        MyVideoBox.set_property('top', -1*image_size_d['top'] )
        MyVideoBox.set_property('bottom', -1*image_size_d['bottom'])
        MyVideoBox.set_property('left', -1*image_size_d['left'])
        MyVideoBox.set_property('right', -1*image_size_d['right'])
        ImageBinElems.append(MyVideoBox)

        # add bins
        for elem in ImageBinElems : self.add(elem)
        
        # link bins
        LG.element_link_many(Myvideoscale,MyVideoFilter,MyVideoBox )
        # this module has a sink pad and a src pad
        self.add_pad(LG.GhostPad('sink', Myvideoscale.get_pad('sink'))) 
        self.add_pad(LG.GhostPad('src', MyVideoBox.get_pad('src'))) 
 
    def calc_video_size(w_src, h_src, w_dst, h_dst):
        """ copmpute the scale for the image : The new image size if needed to scale + border to fill in target destination""" 
        w_scale = (w_src*1.0) / w_dst
        h_scale = (h_src*1.0) / h_dst
        if w_scale >  h_scale :
            scale_f = w_scale
        else  :
            scale_f = h_scale
        if scale_f > 1.0 :
            # Scale to fill in defined zone
            (w_final , h_final) =  (int(w_src/scale_f) , int(h_src/scale_f))
        else :
            # input source lower than target don't scale it
            (w_final , h_final) =  (int(w_src) , int(h_src))

        (border_left, border_right) = ScaleBin.calc_border_size(w_final,w_dst)
        (border_top, border_bottom) = ScaleBin.calc_border_size(h_final,h_dst)
        size_dict = dict()
        size_dict['width'] =  int(w_final)
        size_dict['height'] =  int(h_final)
        size_dict['bottom'] =  int(border_bottom)
        size_dict['top'] =  int(border_top)
        size_dict['left'] =  int(border_left)
        size_dict['right'] =  int(border_right)
        return size_dict 
    calc_video_size = staticmethod(calc_video_size) 

    def calc_border_size(src,tgt) :
        """ This function computes the size of the borders. Images is centered so borders size are equals at one pixel"""
        (border_x, border_y) = (0,0)

        if src < tgt :
            border_size = int( (tgt - src)/2)
            if border_size*2 + src < tgt :
                # to esnsure that border + src = target size
                # means that border size or src are odd; so the first is filled with the missing pixel 
                border_x = int(tgt - src -border_size)
                border_y = border_size
            else :
                (border_x,border_y) = ( border_size, border_size)
    
        return (border_x, border_y)
    calc_border_size = staticmethod(calc_border_size) 


class WebcamInputBin(LG.Bin) :
    """ LG.Bin for Web cam input"""
    def __init__(self,width=640,height=480,framerate=(2,25),source_input='v4l2src',device='/dev/video0') :
        """build webcam cam input bin
        Description of pipeline : 
        | v4lsrc or v4l2src -->  capsfilter --> ffmpegcolorspace --> ScaleBin | src pad
        params :
            width :         The webcam width. Integer value
            height :        The webcam width. Integer value
            framerate :     The webcam framerate. A tuple for fraction representation (denom,num)
            source_input :  The type of driver input. A string
            device :        Path to webcam device. A string 

        """

        super(WebcamInputBin,self).__init__()
        ImageBinElems=[]
          
        MyVideoSrc = LG.element_factory_make(source_input)
        MyVideoSrc.set_property("device", device)
        ImageBinElems.append(MyVideoSrc)
        
        MyVideoSrcFilter = LG.element_factory_make("capsfilter", "MyVideoSrc")
        # create caps string according, width, height and framerate
        caps = LG.Caps("video/x-raw-yuv, width=%s,height=%s , framerate=%s/%s "%(width,height,framerate[0],framerate[1]) )
        self.logger.debug(" Webcam cap : %s"%caps.to_string())
        MyVideoSrcFilter.set_property("caps", caps)
        ImageBinElems.append(MyVideoSrcFilter)
        
        MyyuvInput = LG.element_factory_make('ffmpegcolorspace')
        ImageBinElems.append(MyyuvInput)
        
        # scale Webcam Display to DV SCALE 
        MyScaleBin = ScaleBin(width,height)
        ImageBinElems.append(MyScaleBin)
                
        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(MyVideoSrc,MyVideoSrcFilter,MyyuvInput,MyScaleBin)

        #this bin has only a src ghostPad
        self.add_pad(LG.GhostPad('src', MyScaleBin.get_pad('src'))) 
        
     
      
class DvInputBin(LG.Bin) :
    """ LG.Bin for DV cam input"""
    def __init__(self) :
        """build Dv cam input bin
        Description of pipeline : 
        | dv1394src -->  dvdemux --> dvdec --> ffmpegcolorspace --> | src_pad
         
         """
        super(DvInputBin,self).__init__()
        ImageBinElems=[]
        
        MyVideoSrc = LG.element_factory_make('dv1394src')
        ImageBinElems.append(MyVideoSrc)
        
        #set demuxer ( separation image/sound)
        MyDemux = LG.element_factory_make("dvdemux", "demuxer") 
        ImageBinElems.append(MyDemux)
        MyDemux.connect("pad-added", self.MyDemux_callback)
    
        self.MyVideodecoder = LG.element_factory_make("dvdec", "video-decoder")
        ImageBinElems.append(self.MyVideodecoder)
    
        # ffmpeg needed for pipe ; without the next elements dont understand the stream flow
        MyffmpegInput = LG.element_factory_make('ffmpegcolorspace')
        ImageBinElems.append(MyffmpegInput)
        
        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(MyVideoSrc,MyDemux)
        LG.element_link_many(self.MyVideodecoder,MyffmpegInput)
        
        #this bin has only a src ghostPad
        self.add_pad(LG.GhostPad('src', MyffmpegInput.get_pad('src'))) 

    
    def MyDemux_callback(self, demuxer, pad):
        """ Call back function to create the video pad of dvdemux."""  
        if pad.get_property("template").name_template == "video":
            dec_pad = self.MyVideodecoder.get_pad("sink")
            pad.link(dec_pad)
    
          
class FakeInputBin(LG.Bin) :
    """ LG.Bin for fake input"""
    def __init__(self) :
        """build Fake input bin.
        Description of pipeline : 
        | videotestsrc -->  capsfilter --> | src pad
         
        """
        super(FakeInputBin,self).__init__()

        ImageBinElems=[]
        
        MyVideoSrc = LG.element_factory_make('videotestsrc')
        ImageBinElems.append(MyVideoSrc)
        
        MyVideoSrcFilter = LG.element_factory_make("capsfilter", "MyVideoSrc")
        caps = LG.Caps("video/x-raw-yuv, framerate=(fraction)10/1, width=720,height=576")
        MyVideoSrcFilter.set_property("caps", caps)
        ImageBinElems.append(MyVideoSrcFilter)
        
        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(MyVideoSrc,MyVideoSrcFilter)
        
        #this bin has only a src ghostPad
        self.add_pad(LG.GhostPad('src', MyVideoSrcFilter.get_pad('src'))) 
        

class DisplayBin(LG.Bin) :
    """ 
    Bin used for video display on screen 
      Description of pipeline :

      sink pad | --> ffmpegcolorspace --> videoscale --> autovideosink | 

    """

    def __init__(self) :
        """ Build display bin


        """
        super(DisplayBin,self).__init__()

        ImageBinElems=[]

        Myffmpeg = LG.element_factory_make('ffmpegcolorspace')          # ffmpegcolorspace for display
        ImageBinElems.append(Myffmpeg)
        
        # scale image
        Myvideoscale = LG.element_factory_make('videoscale', 'DisplayVideoScale') 
        ImageBinElems.append(Myvideoscale)
        

        MyImageSink = LG.element_factory_make('autovideosink')
        ImageBinElems.append(MyImageSink)

        for elem in ImageBinElems : self.add(elem)
        
        LG.element_link_many(Myffmpeg,Myvideoscale,MyImageSink)
        
        # only a sink (input) pad
        self.add_pad(LG.GhostPad('sink', Myffmpeg.get_pad('sink')))



class Lcl_gst_acq(LG.lcl_gstreamer) :
    """ Main class for hardware video acquisition with gstreamer"""      
                
    #
    # Class constants declaration
    __HardType=MCONST.HardType
    (NOMIX,MIX) = range(2)
    __MixType=(NOMIX,MIX)
    __ToMixImageName="ToMix.jpeg"
  
 
    #
    # Properties declaration
    #
    def get_inputType(self): return self.__inputType
    def set_inputType(self, value): 
        if value in self.__HardType :
            self.__inputType = value
        else :
            msg = " Invalid Type",value," ",self.__HardType
            self.logger.info(msg)
    def del_inputType(self): del self.__inputType
    inputType = property(get_inputType, set_inputType, del_inputType, " Hard input type ")
  
    def get_mix(self): return self.__mix
    def set_mix(self, value): 
        if value in self.__MixType :
            self.__mix = value
    def del_mix(self): del self.__mix
    mix = property(get_mix, set_mix, del_mix, " Mix type ")

    def get_CaptureImagePath(self): return self.__CaptureImagePath
    def set_CaptureImagePath(self, value): self.__CaptureImagePath = value
    def del_CaptureImagePath(self): del self.__CaptureImagePath
    CaptureImagePath = property(get_CaptureImagePath, set_CaptureImagePath, del_CaptureImagePath, " Path to save file ")

    def get_alphaStream(self): return self.__alphaStream
    def set_alphaStream(self, value): 
        if ( (value >= 0.0) and  (value <= 1.0) ):
            self.__alphaStream = value
    def del_alphaStream(self): del self.__alphaStream
    alphaStream = property(get_alphaStream, set_alphaStream, del_alphaStream, " Stream alpha value ")
  
    def get_alphaImage(self): return self.__alphaImage
    def set_alphaImage(self, value): 
        if ( (value >= 0.0) and  (value <= 1.0)) :
            self.__alphaImage = value
            if self.MixBin : self.MixBin.alphaValueImage = self.__alphaImage
    def del_alphaImage(self): del self.__alphaImage
    alphaImage = property(get_alphaImage, set_alphaImage, del_alphaImage, " Image alpha value ")
  
    def get_image2Mix(self): return self.__image2Mix
    def set_image2Mix(self, value): 
        if ( os.path.isfile(value) ):
            MT.copyf(value,self.__image2Mix)    
            if self.MixBin : self.MixBin.image2Mix = self.__image2Mix
    def del_image2Mix(self): del self.__image2Mix
    image2Mix = property(get_image2Mix, set_image2Mix, del_image2Mix, " Path to Image To Mix ")

    def get_webcam_data(self): return self.__webcam_data
    def set_webcam_data(self, value): self.__webcam_data = value 
    def del_webcam_data(self): del self.__webcam_data
    webcam_data = property(get_webcam_data, set_webcam_data, del_webcam_data, " webcam parameters for gstreamer : source_input,device,height, width ")
  
    def __init__(self,videowidget,baseDirPath="/dev/tmp", on_error = None, cb_capture_done = None) :
        """ Initialisation of class LucioleGstreamer 
            Input parameters :
            - videowidget : the widget into display acquisition
            - baseDirPath : a base path to store the image to mix
            - cb_on_error : callback to inidicate error
            - cb_capture_done : callback to indicate that capture is done.
        """
        
        self.pipe_name = 'Acquistion Pipe'
        
        LG.lcl_gstreamer.__init__(self,video_widget =videowidget, pipe_name = self.pipe_name, cb_on_error = on_error  )

        self.__inputType = MCONST.FAKE
        self.__alphaStream = 1.0
        self.__alphaImage =0.5
        self.__mix  = self.NOMIX
        self.__image2Mix = os.path.join(baseDirPath,self.__ToMixImageName)
        #init videowidget
        #self.DispWidget = videowidget
        self._cb_capture_done = cb_capture_done

        self.playing = False
        self.MixBin=None

        # init webcam data - set default values
        #  standard vga
        self.__webcam_data={}
        self.__webcam_data['width'] = 640
        self.__webcam_data['height'] = 480
        self.__webcam_data['device'] = "/dev/video0"
        self.__webcam_data['source_input'] = "v4l2src"
        self.__webcam_data['framerate_list'] = [ (25,2) ] 
        self.__webcam_data['framerate_selected'] = (25,2) 

    def reset_pipe(self): 
        """ Gstreamer pipe configuration :
        Build the elements according acquisition input, 
        availablity of mixer, and set output to videop display and file.        
        """
        ElementList = []
        self.pipe = LG.Pipeline(self.pipe_name)

        if (self.__inputType == MCONST.WEBCAM) :
            InputBin = WebcamInputBin(
                        width = self.__webcam_data['width'],
                        height = self.__webcam_data['height'],
                        framerate = self.__webcam_data['framerate_selected'],
                        source_input = self.__webcam_data['source_input'],
                        device = self.__webcam_data['device']
                        )
        elif (self.__inputType == MCONST.DVCAM) :
            InputBin = DvInputBin()
        else :
            InputBin = FakeInputBin()
        ElementList.append(InputBin)
   
        #create tee ( One for file sink, the other for video sink)
        MyTee = LG.element_factory_make("tee", "MyTee")
        ElementList.append(MyTee)
    
        # both "branch" of the tee are queued
        
        #    
        # File queue
        #    
        queueFile = LG.element_factory_make("queue","queueFile")              
        ElementList.append(queueFile)
        #fileSink = SaveCapturedImageBin(self.__CaptureImagePath)
        self.fileSink = PhotoSaveBin(self._cb_process_frame)
        ElementList.append(self.fileSink)
        
        #
        # Display queue
        #
        queueDisplay = LG.element_factory_make("queue","queueDisplay")        
        ElementList.append(queueDisplay)
        if (self.__mix == self.MIX) :
            self.MixBin =MixStreamAndImage(self.__alphaStream, self.__image2Mix, self.__alphaImage)
            ElementList.append(self.MixBin)

        DisplaySink =  DisplayBin()
        ElementList.append(DisplaySink)

        #
        # Add elements to pipeline
        #
        for elem in ElementList : self.pipe.add(elem)
        #
        # link pipeline elements
        #
        #link input
        LG.element_link_many(InputBin,MyTee)
        # link  tee File branch 
        LG.element_link_many(MyTee,queueFile, self.fileSink)
        #link tee display Branch
        LG.element_link_many(MyTee,queueDisplay)
        if (self.__mix == self.MIX) :
            LG.element_link_many(queueDisplay,self.MixBin, DisplaySink)
        else :
            LG.element_link_many(queueDisplay,DisplaySink)
    
        self.on_eos = False            # usage tbd 
        
        # connect bus
        LG.lcl_gstreamer.connect_bus(self)

    
    def capture(self) :
        """ capture is requested : 
            capture and JpegConversion are done on PhotoSaveBin
        """

        return self.fileSink.capture(self.__CaptureImagePath)
       
        
    def _cb_process_frame(self):
        """ Callback to inidicate capture and jpeg conversions are done"""
      
       
        if self._cb_capture_done != None :
		    gobject.idle_add(self._cb_capture_done) 
		 

        return True						

