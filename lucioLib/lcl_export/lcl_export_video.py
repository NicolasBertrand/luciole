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

import subprocess as SP
import os
import os.path
import dircache
import fnmatch
import string
import tempfile
import dircache
import re

from .. import luciole_tools as MT
from .. import luciole_exceptions as LEXCEP

import logging 
module_logger = logging.getLogger('luciole')

import gobject
import threading
import Queue
import time

# for i18n
from gettext import gettext as _


import os
import signal

(IMAGE_LIST,IMAGE_DIR)=range(2)
ERR_FILE_EXIST = 1
(EXPORT_DV,EXPORT_DVD,EXPORT_XVID) = range(3)

# Mencoder commands for export , according export type
dictPal= { 
    #EXPORT_DV : "-vf scale=720:576 -ofps 25 -ovc lavc -oac pcm",
    EXPORT_DV : "-target pal-dv -aspect 4:3",
    EXPORT_DVD : "-vf scale=720:576 -ofps 25 -oac pcm -ovc lavc -lavcopts vcodec=mpeg2video:vbitrate=9600:aspect=4/3", 
    EXPORT_XVID : "-vf scale=720:576 -ofps 25 -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=2000:aspect=4/3  -oac mp3lame -lameopts cbr:br=128", 
}

dictEncoder= {
    "PAL":dictPal,
    }


class MyThreadConvertToYuv(threading.Thread):
    """ Thread class for convert a sequence of image to a YUV file """
  
    def _get_abort(self): return self.__abort
    def _set_abort(self, value): 
        if value in (True,False) : self.__abort = value
    abort = property(_get_abort, _set_abort, None, "abort thread work")


    def __init__(self,imageInputType,imageDir,imageList,ppmtoy4m_opts,framesPerImage,tmpDir,VideoName,finish_queue,export_gui_obj):
        """ Thread class initialisation  """
        super(MyThreadConvertToYuv, self).__init__()
        self.__imageInputType = imageInputType
        self.__imageDir = imageDir
        self.__imageList = imageList
        self.__ppmtoy4m_opts = ppmtoy4m_opts
        self.__framesPerImage = framesPerImage
        self.__tmpDir = tmpDir
        self.__VideoName = VideoName
        self.__queue= finish_queue

       
        self._export_gui_obj = export_gui_obj
        self._export_gui_obj.progress_bar_text = _("Pass 1/2")
        self._export_gui_obj.progress_bar_fraction = 0

        self.__abort = False # reset abort value

    def _on_finish(self, file_path,abort):
        """Callback function. Raised when conversions is finished"""
        #preparation of next pass if no abort
        if abort == False :
            self._export_gui_obj.progress_bar_text = _("Pass 2/2") 
        self._export_gui_obj.progress_bar_fraction = 0.0
        # TBD : missing update of file path in export obj 
        self.__abort = False # reset abort value
        return False

    def _on_progress(self, value):
        """Callback function. used to know the conversion progress """
        self._export_gui_obj.progress_bar_fraction = value
        return False

    def _convertToYuv(self) :
        """ This memthod is used to convert the sequence of image in a raw
            video in YUV4MPEG format. This method use external tools as
            imagemagick and tools (ppmtoy4m) from mjpegtools suite."""
        # Get first the list of image To co_nvert is depending of the type 
    
        if self.__imageInputType == IMAGE_DIR :
            # input images are stored in a directory
            imagesToConv = MT.filesInDir(self.__imageDir,"*.jpeg")
        else :
            # input images are in a list
            imagesToConv =  self.__imageList
        # copmute the number of frames to genarate = Number of images * nf of frame per image
        nbFrames = len(imagesToConv)*self.__framesPerImage
        self.__ppmtoy4m_opts['-n'] = str(nbFrames)      #update the numner of frames for  
    
        video_temp_base=os.path.join(self.__tmpDir,self.__VideoName)
        # build  ppmtoy4m_cmd
        ppmtoy4m_cmd = ""
        for key,value in self.__ppmtoy4m_opts.items() :
            mystring = " "+ key
            if value : mystring = mystring + " "+value
            ppmtoy4m_cmd = mystring + ppmtoy4m_cmd
        ppmtoy4m_cmd = 'ppmtoy4m'+ppmtoy4m_cmd

        # launch ppmtoy4m, this process run during all the image convesrion
        # and receive in stdin images converted in ppm format 
        # the ppm images are sent to this subprocess by the convert operation
        # see p2 below 
        fd5 = os.open(video_temp_base+".yuv",os.O_WRONLY|os.O_CREAT)
        fd6 = os.open(video_temp_base+".log",os.O_WRONLY|os.O_CREAT)

        ppm_proc = SP.Popen(ppmtoy4m_cmd, shell=True, stdin=SP.PIPE,stdout=fd5,stderr=fd6)
        frame_cpt = 0
        for (count_image,image) in enumerate(imagesToConv) :
            # check abort 
            if self.__abort == True : break
            #loop on images to convert
            #conversion and rezizing of cuurent image
            imagePath = os.path.join(self.__imageDir,image)
            montage_cmd = "montage  -type TrueColor -quality 100 -geometry 720x576  "+imagePath+ " " + video_temp_base+".jpg"
            pMontage =SP.call(montage_cmd,shell=True)
            convert_cmd = "convert -type TrueColor -quality 100 "+video_temp_base+".jpg " +video_temp_base+".pnm "
            pconvert =SP.call(convert_cmd,shell=True)
          
            for i in range(self.__framesPerImage) :
                # check abort 
                if self.__abort == True : break
                frame_cpt = frame_cpt +1
                convert_cmd = "convert -depth 8 ppm:"+video_temp_base+".pnm -"
                p1 = SP.Popen(convert_cmd,shell=True, stdout=ppm_proc.stdin,stderr=SP.PIPE)
                p1.wait()
            # progress bar update 
            progression = ((count_image+1.0)/len(imagesToConv)) 
            gobject.idle_add(self._on_progress,progression)
        os.fsync(fd5)
        os.close(fd5)
        os.close(fd6) 
        #return the path to yuv file
        return video_temp_base+".yuv"
  
    def run(self) :
        """ Thread start --> launch images to video conversion """
        yuvfile_path = self._convertToYuv()
        self.__queue.put(yuvfile_path)
        gobject.idle_add(self._on_finish,yuvfile_path,self.__abort)



