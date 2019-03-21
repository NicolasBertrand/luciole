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
"""
luciole_project.py :
   Manage project
"""
import os.path
import xml.etree.ElementTree as ET #python 2.5
from xml.parsers.expat import ParserCreate, ExpatError


import luciole_constants as LCONST
import luciole_tools as LT
import luciole_exceptions as LEXCEP

import logging 
module_logger = logging.getLogger('luciole')


class project_dico(dict):
    """ 
    Luciole project dicitionary : contains all porject data as dictionary 
    """
    
    #
    # CONSTANTS
    #

    # mandatory tags for webcam description 
    WEBCAM_DATA_TAGS = [ 'name',
                        'device',
                        'source_input',
                        'height',
                        'width',
                        'framerate_list',
                        'framerate_selected',
                        ]
    
    # default values for webcam
    WEBCAM_TAGS_DEFAULT_VALUES = {
            'framerate_list' : [(5,1) ],
            'framerate_selected' : (5,1)  ,
            }
                    
   
    def __init__(self):
        """ constructor : init a dict """
        super(project_dico,self).__init__()

class project_controller(object) :
    """ 
    Class for handling luciole projects : creation, open, save
    """
   
    
    def __init__(self):
        """ Constructor"""
        # init logger
        self.logger = logging.getLogger('luciole')
        self.logger.debug("Entering project_controller")
        # by default no project loaded
        self.__project_loaded = False
    
    def create(self,p_project_dico) :
        """ create project hiararchy and XML structure"""
        p_project_dico['project_dir'] = os.path.join(p_project_dico['project_dir'],p_project_dico['project_name'])
        
        # create project dir and dirs hierarchy
        p_project_dico = self.__create_folders(p_project_dico)

        # update XML filename
        p_project_dico['xml_filename'] = p_project_dico['project_name']+'.xml'

        self.__project_xml = self.__create_xml_file(p_project_dico)
        
        # create 3 empties list for rsuh capture and chrono
        p_project_dico['rush_images'] = [] 
        p_project_dico['capture_images'] = []
        p_project_dico['chrono_images'] = [] 
 
        self.__save_to_xml_file(    
                                os.path.join( p_project_dico['project_dir'],p_project_dico['xml_filename']),
                                self.__project_xml
                                )

    def open(self,project_file_path) :
        """ open an existing project """
        l_project = project_dico()
        if os.path.isfile(project_file_path) :
            #create  project dico
            l_project['project_path'] = project_file_path
            l_project['project_dir'] = os.path.split(project_file_path)[0]
            #parse XML project file
            try :
                self.__project_xml = ET.parse(project_file_path)
            except ExpatError , err_value :
                l_project = None
                lerr =  "XML parse error in ",project_file_path, "\nerror :",err_value
                raise LEXCEP.LucioException, lerr
            else :
                l_project['xml_filename'] = os.path.basename(project_file_path)
                l_project['is_modified'] = LCONST.PROJECT_NOT_MODIFIED 
                # tmp dir nit in xml file but needed
                l_project['tmp_dir'] = LCONST.TMP_DIR
                try : 
                    (l_is_valid, l_project_changed, l_project) = self.__scan_project_file(l_project)
                except LEXCEP.LucioException, err :
                    raise LEXCEP.LucioException, err
                else :
                    self.__project_loaded = True
                    if l_project_changed == True :
                        # save to file loaded project due to project cange
                        # outside application 
                        self.save(l_project)
                        
        else:
            # exception handling
            lerr =  " invalid file name : ",project_file_path
            raise LEXCEP.LucioException, lerr
            l_project = None
        return (l_is_valid, l_project)

    def save(self,p_project_dico ) :
        """ save a project to XML file """
        # create XML object identical to create a new one
        self.__project_xml = self.__create_xml_file(p_project_dico)
        
        # put image name info ( rush, capture,chrono) in XML file
        self.__project_xml = self.__create_xml_images_tag(p_project_dico, self.__project_xml) 
        

        self.__save_to_xml_file(    
                                os.path.join( p_project_dico['project_dir'],p_project_dico['xml_filename']),
                                self.__project_xml
                                )
        
    def save_as(self,p_new_project_dir,p_project_dico) :
        """ save as """
        #memorise old rush_images dir 
        l_src_rush_dir = os.path.join(p_project_dico['project_dir'], p_project_dico['rush_dir'])

        p_project_dico['project_dir'] = p_new_project_dir
        # the new project name is the dir basename (last fir) of the path
        p_project_dico['project_name'] = os.path.basename(p_new_project_dir)
        p_project_dico['xml_filename'] = p_project_dico['project_name']+'.xml'
            
        # 2. create folders hierarchy 
        p_project_dico = self.__create_folders(p_project_dico)
        
        # 3. copy rush images
        try :
            for image_name in p_project_dico['rush_images'] :
                LT.copyf(   os.path.join(l_src_rush_dir,image_name) , 
                        os.path.join(p_project_dico['project_dir'], p_project_dico['rush_dir']) )
        except LEXCEP.LucioException, err :
            lerr =  " Impossible to copy %s  : ",err
            raise LEXCEP.LucioException, lerr
        else : 
            # 4 call save
            self.save(p_project_dico)


