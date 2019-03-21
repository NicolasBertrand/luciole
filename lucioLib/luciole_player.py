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

from lcl_gst import lcl_gst_play as LGST_P
import luciole_exceptions as L_EXCEP
import luciole_tools as LT
import luciole_constants as LCONST

import os.path
import gtk

class luciole_player(object):
    """ Manage play of image per image video in the preview window """
  
    _local_tmp_dir="play"
    _jpeg_format = "output-%05d.jpeg"

    def __init__(self,videowidget,cb_eos,tmp_dir) :
        """ 
        init of class luciole_player :
        inputs :
            - videoWidget : Drawing area widget where video is played
            - cb_eos : callback for video eos (eos)
            - tmp_dir : path to a temp dir
        Exeption : 
            - raise if temp dirs cannot be created 
        """
        self._cb_eos = cb_eos
        self._tmp_dir = tmp_dir
      
        # create temp dir, where image go to be stored for play  
        PathToImage =  os.path.join(self._tmp_dir,self._local_tmp_dir)
        #clean or create temp dir 
        try : 
            self._cleanTmpDir(PathToImage)
        except L_EXCEP.LucioException,err :
            raise L_EXCEP.LucioException,err.message
        else : 
            self.PathToImage=PathToImage      
      
            # init gstreamer player
            imagesLocation = os.path.join(self.PathToImage, self._jpeg_format)
            self.player = LGST_P.lcl_gst_play(videowidget,imagesLocation, on_eos_cb = self.on_eos)

    
    def on_eos(self) :
        """ action to do when gestreamer EOS( end of stream) occurs """ 
        
        #self.player.on_eos = lambda *x: on_eos() # Why this line ?   
        self.player.stop()
        self._cb_eos()


    def start_play(self,player_data) :
        """ starts playing 
            player_data is a dictionary with :
            image_list : the image list to play. each element of the list is a full image path
            fpi : the video framerate 
        """
        self._copy_file_to_play(player_data ) # prepare image to play
        
        # get framerate to be used 
        fpi = player_data['fpi']
        framerate = None
        for (k,v) in LCONST.VIDEO_FPS_TABLE.iteritems() :
            #  find the position 
            (l_framerate,l_fpi) = v 
            if l_fpi == fpi : framerate= l_framerate
        # update gstreamer playe number of images 
        self.player.framerate=framerate  
        self.player.play()

    def stop_play(self) :
        """ Stop Video player """
        # stop gstreamer player 
        self.player.stop()


    def _copy_file_to_play(self,player_data) :
        """ 
        This method prepare the image to play. Preparation is :
            - copy in a ordered way images in tmp dir all the images to play
            - set the number of image to play
            - set the framerate   
        """
        for index,image in enumerate(player_data['image_list']) :
            path_src = image
            file_dest = self._jpeg_format%index
            path_dest = os.path.join(self.PathToImage,file_dest)
            if os.path.exists(path_dest) : os.remove(path_dest)   # delete image if image exist
            # REMARK : Exception check is not made : TODO 
            os.link(path_src,path_dest)                           # copy image

        # numbers of image to play
        self.player.nbImages = len(player_data['image_list']) 

     
    def _cleanTmpDir(tmp_dir) :
        """ Clean or create  tmp dir if needed"""

        if not os.path.exists(tmp_dir) :
            #create it
            try :
                LT.mkdirs(tmp_dir)
            except L_EXCEP.LucioException,err :
                raise L_EXCEP.LucioException,err.message
        else :
            # directory exist, clean it
            list = LT.filesInDir(tmp_dir)
            for file in list :
                filePath = os.path.join(tmp_dir,file)
                try :
                    LT.delf(filePath)
                except L_EXCEP.LucioException,err :
                    raise L_EXCEP.LucioException,err.message
        
    _cleanTmpDir = staticmethod(_cleanTmpDir)