class MyExportThread(threading.Thread):
    """ Export Thread. Thread in charge to enconde video in Yuv format
        to DV, DVD or XVID format
    """
  
    def _get_abort(self): return self.__abort
    def _set_abort(self, value): 
        if value in (True,False) : self.__abort = value
    abort = property(_get_abort, _set_abort, None, "abort thread work")
  
    def __init__(self, exportType, videoOutPath, yuv_queue, export_gui_obj) :
        """ Init export video Thread"""
        super(MyExportThread, self).__init__()
        self.logger = logging.getLogger('luciole')
        self.__abort = False
        (self._exportType,self._videoInPath,self._videoOutPath) = (exportType,None,videoOutPath)
        self.__queue = yuv_queue
        self._export_gui_obj = export_gui_obj

    def _on_finish(self,abort):
        """Callback function. Raised when conversions is finished"""
        # update gui progress bar
        if abort == False : 
            # Terminated normaly 
            self._export_gui_obj.progress_bar_text = _("Export Done")
            self._export_gui_obj.progress_bar_fraction = 1.0
        else :
            self._export_gui_obj.progress_bar_text = _("Export Canceled")
            self._export_gui_obj.progress_bar_fraction = 0.0
            self.__abort = False # reset abort
        return False

    def _on_progress(self, value):
        """Callback function. used to know the conversion progress """
        self._export_gui_obj.progress_bar_fraction = value
        return False

    def run(self):
        """ Thread execution --> generate export """
        """ Build and launch ffmpeg command. """
        yuv_is_finished=False
        data = None
        while (yuv_is_finished == False) :
            time.sleep(0.1)
            try :
                data=self.__queue.get(block=False)
                yuv_is_finished=True
            except Queue.Empty :
                pass
            # check abort if true leave it  
            if self.__abort == True :
                data = None
                break
        if data :
            self._videoInPath = data
            if self._exportType == EXPORT_DV :
                self._ffmpeg_launcher()
            else :
                self._mencoder_launcher()   
        gobject.idle_add(self._on_finish,self.__abort)

    def _ffmpeg_launcher(self):
        """ Video conversion with ffmpeg : only used for DV conversion """
        self.__videoFormat = "PAL" # only PAL is supported 
        self.__withSound = False        # no sound by default
        if ( (self._exportType == EXPORT_DV)  and ( self._videoInPath ) and ( self._videoOutPath ) ) :
            #
            # Build ffmpeg command
            #
            ffmpeg_cmd = []
            ffmpeg_cmd.append("ffmpeg")
            # add input video name
            ffmpeg_cmd.append('-i')
            ffmpeg_cmd.append(self._videoInPath)
            # add video conversion options
            coding_command = dictEncoder["PAL"][EXPORT_DV]       
            for ffmpeg_w in coding_command.split() : ffmpeg_cmd.append(ffmpeg_w)
            # add output video name
            ffmpeg_cmd.append(self._videoOutPath)
            
            #
            # launch ffmpeg subprocess
            #
            self.logger.debug("command :%s"%ffmpeg_cmd)
            sb_encoder =SP.Popen(ffmpeg_cmd,stdout=SP.PIPE,stderr=SP.PIPE)
            
            #
            # check encoding process and finish
            #
            encode_not_finish = True
            pulse_counter = 0
            pulse_modulo = 20
            while encode_not_finish == True:
                ret_code = sb_encoder.poll()
                if type(ret_code) == int :
                    # encoding is finished when a code is returned
                    encode_not_finish = False
                if pulse_counter % pulse_modulo == 0 :
                    # update progress bar only with pulses
                    gobject.idle_add(self._on_progress, 2.0 )
                pulse_counter = pulse_counter +1

    def _mencoder_launcher(self) : 
        """ Video conversion with mencoder : used for convestion in DVD and XVID format"""
        self.__videoFormat = "PAL" # only PAL is supported
        self.__withSound = False        # no sound by default
        if ( (self._exportType in (EXPORT_DVD,EXPORT_XVID))  and ( self._videoInPath ) and ( self._videoOutPath ) ) :
            #
            # Build mencoder command
            #
            mencoder_cmd =[]
            mencoder_cmd.append("mencoder")
            # add export video options  
            if self.__videoFormat == "PAL" :
                coding_command = dictEncoder["PAL"][self._exportType]       
                for mencoder_w in coding_command.split() : mencoder_cmd.append(mencoder_w)
            #finally add the input and output :
            mencoder_cmd.append(self._videoInPath)
            mencoder_cmd.append('-o')
            mencoder_cmd.append(self._videoOutPath)
            
            #
            # launch mencoder command
            #
            self.logger.debug("command :%s"%mencoder_cmd)
            sb_encoder =SP.Popen(mencoder_cmd,stdout=SP.PIPE,stderr=SP.PIPE)

            #
            # check encoding process and finish
            #
            encode_not_finish = True
            res_value = 0
            res_value_old = 0
            while encode_not_finish == True:
        
                # First loop until child is finished
                buffer = []
                ret_code = sb_encoder.poll()
                if type(ret_code) == int :
                    encode_not_finish = False
                while True:
                    # second loop to detect a line
                    # remark : I have no success to use readline or readlines
                    # missing some characters
        
                    # mencoder display info on stdout, 
                    # read one char to no be blocked until eof
                    char = sb_encoder.stdout.readline(1)
                    if not char : break
                    else : 
                        if char == '\r':
                            aLine = string.join( buffer, '' )
                            buffer = []
                            break
                        else:
                            buffer.append(char)
                #extact Frame num
                #print aLine
                #Exemple line : 
                #Pos:  19.0s    475f (99%) 30.68fps Trem:   0min  65mb  A-V:0.000 [28800:0]
                # regeexp for select percent value here : 99.
                # value in parenthis ; with one or digits; select only the number 
                pattern = re.compile("\(\s*([0-9]+)\%\)")
                # get Match_object
                # cf tuto : http://docs.python.org/howto/regex.html#regex-howto
                re_res = pattern.search(aLine)
                if re_res :
                    # result is at first index of groups method
                    # divide by 100 to have a value in range 0 .. 100
                    res_value = re_res.groups()[0]
                    if res_value != res_value_old :
                        # if send message only when percentage value change
                        # avoid sending unuseful message 
                        gobject.idle_add(self._on_progress, float(res_value)/100.0 )
                        res_value_old = res_value
                        # check if abort requested 
                        if self.__abort == True :
                            pid = sb_encoder.pid
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(1.0)
                            # check if is process really dead
                            if not isinstance(sb_encoder.poll(),int) :
                                os.kill(pid,signal.SIGKILL)
                            encode_not_finish = False
            


