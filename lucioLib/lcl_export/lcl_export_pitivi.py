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

# for i18n
from gettext import gettext as _

import os.path

import lcl_export_tool_base as LETBASE


class lcl_export_pitivi (LETBASE.luciole_export_tool):
    """
    class to export luciole project in pitivi format 

    """

    """ ATTRIBUTES
    @__element_id    : Xml tag id for pitivi export file
     
    """
    
    """ CONSTANTS
    """
    # hard coded value in pitivi template
    __SOURCE_DURATION ="18446744073709551615"
    # pitivi type
    __SOURCE_TYPE = "pitivi.factories.file.PictureFileSourceFactory"
    
    __STREAM_CAPS = "video/x-raw-yuv, format=(fourcc)I420, width=(int)720, height=(int)576, framerate=(fraction)0/1"
    __STREAM_NAME = "src0"
    __STREAM_TYPE = "pitivi.stream.VideoStream"

    __BASE_DURATION_NS = 1000000000

    __TIMELINE_TYPE = "pitivi.timeline.track.SourceTrackObject"
    __TIMELINE_IN_POINT = "(gint64)0"
    __TIMELINE_PRIORITY = "(int)0"



    def __init__(self,  lcl_project = "./luciole_project.xml", template="./pitivi_template.xptv", export_file = "./export.xptv"):
        """
        initialization of class  lcl_export_pitivi

        @param object lcl_project : luciole project or file 
        @param string template : Path to template
        @param string export_file : Path to export_file
        """
        super(lcl_export_pitivi, self).__init__(lcl_project,template,export_file )
        
        
        #
        # Attributes init.
        #
        self.__element_id = 0

    def _gen_ressources(self):
        """
        heritage method   
        resources is called sources in pitivi 
        """
        resources_tag = self._template_xml.find("//sources")

        for image in self._lcl_project_data['resources_images'] :
            # build image_path 
            image_p = os.path.join(self._lcl_project_data['image_path'], image)
            image_p = "file://"+image_p
            # create a resource element --> i.e a source element
            new_element = self._template_xml.SubElement(resources_tag,"source",
                    {"filename":image_p,
                     "type":self.__SOURCE_TYPE,
                     "duration":self.__SOURCE_DURATION,
                     "id":self.__new_element_id(),
                     "default_duration":self.__calc_duration(int(self._lcl_project_data['fpi']))
                     })
            
            # create <output-stream> and <stream> sub element 
            new_output_stream = self._template_xml.SubElement(new_element,"output-streams")
            new_stream = self._template_xml.SubElement(new_output_stream,"stream",
                    {"caps":self.__STREAM_CAPS,
                     "name":self.__STREAM_NAME,
                     "id":self.__new_element_id(),
                     "type":self.__STREAM_TYPE
                     })
            
    def _gen_timeline(self):
        """
        heritage method   
        generate timeline :
        in pitivi each image is a track object with ref to <ourrce>

        """
        # get video track on timeline
        video_track = self.__get_timeline_video_tags() 
        
        # create <track-objects> for each resource 
        track_objects = video_track.find('track-objects')
        
        # loop on luciole project timeline images
        for (index,image) in enumerate(self._lcl_project_data['timelines_images']) :
            
            # compute duration and start point
            track_duration = int( self.__calc_duration(int(self._lcl_project_data['fpi'])))
            start_point = index * int(track_duration)
            
            
            # create a track_object
            new_track_object = self._template_xml.SubElement(track_objects,"track-object",
                    { "id":self.__new_element_id(),
                        "type": self.__TIMELINE_TYPE,
                        "duration" :self.__convert_to_gint64(track_duration),
                        "media_duration" : self.__convert_to_gint64(track_duration),
                        "start": self.__convert_to_gint64(start_point),
                        "in_point": self.__TIMELINE_IN_POINT,
                        "priority": self.__TIMELINE_PRIORITY
                        })
            
            # get and create ref tags with sources 
            (factory_id, stream_id) = self.__find_track_id(image)
            self._template_xml.SubElement(new_track_object,"factory-ref", { "id":factory_id})
            self._template_xml.SubElement(new_track_object,"stream-ref", { "id":stream_id})


    #
    # class PRIVATE methods
    #
    def __new_element_id(self):
        """ generates an element id """
        element_id = self.__element_id
        self.__element_id += 1
        return str(element_id)

    def __calc_duration(self,fpi) :
        """ compute duration in pitivi format. 
            Input is the fpi : number of frame per image
        """
        print "export pitivi calc duration fpi = %s"%fpi
        duration = (1.0/ (25.0/fpi) )*self.__BASE_DURATION_NS
        # use of str and int : int for a rounded value and str for string in element tree
        return str(int(duration))

    def __get_timeline_video_tags(self) :
        """
           in pitivi timeline tag is <timeline>
           video is on <track>/<stream> with typepitivi.stream.VideoStream
        """
        video_track = None
        tracks = self._template_xml.findall("//track")
        for track in tracks:
            stream = track.find("stream")
            if stream.attrib["type"] == self.__STREAM_TYPE :
                video_track = track
                break
        return video_track

    def __convert_to_gint64(self,value) :
        """ convert to gint64 format. Only str conversion"""
        return "(gint64)"+str(value)

    def __find_track_id(self,image) :
        """ find image ids for pitivi according image name """
        sources = self._template_xml.findall("//source")
        (source_id, stream_id) = (None,None)
        for source in sources :
            filename  = source.attrib["filename"]
            filename = filename.split('/')[-1]
            if filename == image :
                # get source id
                source_id = source.attrib['id']
                # find stream id
                stream_id = source.find('output-streams/stream').attrib['id']
                break
        return (source_id, stream_id)



    
