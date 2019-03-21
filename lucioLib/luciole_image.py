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
luciole_image.py :
    Handle imges in luciole application.
        - Manage image type and rush
        - Resize image 
"""

import Image as PIL
import os.path
import gtk
import pango
import subprocess as SP
import threading
import gobject
import time
import Queue
import re

import luciole_tools as LT
import luciole_constants as LCONST

import logging 
module_logger = logging.getLogger('luciole')


#i18n support
import gettext
_ = gettext.gettext

class Image(object):
    
    # class attributes :
    # image_path
    def __get_path(self): return self._image_path
    path = property(__get_path, None, None, "Image's path ")

    # image_name
    def __get_name(self): return self._name
    name = property(__get_name, None, None, "Image's name. ")

    # pixbuf_normal
    def __get_pixbuf_normal(self): return self._pixbuf_normal
    pixbuf_normal = property(__get_pixbuf_normal, None, None, "Normal size pixbuf ")
    
    # pixbuf_thumb
    def __get_pixbuf_thumb(self): return self._pixbuf_thumb
    pixbuf_thumb = property(__get_pixbuf_thumb, None, None, "Thumbnail pixbuf ")
    # thumb_ratio


    def __init__(self, image_path = None, generate_pixbuf = False, thumb_ratio = LCONST.THUMB_RATIO, generate_text = True ):
        """ init Image object
            image_path : absolute imapge path
            generate_pixbuf : set to True to generate pixbuf during init
            thumb_ratio : A thumb ratio from Normal size. Should be an integer value
        """
        
        self.logger = logging.getLogger('luciole')
        self._load_from_file(image_path)
         
        self._pixbuf_normal = None
        self._pixbuf_thumb = None
        self._thumb_ratio = thumb_ratio
        self._generate_text = generate_text
        self.generated = False
        
        
        if generate_pixbuf == True :
            # launch generation of poixbuf at init. Not threaded 
            self._generare_pixbuf()


    def generate_pixbuf_in_gui_thread(self) :
        """ generate pixbuf in gui thread : usage of idle_add"""
        gobject.idle_add(self._generare_pixbuf)
        
    def _generare_pixbuf(self) :
        """ Generation of normal and thumbnail pixbuf  """
        self.generated = False
        self._pixbuf_normal = gtk.gdk.pixbuf_new_from_file(self._image_path)
        # generate normal and thumb pixbuf if requested
        
        # generate thumbnail according the given ratio and image size
        width = self._pixbuf_normal.get_width() / self._thumb_ratio
        height = self._pixbuf_normal.get_height() / self._thumb_ratio
    
        self._pixbuf_thumb = self._pixbuf_normal.scale_simple(  width ,  
                                                                height ,
                                                                gtk.gdk.INTERP_BILINEAR)
        if self._generate_text == True :     
            self._generate_thumb_with_text()

        self.generated =True
        return False

    def _generate_thumb_with_text(self) :
        """ Generate the text on the pixbuf """
        # This technique is used to compose image with text
        # create a pixmap with the data of the pixbuf then insert text
        # cf. pygtk FAQ  How do I draw a text [or something else] on a gtk.gdk.pixbuf? for mor explication 
        # (http://faq.pygtk.org/index.py?req=show&file=faq08.020.htp )  
        
        pixmap,mask = self._pixbuf_thumb.render_pixmap_and_mask()
            
        # graphic context and Drawarea any created to allow generation of pixbuf composition
        gc = pixmap.new_gc()        
        area = gtk.DrawingArea()
        # create pango layout
        self.pangolayout = area.create_pango_layout("")
        
        # extract only the image name without extenstion
        text_buffer, ext = os.path.splitext(self._name)
        text_buffer =" "+text_buffer+" "
        self.pangolayout.set_text(text_buffer)
        # set text attributes
        attrs = pango.AttrList()
        attrs.insert(pango.AttrFamily(LCONST.THUMB_TEXT_FAMILY,0,-1))
        attrs.insert(pango.AttrStyle(pango.STYLE_ITALIC,0, -1))
        attrs.insert(pango.AttrForeground(LCONST.THUMB_TEXT_COLOR[0],LCONST.THUMB_TEXT_COLOR[1],LCONST.THUMB_TEXT_COLOR[2],0,-1))
        attrs.insert(pango.AttrBackground(0,0,0,0,-1))
        attrs.insert(pango.AttrSize(LCONST.THUMB_TEXT_SIZE,0,-1))
        self.pangolayout.set_attributes(attrs)
        
        # compute text layout position and set it on pixmap
        (w,h) = (self._pixbuf_thumb.get_width(),self._pixbuf_thumb.get_height())
        (lw,lh) = self.pangolayout.get_pixel_size()
        pixmap.draw_layout(gc, (w-lw)//2, (h -lh -2), self.pangolayout)
        
        # function get_from_drawable gets the the pixbuf from the pixmap
        # no need to affect resuly to a new pisbuf: self._pixbuf_thumb is changed whe get_from_drawable is used
        self._pixbuf_thumb.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, -1, -1)
        
 
            
    def _load_from_file(self, image_path) :
        """ Private function for loading images"""
        if os.path.isfile(image_path) :
            self._image_path=image_path
            self._name=os.path.split(image_path)[1]
        else :
            self.logger.info( "Not a file : %s"%image_path)

class Rush_images(list):
    """ list of images sources """
    
    # class attributes :
    # rush_index
    def __get_rush_index(self): return self._rush_index
    rush_index = property(__get_rush_index, None, None, " Rush image index ")
    
    def __init__(self,rush_folder,images_list=None,cb_progress = None) :
        """ Warning : the init of Rush_images shall be done inside a thread or thread  not in gui thead 
            rush_folder : folder whe re the images are :
            images_list : list of image to generate 
            cb_progress : used to indicate rush_obj progress creation : (ie number of image object generated
        """ 
        self.logger = logging.getLogger('luciole')
        if (os.path.exists(rush_folder)) :
            self._rush_folder = rush_folder
            self._rush_index = 0

            # if image list not empty generate images
            if images_list != [] :

                self._progression = 1
                self._progression_ratio = 0.0
                self._cb_progress = cb_progress
                # the execution of pixbuf are threaded
                # 1. create the image list
                for index,image in enumerate(images_list) :
                    # craate image onject
                    image_obj = Image(os.path.join(self._rush_folder,image),
                                        False)
                    # append it to list
                    super(Rush_images,self).append(image_obj )
                        
                    # genratat pixbug i threaded way (idle_add)
                    image_obj.generate_pixbuf_in_gui_thread()
                        
                    # wait for pixbuf generation
                    while image_obj.generated == False :
                        time.sleep(0.005)
                    #inidcate ptogression
                    self._progression_ratio = (index +1.0)/len(images_list)
                    if self._cb_progress != None : self._cb_progress(self._progression_ratio)

                
                self._rush_index = self.__get_rush_number_index()
        else :
            self.logger.info('Rush folder not valid')

    def __get_rush_number_index(self) :
        """ this functions extract the rush number according last file name.
        rush list is sorted before. """
        if  self != [] :
            images_name = [ obj.name for obj in self] 
            # sort rush list
            images_name.sort()
            # get last element
            l_last = images_name[-1]
            # on this rush name extract th number
            l_pattern = re.compile(r'\d+')
            # we have just one match we take the first element.
            l_index = int (l_pattern.findall(l_last)[0])
            # now increment index 
            l_index = l_index + 1
        else :
            # rush image is emty so inex is 0
            l_index = 0 
        return l_index 
                
    def get_image(self,image_name):
        """ return image object according image_name """
        for image in self :
            if image.name == image_name : 
                return image
                
        # if this return is reached no image was found
        return None
    

    def append(self,image_name) :
        """ append an image name : generater pixbuf """
        image_path = os.path.join(self._rush_folder,image_name)

        # the generation of pixbuf in not threaded and made imedialtely
        super(Rush_images,self).append(Image(image_path,True))
        
        self._rush_index += 1 
 
    def append_threaded(self,image_name) :
        """ append an image name : generater pixbuf for threaded calls
            Manage the iddle_add stuff for pixbuf generation
        """
        image_path = os.path.join(self._rush_folder,image_name)

        # the generation of pixbuf in not threaded and made imedialtely
        image = Image(image_path,False)
        super(Rush_images,self).append(image )
        image.generate_pixbuf_in_gui_thread()
        
        self._rush_index += 1 
        while image.generated == False :
            time.sleep(0.05)
        return image

    def dump_image_name(self) :
        """ test function display rush image """
        l_list =[]
        for l_i in self : l_list.append(l_i.name)
        return l_list
        

class Image_resize(object) :
    """ resize an image.
    If image is lower then specifoed format , black bands are dawn
    if image is lower image resized ratio is repected, black bands are generated to repect final video 
    format 
    The convert tool from image magic used. 
    """
    convert_cmd_tpl ="convert %s -resize %s\> -size %s xc:black +swap -gravity center -composite %s"
    
    


    def __init__(self, source, dest, format=LCONST.VIDEO_PAL_RES) : 
        """ init object : """
        if os.path.isfile(source) :
            self._source = source
            self._dest =  dest
            self._format="%sx%s"%format
            # check source size
            self._im_format = "" 
            try : 
                im = PIL.open(self._source)
                self._im_format="%sx%s"%im.size
            except :
                err = 'problem with pil'
                raise L_EXCEP.LucioException,err
            else :
                self._convert_cmd = self.convert_cmd_tpl %(self._source,self._format,self._format,self._dest) 
            
        else : 
            #error to raise
            lerr = "Error, path does not exist : %s"%source
            raise L_EXCEP.LucioException,lerr

    def convert(self) :
        """ scale an image if needed """ 
        if self._convert_cmd != None :
            if self._format != self._im_format :
                # image is not at correct size Image need to be scalled
                pCmd =SP.call(self._convert_cmd,shell=True)
            else :
                # format is identical just rename file
                try : 
                    LT.movef(self._source,self._dest)
                except L_EXCEP.LucioException,err :
                    raise L_EXCEP.LucioException,err


# test 

if __name__ == '__main__' :
    X = Image_resize ('/home/nico/temp/testLuciole/Lefilm/capture.jpeg',
                        '/home/nico/temp/testLuciole/Lefilm/tmp/capture.jpeg')
    X.convert()

