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


class lcl_export_cinelerra (LETBASE.luciole_export_tool):
    """
    class to export luciole project in cinelerra format 
    """

    """ ATTRIBUTES
    N/A
    """

    def __init__(self,  lcl_project = "./luciole_project.xml", template="./template.xml", export_file = "./export.xml"):
        """
        initialization of class  lcl_export_cinelerra

        @param object lcl_project : Luciole project or file
        @param string template : Path to template
        @param string export_file : Path to export_file
        """
        super(lcl_export_cinelerra, self).__init__(lcl_project,template,export_file )

    def _gen_ressources(self):
        """
        ressource is called asset in cinelerra template 
        """
        resources_tag = self._template_xml.find("//ASSETS")
        resource_elem_tpl =  self._template_xml.find("//ASSET")

        for image in self._lcl_project_data['resources_images'] :
            # build image_path 
            image_p = os.path.join(self._lcl_project_data['image_path'], image)
            # create a resource element --> i.e an ASSET element
            new_element = self._template_xml.SubElement(resources_tag,"ASSET",{"SRC":image_p})
            # copy subelement ASSET template tag in new element
            for elem_tpl in resource_elem_tpl.getchildren() :
                new_element.append(elem_tpl)
        
        #remove template tag
        resources_tag.remove(resource_elem_tpl)
    
    def _gen_timeline(self):
        """
        generate timeline 
        """
        (timeline_tag, timeline_item_tpl) = self.__get_timeline_tags()
        for image in self._lcl_project_data['timelines_images'] :
            # build image_path 
            image_p = os.path.join(self._lcl_project_data['image_path'], image)
            
            # create New EDIT element per image 
            for frame in range(self._lcl_project_data['fpi']):
                framerate = str(self._lcl_project_data['fpi'])
                new_element = self._template_xml.SubElement(timeline_tag,"EDIT",{"STARTSOURCE":"0","CHANNEL":"0", "LENGTH":"1"})
                # create FILE subElement of EDIT
                self._template_xml.SubElement(new_element,"FILE",{"SRC":image_p})
        
        # remove EDIT template tag 
        timeline_tag.remove(timeline_item_tpl)
            
    #
    # class PRIVATE methods
    #    
    def __get_timeline_tags(self) :
        """
           in cinelerra timeline tags is TRACK with type video, and EDITS/EDIT tag
        """
        video_track = None
        tracks = self._template_xml.findall("//TRACK")
        for track in tracks :
            if track.get("TYPE") == "VIDEO" :
                # video track is found
                video_track = track
                break
        # get EDIT tag
        return ( video_track.find("EDITS"), video_track.find("EDITS/EDIT"))


  

if __name__ == '__main__' :
    X = lcl_export_cinelerra( lcl_project = "/home/nico/temp/testLuciole/luciole_project_isight/luciole_project_isight.xml",template="./cinelerra_template.xml",export_file = "./cine_export.xml" ) 
    X.generate()
    
