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

# for i18n
from gettext import gettext as _
import xml.etree.ElementTree as ET #python 2.5
from xml.parsers.expat import ParserCreate, ExpatError

import luciole_exceptions as LEXCEP

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
       

class lcl_et(object) :
    def __init__(self,xml_file) :
        self.xml_file = xml_file
        #parse XML tempalte file
        try :
            self.xml_obj = ET.parse(self.xml_file)
        except ExpatError , err_value :
            # Raise Error
            lerr =  "XML parse error in ",self.xml_file, "\nerror :",err_value
            raise LEXCEP.LucioException, lerr
            self.xml_obj = None
        
    def findtext(self,condition) :
        return self.xml_obj.findtext(condition)
    
    def find(self,match) :
        return self.xml_obj.find(match)

    def findall(self,match) :
        return self.xml_obj.findall(match)

    def Element(self, tag) :
        return ET.Element(tag)

    def SubElement(self,parent,tag,attrib={}) :
        return ET.SubElement(parent,tag,attrib)

    def insert(self,index,element) :
        return self.xml_obj.insert(index,element)

    def tostring(self,element) :
        return ET.tostring(element)

    def getroot(self) :
        return self.xml_obj.getroot()

    def write(self,file) :
        indent(self.xml_obj.getroot())
        return self.xml_obj.write(file,"UTF-8")
    