####################################################################################################
##### PRIVATE  METHODS
####################################################################################################
    def __save_to_xml_file(self,p_xml_file_path,p_project_xml):
        """ save an XML obect to file """
        # XML file indetation for readability
        self.__indent(p_project_xml.getroot())
        p_project_xml.write(p_xml_file_path,"UTF-8")

    def __scan_project_file(self,p_project) :
        """ scan xml project file """
        # by default a project is valid : 
        # validity is only available with WEBCAM hardtype 
        is_valid = True 
        l_project_changed = False

        # get path and dir data
        p_project['project_name'] = self.__project_xml.findtext("metas/projectName").strip()
        # check if path cahnged 
        if p_project['project_dir'] != self.__project_xml.findtext("metas/projectPath").strip() :
            l_project_changed = True 
        p_project['export_dir'] = self.__project_xml.findtext("metas/export_dir").strip()
        p_project['rush_dir'] = self.__project_xml.findtext("metas/rush_dir").strip()
        # tmp dir nit in xml file but needed
        p_project['tmp_dir'] = LCONST.TMP_DIR
        
        # get FPI
        # nbd@grape text or int value needed ?
        p_project['fpi'] = self.__project_xml.findtext("metas/fpi").strip() 

        # get hardware data
        elem=self.__project_xml.find("metas/hardtype")
        p_project['hardtype'] = int(elem.attrib["id"])
        
       
        # get webcam data
        if p_project['hardtype'] == LCONST.WEBCAM :
            # loop on webcam datas
            et_webcam_data = self.__project_xml.find("//hard_type_data")
            if et_webcam_data != None :
                # loop on webcam data and save on data dictionary
                webcam_data={}
                for my_item in et_webcam_data.getchildren() :
                    # for framerate_selected and framerate_list tage : evaluate to convert in tuple and list
                    # for others keep it as str
                    if my_item.tag == 'framerate_selected' or my_item.tag == 'framerate_list' :
                        webcam_data[my_item.tag] = eval(my_item.attrib.get("key"))
                    else :
                        webcam_data[my_item.tag] = my_item.attrib.get("key")

                # check webcam data validity 
                is_valid = True
                missing_tags = [] 
                for data in p_project.WEBCAM_DATA_TAGS :
                    if not webcam_data.has_key(data) :
                        is_valid = False
                        missing_tags.append(data)

                if is_valid == False :
                    # not a valid project
                    for missing_tag in missing_tags :
                        if p_project.WEBCAM_TAGS_DEFAULT_VALUES.has_key(missing_tag) :
                            webcam_data[missing_tag] = p_project.WEBCAM_TAGS_DEFAULT_VALUES[missing_tag]
                            msg = "  missing_tag : ",missing_tag
                            self.logger.debug(msg)
                        else :
                            err = 'Invalid Project webcam data , tag %s is missing  '%missing_tag
                            raise LEXCEP.LucioException, err
                
                p_project['webcam_data'] = webcam_data
            else :
                # raise Error
                err =  "Invalid webcam data found "
                raise LEXCEP.LucioException, err


        p_project['rush_images'] = self.__scanImages("rushData") 
        p_project['capture_images'] = self.__scanImages("captureData") 
        p_project['chrono_images'] = self.__scanImages("chronoData") 
      
        p_project = self.__check_rush_images(p_project)
        
        return (is_valid, l_project_changed, p_project)


    def __scanImages(self,p_type) :
        """ scan image tag and return image list """
        l_list_out = []
        
        # get tag for image : param p_type 
        DataTag = self.__project_xml.find(p_type)

        list_image = DataTag.getiterator('image')
        
        for image in list_image :
            # append  image name to list
            l_list_out.append(image.text.strip()) 
        
        return l_list_out

    def __check_rush_images(self,p_project) :
        """ verify if all images in project really exist in dir. 
            if not remove it in p_project """
        rush_dir =  os.path.join( p_project['project_dir'] , p_project['rush_dir'] )
        images_to_remove = []
        for image_name in p_project['rush_images'] :
            # test if image exists
            img_path = os.path.join(rush_dir,image_name)
            if not os.path.exists(img_path) :
                msg =  "Not an image : ", image_name
                self.logger.info(msg)
                # image is not on rush dir
                # collect image to suppress  from rush_list
                images_to_remove.append(image_name)
        
        # now remove images in rush list
        for image_name in images_to_remove :
            p_project['rush_images'].remove(image_name) 
               
            # remove also image ref in capture_images
            l_nb_images = p_project['capture_images'].count(image_name)
            if l_nb_images >0 :
                for l_i in xrange(l_nb_images) : p_project['capture_images'].remove(image_name)

            # remove also image ref in chrono_images
            l_nb_images = p_project['chrono_images'].count(image_name)
            if l_nb_images >0 : 
                for l_i in xrange(l_nb_images) : p_project['chrono_images'].remove(image_name)
        
        return p_project





