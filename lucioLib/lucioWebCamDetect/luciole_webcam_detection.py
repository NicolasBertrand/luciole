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
"""
luciole_webcam_detection 
Interface function for webcam detection.
Retro compatibilty of luciole 0.9 in 0.8 branch.
Main reason : remove usage of hal
"""
import gobject
import gst


import logging 
module_logger = logging.getLogger('luciole')

#from lucioLib.luciole_exceptions import luciole_exceptions as LEXCEP

from .. import luciole_exceptions as LEXCEP
#import luciole_exceptions as LEXCEP


from webcam_detection import WebcamDetection

class luciole_webcam_detection(WebcamDetection) :

    def __init__(self) :
        WebcamDetection.__init__(self)

    def detect_webcam(self):
        """ interface function for webcam detection """
        # udev detetction
        _nb_webcams = WebcamDetection.detect_webcams(self)
        
        if _nb_webcams != 0 :
             # detect properties with gstreamer
            self.gst_props =  webcam_gstreamer_properties(self.webcam_devices)
            _nb_webcams = self.gst_props.gst_detection()

        return _nb_webcams
    
    def get_gst_best_input(self, webcam_device_index=0) :
        """ interface function to select best input """
        return self.gst_props.get_gst_best_input(webcam_device_index)
        #_device = self.webcam_devices[webcam_device_index]
        #print "device ", _device
        #_prop_name ='definition'
        
        
        #WebcamDetection.get_best_value(self, _prop_name, "")


