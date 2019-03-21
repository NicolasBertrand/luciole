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

""" file luciole_conf.py """

import os.path
import luciole_exceptions as LEXCEP
import luciole_tools as MT

from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import xml.etree.ElementTree as ET 

import copy

import gtk

from gettext import gettext as _

import logging 
module_logger = logging.getLogger('luciole')

class LucioleConf(object):
    """ Manage the configuration file of luciole """    
    
    __USER_LUCIOLE_DIR = ".luciole"
    __CONF_FILE_NAME = "lucioleConf.xml"
    __ORIGINAL_DIR = "templates"
    __THEME_DIR = "themes"

    def _get_conf_options(self):
        """ get method for option dicrionary """
        return self._option_dict
    def _set_conf_options(self,key,value) :
        if self._option_dict.has_key(key) : self._option_dict[key] = value

    conf_options = property(_get_conf_options, _set_conf_options, None, "Options dictionary")

 
    def __init__(self):
        """ init of luciole conf :
            - if conf file does not exist in user dir create it
            - parse xml conf file
        """
        
        self.logger = logging.getLogger('luciole')
        self._home_dir = os.path.expandvars('$HOME')
        self._option_dict = dict()
        self._option_dict["LastProjects"] = list()
        self._conf_et = None
        # verify if luciole confile exits
        conf_file_path = os.path.join(self.__USER_LUCIOLE_DIR, self.__CONF_FILE_NAME)
        self._conf_file_path = os.path.join(self._home_dir, conf_file_path)
        if os.path.exists(self._conf_file_path) :
            # luciole file exist parse it
            self._parse_conf_file()
        else :
            try :
                # copy file to local dir
                self._copy_conf_file(os.path.join(self.__ORIGINAL_DIR,self.__CONF_FILE_NAME))
                # and parse it 
                self._parse_conf_file()
                
            except LEXCEP.LucioException, err :
                lerr =  "Error in copy %s : ",err
                raise LEXCEP.LucioException, lerr
    #
    # Public methods
    # 
    
    def update_last_project(self, project_list = [] ) :
        """ update project list file """
        if project_list != [] :
            self._option_dict["LastProjects"] = project_list
        last_projects = self._conf_et.find("LastProjects")
        #copy list objecy
        lproject_list = copy.copy(project_list) 
        lproject_list.reverse()        
        for my_iter in last_projects.getiterator("LastProject") :
            if lproject_list : 
                my_iter.text = lproject_list.pop()           
        self._conf_et.write(self._conf_file_path ,"UTF-8")


    def load_theme(self) :
        """ Load a gtk theme """
        self.logger.debug('Entering theme load')
        if self._option_dict.has_key('Theme') :
            l_path = os.path.join(self.__THEME_DIR,self._option_dict['Theme'])
            if os.path.exists(l_path) :
                gtk.rc_parse(l_path)
            else :
                msg =  _('Theme %s does not exist'%l_path)
                self.logger.info(msg) 
        else : 
            msg =  _('Impossible to load theme')
            self.logger.info(msg) 
        self.logger.debug('Exiting theme load')

    def save_options(self) :
        options_el =  self._conf_et.find("options")
        for my_iter in options_el.getiterator("option") :
            (name , value ) = (my_iter.get('name'), my_iter.get('value'))
            if self._option_dict.has_key(name) and self._option_dict[name] != value :
                # key exist and value change update xml file
                my_iter.set('value',self._option_dict[name])
        #save to file
        self._conf_et.write(self._conf_file_path ,"UTF-8")

    #
    # Private methods
    #

    def _copy_conf_file(self, source_conf_file) :
        """ copy config file to user dir """
        #check if user luciole dir exist
        ldir = os.path.join(self._home_dir, self.__USER_LUCIOLE_DIR)
        if os.path.exists(ldir) :
            if os.path.isdir(ldir) :
                # cp luciole_conf file
                try :
                    MT.copyf(source_conf_file, ldir)
                except LEXCEP.LucioException, err :
                    raise  LEXCEP.LucioException, err
            else :
                try :
                    MT.delf(ldir)
                except LEXCEP.LucioException, err :
                    raise  LEXCEP.LucioException, err
        else :
            # dir .luciole does not exist
            try :
                MT.mkdirs(ldir)
            except LEXCEP.LucioException, err :
                raise  LEXCEP.LucioException, err
            else :
                # cp luciole_conf file
                try :
                    MT.copyf(source_conf_file, ldir)
                except LEXCEP.LucioException, err :
                    raise  LEXCEP.LucioException, err

    
    def _parse_conf_file(self) :
        """ parse user config file """
        # first XML validity of document
        try :
            LucioleConf._check_xml_validity(self._conf_file_path)
        except Exception, err :
            lerr == " File %s is NOT well formed !! %s" % (self._conf_file_path, err)
            raise LEXCEP.LucioException, lerr
        else :
            # parse configFile with elemenent Tree 
            self._conf_et = ET.parse(self._conf_file_path)
            
            # get used projects history
            last_projects = self._conf_et.find("LastProjects")
            for my_iter in last_projects.getiterator("LastProject") :
                # check that Last project tag is not empty 
                if my_iter.text :
                    project_path = my_iter.text.strip()
                    # update options only if project exists
                    if os.path.exists(project_path) :
                        self._option_dict["LastProjects"].append(project_path)
            # get theme 
            self._parse_options()

    def _parse_options(self) :
        """ Parse options  """
        options_el =  self._conf_et.find("options")
        for my_iter in options_el.getiterator("option") :
            (name , value ) = (my_iter.get('name'), my_iter.get('value'))
            if name != None and value != None :
                self._option_dict[name] = value

    def _check_xml_validity(my_file) :
        """ check if config XML file is well formed """
        parser = make_parser()
        parser.setContentHandler(ContentHandler())
        parser.parse(my_file)
    _check_xml_validity = staticmethod(_check_xml_validity)