class lcl_export_video(object) :
    """ Class in charge of managing exports. The class use threads for conversions"""

    _exportType = (EXPORT_DV,EXPORT_DVD,EXPORT_XVID) 
  
    _suffixList =(".dv",".mpeg2",".avi")
  
    def _get_imageDir(self): return self.__imageDir
    def _set_imageDir(self, value): self.__imageDir = value
    def _del_imageDir(self): del self.__imageDir
    imageDir = property(_get_imageDir, _set_imageDir, _del_imageDir, "Image's directory. ")

    def _get_imageList(self): return self.__imageList
    def _set_imageList(self, value): self.__imageList = value
    def _del_imageList(self): del self.__imageList
    imageList = property(_get_imageList, _set_imageList, _del_imageList, "Image's list to encode. This list should be sorted. images are encodede in list order. ")

    def _get_imageInputType(self): return self.__imageInputType
    def _set_imageInputType(self, value): 
        if value in (IMAGE_LIST,IMAGE_DIR) :
            self.__imageInputType = value
        else :
            msg = "[",self.__class__.__name__,"] ",value," not in correct type"
            self.logger.info(msg)
    def _del_imageInputType(self): del self.__imageInputType
    imageInputType = property(_get_imageInputType, _set_imageInputType, _del_imageInputType, "Image's input type  ")

    def _get_VideoName(self): return self.__VideoName
    def _set_VideoName(self, value): self.__VideoName = value
    def _del_VideoName(self): del self.__VideoName
    VideoName = property(_get_VideoName, _set_VideoName, _del_VideoName, "Image's directory. ")

    def _get_videoDir(self): return self.__videoDir
    def _set_videoDir(self, value): self.__videoDir = value
    def _del_videoDir(self): del self.__videoDir
    videoDir = property(_get_videoDir, _set_videoDir, _del_videoDir, "Image's directory. ")

    def _get_framesPerImage(self): return self.__framesPerImage
    def _set_framesPerImage(self, value): self.__framesPerImage = value
    def _del_framesPerImage(self): del self.__framesPerImage
    framesPerImage = property(_get_framesPerImage, _set_framesPerImage, _del_framesPerImage, "Number of frames per image. ")

    def _get_outputFPS(self): return self.__outputFPS
    def _set_outputFPS(self, value): self.__outputFPS = value
    def _del_outputFPS(self): del self.__outputFPS
    outputFPS = property(_get_outputFPS, _set_outputFPS, _del_outputFPS, "Image's directory. ")

    def _get_videoFormat(self): return self.__videoFormat
    def _set_videoFormat(self, value): 
        self.__videoFormat = value
        #set values for PAL format
        if self.__videoFormat == "PAL" :
            self.__ppmtoy4m_opts['F'] = "-F 25:1"     # framerate - see man ppmtoy4m
            self.__ppmtoy4m_opts['A'] = "-A 59:54"    # aspect ratio - see man ppmtoy4m 
    def _del_videoFormat(self): del self.__videoFormat
    videoFormat = property(_get_videoFormat, _set_videoFormat, _del_videoFormat, "Image's directory. ")

    def _get_videoType(self): return self.__videoType
    def _set_videoType(self, value): self.__videoType = value
    def _del_videoType(self): del self.__videoType
    videoType = property(_get_videoType, _set_videoType, _del_videoType, "Image's directory. ")

    def _get_videoAspect(self): return self.__videoAspect
    def _set_videoAspect(self, value): self.__videoAspect = value
    def _del_videoAspect(self): del self.__videoAspect
    videoAspect = property(_get_videoAspect, _set_videoAspect, _del_videoAspect, "Image's directory. ")

    def _get_withSound(self): return self.__withSound
    def _set_withSound(self, value): self.__withSound = value
    def _del_withSound(self): del self.__withSound
    withSound = property(_get_withSound, _set_withSound, _del_withSound, "Image's directory. ")
  
    def _get_export_on_progress(self):
        """ export status is knowed by the status of the last expôpt thread """
        if self._t_encoder  and self._t_encoder.isAlive() == True :
            self._export_on_progress = True
        else :
            self._export_on_progress = False
        return self._export_on_progress
    export_on_progress = property(_get_export_on_progress, None, None, "export status")



    def __init__(self,tmp_dir, export_gui_obj):
        """Init of class"""
        self.__tmpDir = os.path.join(tmp_dir,"export") 
        self.logger = logging.getLogger('luciole')
        self._cleanTmpDir()
    
        self.__imageList = list() # input image list
        self.__imageInputType = IMAGE_LIST    # image type input is imageList by default

        self.__VideoName = "export"
        self.__outputFPS = "25"
        self.__videoFormat = "PAL"
        self.__videoType = "DV"
        self.__videoAspect ="4/3"

        # set ppmtoy4m options
        self.__ppmtoy4m_opts=dict()
        self.__ppmtoy4m_opts['-F'] = "25:1"      # framerate - see man ppmtoy4m
        self.__ppmtoy4m_opts['-A'] = "59:54"     # aspectRatio - see man ppmtoy4m
        self.__ppmtoy4m_opts['-S'] = "420mpeg2"  # subsamplimg chroma mode  - see man ppmtoy4m
        self.__ppmtoy4m_opts['-I'] = "p"         # interlacing mode,progressive, non-interlaced  - see man ppmtoy4m
        self.__ppmtoy4m_opts['-n'] = "0"       # total output frames  - see man ppmtoy4m
        self.__ppmtoy4m_opts['-v'] = "2"       # verbosity  - see man ppmtoy4m
 
        self.__framesPerImage=10           # default value for frame Per image
    
        self.__withSound = False        # no sound by default
    
        self._export_on_progress = False   # export progression
        self._t_yuv = None
        self._t_encoder = None
        self._videopath = None
        self.__imageDir = None
        if self.__videoFormat == "PAL":
            self.__videoRes=(720,576)
        # export gui obj    
        self._export_gui_obj = export_gui_obj


  
    def export(self, export_data ,forceExport=False) :
        """ Export function 
            exportData is a dict with the following items :
            'image_input' = type of image put list or dir (IMAGE_LIST,IMAGE_DIR)
            'image_list' = List of image to convert, each element is an absolute path yo the image
                or
            'image_dir' = dir with all the images to impot : Not implemented
            'export_dir' = the directory where the video will be exported
            'video_name' = the export video name wihout extension
            'export_type' = the type of export (EXPORT_DV,EXPORT_DVD,EXPORT_XVID)
            'fpi' = the frame rate
            """

        
        (VideoExsists,videopath) = self._IsVideoExists(export_data)
        if (    ( VideoExsists == False) or (forceExport == True) 
                and 
                ( videopath != None ) ) : 
            # check tmp dir is clean
            self._cleanTmpDir()
            self._export_on_progress = True

            # initiate queue for comunication between yuv converter and export converter
            self._dataQueue=Queue.Queue()
            self._ResQueue=Queue.Queue()

            #
            # Check input parameters
            #
            self.logger.debug("export Data : %s "%export_data)
            export_is_valid = False
            if export_data.has_key('image_input') :
                self.__imageInputType = export_data['image_input']
                export_is_valid = True

            # check type of input validity
            if( 
                    (export_is_valid == True ) 
                and 
                    ( 
                    (
                    export_data.has_key('image_list') 
                    and
                    export_data['image_input'] == IMAGE_LIST
                    )
                or 
                    (
                    export_data.has_key('image_dir') 
                    and
                    ( export_data['image_input'] == IMAGE_DIR )
            ) )) :
                
                if export_data.has_key('image_list') : self.__imageList = export_data['image_list']
                if export_data.has_key('image_dir') : self.__imageList = export_data['image_dir']
                export_is_valid = True
            else :
                export_is_valid = False

            if  (export_is_valid == True) and (export_data.has_key('fpi')) :
                self.__framesPerImage = int(export_data['fpi'])
                export_is_valid = True
            else :
                export_is_valid = False

            if  (export_is_valid == True) and (export_data.has_key('video_name')) :
                self.__VideoName = export_data['video_name']
                export_is_valid = True
            else :
                export_is_valid = False

            if (export_is_valid == True) and os.path.exists(videopath) :
                try :
                    os.remove(videopath) 
                except OSError,err :
                    videopath = None  
                    export_is_valid = False 
                    lerr =  _('Unable to erase : %s')%err.filename
                    lerr = "%s \n %s"%(lerr,  err.strerror)
                    raise LEXCEP.LucioException, lerr


            if export_is_valid == True :
                # start yuv converter sub process
                self._t_yuv = MyThreadConvertToYuv(self.__imageInputType,self.__imageDir,self.__imageList,self.__ppmtoy4m_opts,self.__framesPerImage,self.__tmpDir,self.__VideoName,self._dataQueue, self._export_gui_obj)
                self._t_yuv.start()
                # start video export encoder subprocess
                self._videopath = videopath
                self._t_encoder = MyExportThread(export_data['export_type'], self._videopath, self._dataQueue, self._export_gui_obj)
                self._t_encoder.start()
            else :
                return (0,videopath)
    
        if ( VideoExsists == True ) :
            return (ERR_FILE_EXIST,videopath)
        else :
            return (0,videopath)

    def cancel_export(self):
        """ Cancel export """
        if self._export_on_progress == True :
            # kill the eport Threads
            if self._t_yuv.isAlive() : self._t_yuv.abort= True 
            if self._t_encoder.isAlive() : self._t_encoder.abort= True 
            #check if process remains 
            while ( self._t_yuv.isAlive() or self._t_encoder.isAlive() ) : 
                time.sleep(0.1)
            # clean temporary files  
            self._cleanTmpDir()
            try :
                os.remove(self._videopath ) 
                self.logger.debug("%s is removed"%self._videopath)
            except OSError,err :
                lerr = _('Unable to erase : %s')%err.filename
                lerr = "%s \n %s"%(lerr,  err.strerror)
                raise LEXCEP.LucioException, lerr



    ################################################################################ 
    # private methods
    ################################################################################ 
    def _cleanTmpDir(self) :
        """ Clean or create  tmp dir if needed"""
        if not os.path.exists(self.__tmpDir) :
            #create it
            try :
                os.makedirs(self.__tmpDir)
            except OSError,err :
                lerr = _('Creation of export folder not possible -- %s'% err.strerror )    
                raise LEXCEP.LucioException, lerr
        else :
            # directory exist, clean it
            list = dircache.listdir( self.__tmpDir)
            for file in list :
                filePath = os.path.join(self.__tmpDir,file)
                try :
                    os.remove(filePath) 
                    self.logger.debug("%s is removed"%filePath)
                except OSError,err :
                    lerr = _('Unable to erase : %s')%err.filename
                    lerr = "%s \n %s"%(lerr,  err.strerror)
                    raise LEXCEP.LucioException, lerr

    def _IsVideoExists(self,export_data):
        """ test if a video path exists """
        exists = False
        video_path = None
        # check export type 
        if export_data.has_key('export_type') and export_data['export_type'] in self._exportType :
            suffix = self._suffixList[export_data['export_type']]
            # check export video name
            if export_data.has_key('video_name') :
                video_name = export_data['video_name']+suffix
                
                # check export dir 
                if not os.path.exists(export_data['export_dir']) :
                    #create it
                    try :
                        MT.mkdirs(export_data['export_dir'])
                    except LEXCEP.LucioException , err :
                        # to robustify : Error handling
                        raise LEXCEP.LucioException, lerr
                video_path = os.path.join(export_data['export_dir'], video_name)
                
                # check if video path exists
                if os.path.exists(video_path) : 
                    exists = True
        return (exists,video_path)