class webcam_gstreamer_properties(object) :
    
    def __init__(self, devices) :
        self._webcam_devices = devices
        # laucnch gst detection

    

    def gst_detection(self) :
        """ performs webcam type detection with gstreamer :
            _ detects what source yo use ( v4lsrc or v4l2src)
            _ resolution 
            _ video mime types
        """ 
        nb_device_detected = 0
        for webcam_device in self._webcam_devices :
            # for each detected device get the data (source type, mimetype, resolution) 
            (status, webcam_device_data) = self.__get_gst_webcam_data(webcam_device["device-file"], webcam_device["v4ldriver"])
            if status[0] == gst.STATE_CHANGE_SUCCESS and webcam_device_data != None :  
                # detection is success
                webcam_device["webcam_data"] = webcam_device_data
                nb_device_detected = nb_device_detected +1
            else :
                # gstreamer test unsuccesfull : test with other driver
                if webcam_device["v4ldriver"] == 'v4lsrc' :
                    webcam_device["v4ldriver"] = 'v4l2src'
                else :
                    webcam_device["v4ldriver"] ='v4lsrc'
                (status, webcam_device_data) = self.__get_gst_webcam_data(webcam_device["device-file"], webcam_device["v4ldriver"])
                if status[0] == gst.STATE_CHANGE_SUCCESS and webcam_device_data != None :  
                    # detection is success
                    webcam_device["webcam_data"] = webcam_device_data
                    nb_device_detected = nb_device_detected +1
                else :
                    #Nothing detected . Reset webcam device
                    webcam_device=dict()
        return nb_device_detected


    def get_gst_best_input(self, webcam_device_index=0) :
        """ for selected webcam device returns the gst.Bin with  
        the best video quality .
        Criteria are :
            1) first select mimetype in the following order :    
                1) video/x-raw-yuv
                2) video/x-raw-rgb
                3) image/jpeg
            2) get the greatest resolution according video mimetype
                'width'     
                'height'
                'source_input'      -> v4lsrc or v4l2src
                'device '           -> device path ex. : /dev/video0
        The method returns a dict with the following keys :
            
        """
        video_formats = self._webcam_devices[webcam_device_index]['webcam_data']['video_formats']         
        mimetypes = ('video/x-raw-yuv','video/x-raw-rgb','image/jpeg')
        (width,height)=(None,None)
        for mimetype in mimetypes :

            if video_formats.has_key(mimetype) :
                # the resolution format are sorted by resolution  
                # the higher resolution is first in list
                
                #width = video_formats[mimetype][0]['width']
                #height = video_formats[mimetype][0]['height']
                #framerate =  video_formats[mimetype][0]['framerate']
                width, height, framerate = self._get_best_definition(video_formats[mimetype])
                
                # leave loop when mimetype is found
                break
        webcam_bin_data = dict()
        if width != None :
            # a format was detected : prepare pipeline info
            webcam_bin_data['width'] = width 
            webcam_bin_data['height'] = height
            webcam_bin_data['framerate_list'] = framerate
            webcam_bin_data['framerate_selected'] = framerate[len(framerate)/2]
            webcam_bin_data['source_input'] = self._webcam_devices[webcam_device_index]['v4ldriver']
            webcam_bin_data['device'] = self._webcam_devices[webcam_device_index]['device-file'] 
            webcam_bin_data['name'] = self._webcam_devices[webcam_device_index]['name']

        return  webcam_bin_data

 
    def _get_best_definition(self, mimetype_data) :
        """ Loop on width height return valu with greatest size ( Widthxheight)"""
        _width = 0
        _height = 0
        _MAX = _width * _height
        _framerate = 0
        for _data in mimetype_data :
            _new_max = _data['width'] * _data['height']
            if _new_max > _MAX :
                _MAX = _new_max
                _width = _data['width']
                _height = _data['height']
                _framerate =  _data['framerate']
        return _width, _height, _framerate




    def __get_gst_webcam_data(device_name,driver) :
        """ get data from the webcam test compatible sources
            input device_name is the file path ( ex. /dev/video0)
        """
        # creation of a fake gstreamer to test webcam with v4lsrc ot v4l2src
        webcam_device=dict()
        
        pipeline_desc = "%s name=source device =%s ! fakesink" %(driver, device_name)
        pipeline = gst.parse_launch(pipeline_desc)
            
        #Start pipeline and check for state 
        pipeline.set_state(gst.STATE_PLAYING)
        ret = pipeline.get_state(timeout=10000*gst.MSECOND)
            
        if ret[0] == gst.STATE_CHANGE_SUCCESS :
            # webcam is detected succefully
            pipeline.set_state(gst.STATE_PAUSED)
                
            # get source element name and webcam name 
            src = pipeline.get_by_name('source')
            name = src.get_property('device-name')
                
                
            # start detection of source video formats
            # video formats are accesible in the capabilities
            # of the source "src" pad 
            pad = src.get_pad("src")
            caps = pad.get_caps()
            webcam_gstreamer_properties.gst_get_supported_video_formats(webcam_device,caps)
            # stop playing with webcam
            pipeline.set_state(gst.STATE_NULL)
        return (ret,webcam_device)
    __get_gst_webcam_data = staticmethod(__get_gst_webcam_data)

    def __gst_get_supported_video_formats(webcam_device, caps) :
        """ get video mimetypes and resolution 
            Format example  
            webcam_device ["mimetypes"]      ==> ["video/x-raw-yuv"]     ==> ( 
                                                                            (["width"] = 320 , ["height"] = 240) 
                                                                            (["width"] = 640 , ["height"] = 480) 
                                                                            )
                                             ==> ["video/x-raw-rgb"]     ==> ( 
                                                                            (["width"] = 640 , ["height"] = 480) 
                                                                            )
        
        The input structures  are identified by the mime type and have the width and height as field
        some other fields as bpp , depth or framerate are also available but not used here.
        """
        num_structures = caps.get_size()
        webcam_device["video_formats"] = dict()
        for i in range(num_structures) :
            # loop on each strutcures
            structure = caps[i]
            if (    structure.has_name("video/x-raw-yuv") 
                or  structure.has_name("video/x-raw-rgb")  
                or  structure.has_name("image/jpeg")
                ) :
                # get resolution list or create it
                if not webcam_device["video_formats"].has_key(structure.get_name()):
                    webcam_device["video_formats"][structure.get_name()] = list()
                resolution_list = webcam_device["video_formats"][structure.get_name()]
                #print " resolution_list at the begin : \n %s"%webcam_device["video_formats"]
                
                # take in acount only structure wih fields width and height
                if (structure.has_field("width") and  structure.has_field("height")) :
                    #print "  %s : %s x %s"%(structure.get_name(),structure["width"],structure["height"] )
                    resolution=dict()
                    # check if result is in GST_TYPE_INT_RANGE format
                    if (isinstance(structure["width"], gst.IntRange)):
                        # when type is range --> some resolution points are created in the range
                        # value are *2 from min to max
                        width_cur =  structure["width"].low
                        height_cur =  structure["height"].low
                        while ( ( width_cur   <=  structure["width"].high ) and
                              ( height_cur  <=  structure["height"].high ) 
                            ):
                            
                            ( resolution["width"] , resolution["height"] ) = (width_cur,height_cur)  
                            #store framerate 
                            resolution["framerate"] = None
                            if structure.has_field("framerate") :
                                resolution["framerate"] = structure["framerate"]
                            # Append resolution dict to list
                            if not resolution  in resolution_list :
                                resolution_list.append(resolution)
                            (width_cur,height_cur) = (width_cur*2,height_cur*2)
                    
                    # check if result is in G_TYPE_INT format
                    elif  structure.has_field_typed("width",gobject.TYPE_INT) :
                        (resolution["width"] , resolution["height"] ) = (structure["width"],structure["height"])  
                        resolution["framerate"] = None
                        if structure.has_field("framerate") :
                            resolution["framerate"] = webcam_gstreamer_properties.gst_get_framerate(structure["framerate"])
                        if not resolution  in resolution_list :
                            resolution_list.append(resolution)
                    
                    else :
                        # raise error
                        excep_message =  "unkown video type %s"% structure.get_field_type("width")
                        raise LEXCEP.LucioException,excep_message  
        
        for mimetype,res_list in webcam_device["video_formats"].iteritems():
            # loop on video on formats to stort it
            # data are sorted by width , in reverse order; i.e max res is the first in the list
            # for sorting see howto sort : http://wiki.python.org/moin/SortingListsOfDictionaries
            from operator import itemgetter
            result = sorted(res_list, key=itemgetter('width'))
            result.reverse()
            webcam_device["video_formats"][mimetype] = result
        # debug purpose
        #for mimetype,res_list in webcam_device["video_formats"].iteritems():
        #    print "----- %s : %s"%(mimetype,res_list)
    gst_get_supported_video_formats = staticmethod(__gst_get_supported_video_formats)

    def __gst_get_framerate(framerate_obj):
        """ create a list of gst.Fraction framerates """ 
        framerate = list()
        if type(framerate_obj) == list :
            framerate = framerate_obj
        elif isinstance(framerate_obj, gst.FractionRange) :
            # convert also to list of framerate
            NB_FRAMERATE = 4
            MAX_FRAMERATE = gst.Fraction(25,1)
            
            # limit max framerate 
            if framerate_obj.high < MAX_FRAMERATE :
                framerate_obj.high = MAX_FRAMERATE
            
            new_framerate = framerate_obj.high
            for i in range(NB_FRAMERATE) :
                framerate.append(new_framerate)
                new_framerate = new_framerate/2
            # at end of loop append the lowest framerate if not 0
            if framerate_obj.low != gst.Fraction(0,1) :
                framerate.append(framerate_obj.low)
        else :
            # raise error
            excep_message = " unable to detect framerate : unknown type : %s for "%(type(framerate_obj),framerate_obj)
            raise LEXCEP.LucioException,excep_message  
        # transform framerate in not gst format
        if framerate != None :
            framerate_trans = [ (fraction.num,fraction.denom) for fraction in framerate]
        return framerate_trans
    gst_get_framerate = staticmethod(__gst_get_framerate)



    
if __name__ == '__main__' :
    # TEST PURPOSE  : for webcam detection
    CamObj = luciole_webcam_detection()
    val = CamObj.detect_webcam()
    print " found %s webCam device "%val

    #if val >0 :
    #    for device in CamObj.webcam_devices : 
    #        for k,j in device.iteritems() : print "%s : %s"%(k,j)
    #        print "---------------------------------------------"
    for i in range(val) :
    #for enumerate(index,device) in CamObj.webcam_devices :
        best = CamObj.get_gst_best_input(i)
        print "Best webcam resolution found " 
        print best
        print "\n \n"

