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
"""
lcl_export_tool_base.py
Base export to tool definition and class

"""
# for i18n
from gettext import gettext as _

import os.path
from .. import luciole_et as LE
from .. import luciole_exceptions as LEXCEP
from .. import luciole_project as LPROJECT

class luciole_export_tool(object) :
    """
    Base class for export to tool
    """
    
    
    """ ATTRIBUTES
    @_export_file        : Path to file to export
    @_template           : Path to template
    @_lcl_project        : The luciole project a file or a dict
    @_lcl_project_data   : luciole project data dictionary filled with ecport data 
    @_export_template    : File to update with export data
    @_template_xml       : the export template loaded as xml file
    """
    


    def __init__(self,  lcl_project = "./luciole_project.xml", template="./template.xml", export_file = "./export.xml"):
        """
        @param lcl_project      : luciole project  
        @param template         : Path to template
        @param export_file      : Path to export_file
        """
        #
        # Atributes init
        #
        self._lcl_project = lcl_project
        self._template = template
        self._export_file = export_file
        self._lcl_project_data = {}
        self._lcl_project_data['resources_images'] = []
        self._lcl_project_data['timelines_images'] = []

        self._export_template = None
        self._template_xml = None
        
        if (type(lcl_project) == str) : 
            # test file type
            if os.path.exists(lcl_project) :
                #filetype exits load it
                self.__load_lcl_file()
            else :
                #Raise Error
                excep_message = "%s is ot a file",lcl_project
                raise LEXCEP.LucioException,excep_message            
        elif (type(lcl_project) == LPROJECT.project_dico) :
            # input is a dictionary
            self.__load_lcl_dict()
        else :
            # template does not exists : raise an exception
            excep_message = "Invalid projetc type nor file nor luciole_project"
            raise LEXCEP.LucioException,excep_message            
        
        #
        # Test template
        #
        if os.path.exists(self._template) :
            self._load_template()
        else :
            # template does not exists : raise an exception
            excep_message = " Template file %s does not exist"%self._template
            raise LEXCEP.LucioException,excep_message            

            


    def generate(self):
        """
         

        @return  :
        @author
        """
        self._gen_meta()
        self._gen_ressources()
        self._gen_timeline()
        self.__write_export_file()

    def _load_template(self):
        """
         

        @return  :
        @author
        """

        self._template_xml = LE.lcl_et(self._template)

    def _gen_ressources(self):
        """
         generate date for resources

        @return  :
        @author
        """
        pass

    def _gen_timeline(self):
        """
         Generate data for timeline

        @return  :
        @author
        """
        pass

    def _gen_meta(self) :
        """
         Generate meta information for project

        @return  :
        @author
        """
        pass



    def __load_lcl_file(self):
        """
         Load a Luciole project from a file dictionary

        @return  :
        @author
        """
        try :
            _lcl_project_xml = LE.lcl_et(self._lcl_project)
        except :
            pass
        else :
            self._lcl_project_data['image_path'] = os.path.join(_lcl_project_xml.findtext("metas/projectPath").strip() , 
                                                        _lcl_project_xml.findtext("metas/rush_dir").strip() )
            self._lcl_project_data['fpi'] = int(_lcl_project_xml.findtext("metas/fpi").strip())
            
            # get resources images from project capture data
            list_image = _lcl_project_xml.find("captureData").getiterator('image')
            [ self._lcl_project_data['resources_images'].append(image.text.strip())  for image in list_image]
            
            # get timelines images from project chrono data
            list_image = _lcl_project_xml.find("chronoData").getiterator('image')
            [self._lcl_project_data['timelines_images'].append(image.text.strip())  for image in list_image]
            

    def __load_lcl_dict(self):
        """
         Load a Luciole project from a dictionary

        @return  :
        @author
        """
        
        self._lcl_project_data['image_path'] = os.path.join(self._lcl_project['project_dir'], self._lcl_project['rush_dir'])
        self._lcl_project_data['fpi'] = int(self._lcl_project['fpi'])
        self._lcl_project_data['resources_images'] = self._lcl_project['capture_images']
        self._lcl_project_data['timelines_images'] = self._lcl_project['chrono_images']


    def __write_export_file(self):
        """
         

        @return  :
        @author
        """
        self._template_xml.write(self._export_file)

   