####################################################################################################
##### STATIC METHODS
####################################################################################################

    def __indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for elem in elem:
                project_controller.__indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    __indent = staticmethod(__indent)

    def __create_xml_file(p_project_dico) :
        """ create the xml file for a project ans return it  """
        # load new xml file from template
        __project_xml = ET.parse("./templates/project_template.xml")
        
        # update element tree file     
        elem = __project_xml.find("metas/projectName")
        elem.text =  p_project_dico['project_name']
        
        elem = __project_xml.find("metas/projectPath")
        elem.text =p_project_dico['project_dir']
       
        if p_project_dico.has_key('rush_dir') :
            elem = __project_xml.find("metas/rush_dir")
            elem.text =p_project_dico['rush_dir']

        if p_project_dico.has_key('export_dir') :
            elem = __project_xml.find("metas/export_dir")
            elem.text =p_project_dico['export_dir']

        # update fpi
        elem = __project_xml.find("metas/fpi")
        if (p_project_dico['fpi']):
            elem.text=str(p_project_dico['fpi'])
        else  :
            elem.text='5'
            #  nbd@grape :Warning Static method = Think nefor using logger
            print" !!! No FPI selected, default value 5 frame per image  is set "
  
        # update hardtype
        elem = __project_xml.find("metas/hardtype")
        if (p_project_dico['hardtype']):
            elem.attrib['id'] = str(p_project_dico['hardtype'])
            hard_type_desc = ET.SubElement(elem, 'hard_type_desc') 
            hard_type_desc.text = LCONST.HardTypeName[p_project_dico['hardtype']]
            
            # in case of webcam save specific data
            if p_project_dico['hardtype'] == LCONST.WEBCAM and p_project_dico['webcam_data'] != None : 
                hard_type_data = ET.SubElement(elem, 'hard_type_data')
                # create new elements with same tage name as dictionary
                for k,v in p_project_dico['webcam_data'].iteritems() :
                    t_elem = ET.SubElement(hard_type_data,k)
                    t_elem.attrib['key'] = str(v)
        else :
            elem.attrib['id']=str(LCONST.FAKE)
            elem.text=LCONST.HardTypeName[LCONST.FAKE]
            #  nbd@grape :Warning Static method = Think before using logger
            print " !!! No hardware selected, FAKE hardware selected"
        
        return __project_xml

    __create_xml_file = staticmethod(__create_xml_file)

        
    def __create_xml_images_tag(p_project_dico,p_xml_file) :
        """ create image tag for rush, chrono and image """


        # rush images 
        __parent_image_tag = p_xml_file.find('rushData')
        __images_list =  p_project_dico['rush_images']
        __parent_image_tag = project_controller.__make_tag_image_list(__parent_image_tag, __images_list)

        # capture images 
        __parent_image_tag = p_xml_file.find('captureData')
        __images_list =  p_project_dico['capture_images']
        __parent_image_tag = project_controller.__make_tag_image_list(__parent_image_tag, __images_list)

        # chrono images 
        __parent_image_tag = p_xml_file.find('chronoData')
        __images_list =  p_project_dico['chrono_images']
        __parent_image_tag = project_controller.__make_tag_image_list(__parent_image_tag, __images_list)

        # returm XML file with images
        return p_xml_file

    __create_xml_images_tag = staticmethod(__create_xml_images_tag)
    

    def __make_tag_image_list(p_tag , p_list) :
        """ create all the image tag elems and appen it to tag """
        for image in p_list :
            # create image element
            elem = ET.Element('image')
            elem.text = image
            # then append it in parent
            p_tag.append(elem)            
        return p_tag
   
    __make_tag_image_list = staticmethod(__make_tag_image_list)

        
    def __create_folders(p_project_dico) : 
        """ create project dir and dirs hierarchy """
        p_project_dico['export_dir'] = 'export'
        p_project_dico['rush_dir'] = 'rush'
        p_project_dico['tmp_dir'] = LCONST.TMP_DIR
        folder_to_create = [
                p_project_dico['project_dir'],
                os.path.join( p_project_dico['project_dir'], p_project_dico['export_dir']),
                os.path.join( p_project_dico['project_dir'], p_project_dico['rush_dir']),
                os.path.join( p_project_dico['project_dir'],LCONST.TMP_DIR)
                ]
        try :
            for folder in folder_to_create :
                LT.mkdirs(folder)
        except LEXCEP.LucioException, err :
            lerr =  "impossible to create %s : %s"%(folder,err)
            raise LEXCEP.LucioException, lerr
        else :
            return p_project_dico

    __create_folders = staticmethod(__create_folders)





