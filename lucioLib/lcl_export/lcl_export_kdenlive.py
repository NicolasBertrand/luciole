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
import subprocess as SP
import os
import stat

import lcl_export_tool_base as LETBASE

from .. import luciole_constants as LCONST

class lcl_export_kdenlive (LETBASE.luciole_export_tool):
    """
    class to export luciole project in cinelerra format 
    kdenlive files are xml files based on MLT framework

    """

    """ ATTRIBUTES
    @___element_id : Xml tag id for kdenlive export file
    @__list_id_producer : List of kdenlive producer tag's id
    @__total_duration : Total duration, in frame, or movie in timeline

    """
    
    """ CONSTANTS
    """
    __PRODUCER_AUDIO_MAX = "0"
    __PRODUCER_VIDEO_MAX = "0"
    __PRODUCER_CHANNELS = "0"
    __PRODUCER_DEFAULT_AUDIO = "0"
    __PRODUCER_FRAME_SIZE = str(LCONST.VIDEO_PAL_RES[0])+"x"+ str(LCONST.VIDEO_PAL_RES[1])
    __PRODUCER_FREQUENCY = "0"
    __PRODUCER_IN = "0"
    __PRODUCER_ASPECT_RATIO = "1.000000"
    __PRODUCER_TYPE ="5"
    __PRODUCER_DEFAULT_VIDEO = "0"
    __PRODUCER_POS = 4
    __PLAYLIST_ID = "lcl_track" 

    __META_HOMEDIR = os.path.expandvars('$HOME')
    __META_PROJECFOLDER = os.path.join(os.path.expandvars('$HOME'),"kdenlive")
    __META_PROJECT_NAME =  "Submission from luciole"




    def __init__(self,  lcl_project = "./luciole_project.xml", template="templates/kdenlive_template.kdenlive", export_file = "./export.xptv"):
        """
        initialization of class  lcl_export_kdenlive

        @param object lcl_project : luciole project or file 
        @param string template : Path to template
        @param string export_file : Path to export_file
        @return  :
        @author
        """
        super(lcl_export_kdenlive, self).__init__(lcl_project,template,export_file )

        self.__element_id = 1
        self.__list_id_producer = []
        self.__total_duration = 0

    def _gen_meta(self):
        """
        generate meta information for kdenlive file
        """
        mlt_tag =  self._template_xml.getroot() 
        mlt_tag.attrib["root"] = self.__META_HOMEDIR
        mlt_tag.attrib["title"] = self.__META_PROJECT_NAME
        kdenlivedoc = self._template_xml.find("//kdenlivedoc")
        kdenlivedoc.attrib["projectfolder"] = self.__META_PROJECFOLDER

    def _gen_ressources(self):
        """
        resources is called <kdenlive_producer> and is stored in <kdenlive_doc> 
        """
        resources_tag = self._template_xml.find("//kdenlivedoc")

        duration =  self.__calc_duration( self._lcl_project_data['fpi'])
        for image in self._lcl_project_data['resources_images'] :
            # build image_path 
            image_p = os.path.join(self._lcl_project_data['image_path'], image)
            # create a resource element --> i.e a kdenlive_producer element

            new_element = self._template_xml.SubElement(resources_tag,"kdenlive_producer",
                    {"audio_max":       self.__PRODUCER_AUDIO_MAX,
                     "channels" :       self.__PRODUCER_CHANNELS,
                     "duration" :       str(duration),
                     "default_audio" :  self.__PRODUCER_DEFAULT_AUDIO,
                     "video_max" :      self.__PRODUCER_VIDEO_MAX,
                     "frame_size" :     self.__PRODUCER_FRAME_SIZE,
                     "frequency" :      self.__PRODUCER_FREQUENCY,
                     "in" :             self.__PRODUCER_IN,
                     "file_size" :      self.__calc_file_size(image_p),
                     "aspect_ratio" :   self.__PRODUCER_ASPECT_RATIO,
                     "out" :            str(duration-1),
                     "file_hash" :      self.__calc_file_hash(image_p),      
                     "type" :           self.__PRODUCER_TYPE,
                     "id" :             self.__new_element_id(),
                     "name" :           image,
                     "default_video" :  self.__PRODUCER_DEFAULT_VIDEO,
                     "resource" :      image_p,
                     })
            
    def _gen_timeline(self):
        """
        The timeline in kdenlive is divided in 3 steps : the <producer> tag, the <playlist>, and <tractor>
        """
        self.__gen_producer()
        self.__gen_playlist()
        self.__gen_tractor()


    #
    # class PRIVATE methods
    #

    def __new_element_id(self):
        """ generates an element id """
        element_id = self.__element_id
        self.__element_id += 1
        return str(element_id)

    def __calc_file_hash(self,file) :
        """ compute the md5sum of a file.
        These function needs robustness in cas on non success of md5sum command"""
        output =SP.Popen(["md5sum",file], stdout=SP.PIPE).communicate()[0]
        # output is a srting who looks like : hash_code   file
        # return only the hashcode
        return output.split()[0]

    def __calc_file_size(self,file) : 
        """ compute the file size """
        fsz = os.stat(file)[stat.ST_SIZE]
        return str(fsz)
     
    def __calc_duration(self,fpi) : 
        """ kdenlive does not support ressource with duration less then 3 frames ...."""
        fr = int(fpi)
        if fr < 3 : fr =3 
        return fr
            
    def __get_timeline_video_tags(self) :
        """
           in pitivi timeline tag is <timeline>
           video is on <track>/<stream> with typepitivi.stream.VideoStream,        """    
        video_track = None
        tracks = self._template_xml.findall("//track")
        for track in tracks:
            stream = track.find("stream")
            if stream.attrib["type"] == self.STREAM_TYPE :
                video_track = track
                break
        return video_track


    def __find_black_track(self) :
        """ get back track play list. return the entry element """
        pl_found = None
        for pl in self._template_xml.findall("//playlist") :
            if pl.attrib["id"] == "black_track" :
                pl_found = pl
                break
        return pl_found.find("entry")

    def __find_kdenlive_producer_id(self,image) :
        """ find the id of a <kdenlive_producer> tag """
        kd_producer_tags = self._template_xml.findall("//kdenlive_producer")
        id_found  = None
        for kd_producer_tag in kd_producer_tags :
            if kd_producer_tag.attrib['name'] == image :
                id_found = kd_producer_tag.attrib['id']
        # raise error if id not found
        return id_found

    def __gen_proprety_tag(self,producer_tag,name,text) :
        """ generate property tag """
        prop_tag = self._template_xml.SubElement(producer_tag,"property",{
                                        "name":name})
        prop_tag.text = text
        

    def __gen_producer_properties(self,producer_tag, image_p) :
        """ properties of producer tag. Dirty generation. """
        self.__gen_proprety_tag(producer_tag,"mlt_type","producer")
        self.__gen_proprety_tag(producer_tag,"aspect_ratio","1")
        self.__gen_proprety_tag(producer_tag,"length","15000")
        self.__gen_proprety_tag(producer_tag,"eof","pause")
        self.__gen_proprety_tag(producer_tag,"resource",image_p)
        self.__gen_proprety_tag(producer_tag,"ttl","25")
        self.__gen_proprety_tag(producer_tag,"progressive","1")
        self.__gen_proprety_tag(producer_tag,"mlt_service","pixbuf")


    def __gen_producer(self) : 
        """ <producer> tag have attributes and property subtag.
            Producer tag is a son of <mlt> tag """        
        mlt_tag =  self._template_xml.getroot()
        producer_pos = self.__PRODUCER_POS

        duration = str(self._lcl_project_data['fpi'])
        # loop on luciole project timeline images
        for (index,image) in enumerate(self._lcl_project_data['timelines_images']) :
            id_kd_producer = self.__find_kdenlive_producer_id(image)
            if id_kd_producer != None :
                # create the tag 
                producer_tag= self._template_xml.Element("producer")
                producer_tag.set("in",self.__PRODUCER_IN)
                producer_tag.set("out",duration)
                producer_tag.set("id",id_kd_producer)
                mlt_tag.insert(producer_pos,producer_tag)

                # create <property> tags
                image_p = os.path.join(self._lcl_project_data['image_path'], image)
                self.__gen_producer_properties(producer_tag, image_p)
                
                # remember the id for playlist generation
                self.__list_id_producer.append(id_kd_producer)

                #increment position for next element
                producer_pos += 1

    def __gen_playlist_entry(self,pl_tag,out,producer) :
        """ playlist entry tag"""
        self._template_xml.SubElement(pl_tag,"entry",{
                                        "in":self.__PRODUCER_IN,
                                        "out":out,
                                        "producer":producer})


    def __gen_playlist(self) :
        """ generate playlist """
        mlt_tag =  self._template_xml.getroot()
        
        # get playlist tag
        playlists_tag =  self._template_xml.findall("//playlist")
        playlist_tag = None
        for tag in playlists_tag :
            if tag.attrib["id"]  == self.__PLAYLIST_ID :
                playlist_tag = tag
        # generate entry tag and compute duration of all timeline 
        if playlist_tag != None :
            # compute duration
            duration = int(self._lcl_project_data['fpi']) 
        
            for id_p  in self.__list_id_producer :
                self.__gen_playlist_entry(playlist_tag,str(duration),id_p)
                self.__total_duration += duration
        
            self.__total_duration =  self.__total_duration -1         

    def __gen_tractor(self) :
        """ modify tractor tag""" 
        tractor_tag = self._template_xml.find("tractor")
        tractor_tag.attrib['out'] = str(self.__total_duration)
        
        #update duration in black_track playlist
        pl_entry=self.__find_black_track()
        pl_entry.attrib["out"] = str(self.__total_duration)


    
