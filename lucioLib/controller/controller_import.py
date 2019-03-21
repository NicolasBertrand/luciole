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

import os.path
import gobject
import threading
import Queue

from .. import luciole_tools as LT
from .. import luciole_image as LI
from .. import luciole_constants as LCONST
from .. import luciole_exceptions as L_EXCEP

from gettext import gettext as _

class Import_thread(threading.Thread):
    """ this thread is used to load the rush images, its take a while so this action is threaded """
    def __init__(self,filenames,project,rush_obj,queue) :
        """ initilise thread 
        """
        # init thread
        super(Import_thread, self).__init__()
        
        self.filenames = filenames
        self.project = project
        self.rush_obj = rush_obj
        self.queue = queue
        
    def run(self) :
        """ run thread """
        # create rush list object
        image_objs = []
        for (index,filename) in enumerate(self.filenames) :
            # copy image to rush folder and resize it
            try : 
                l_rush_image_name = self.__copy_import_to_rush_folder(filename)
            except L_EXCEP.LucioException,err :
                image = None
                lerr =  "ERROR  on import image : ",err
                raise L_EXCEP.LucioException,lerr
            else :
                # append image to rush list : usage of append_threaded special for thread execution  
                image_objs.append(self.rush_obj.append_threaded(l_rush_image_name))
            
            
            # indicate progression on queue
            qmsg = dict()
            qmsg['progression'] = (index + 1.0)/len(self.filenames) 
            self.queue.put(qmsg,block=False)

        
        # indicate finsih  on queue and send rush_obj
        # send finsih message on queueu
        qmsg = dict()
        qmsg['finish'] = image_objs
        self.queue.put(qmsg,block=False)

    
    def __copy_import_to_rush_folder(self,p_image_path):
        """ copy imported image to rush dir : 
            1. copy image to tmp dir.
            2. resize it.
            3. move it to rush image dir """

        # build temp impage path
        l_temp_dir =  os.path.join(self.project['project_dir'], LCONST.TMP_DIR)
        # copy name
        l_ac_image_temp = os.path.join(l_temp_dir,LCONST.ACQUIRED_IMAGE_NAME)
        # resized copy name
        l_ac_image_temp_rz = os.path.join(l_temp_dir,LCONST.ACQUIRED_IMAGE_NAME_RZ)

        # build rush image name
        l_basename = LCONST.RUSH_FILENAME_TPL%self.rush_obj.rush_index
        l_rush_image = os.path.join(self.project['project_dir'], self.project['rush_dir'])
        l_rush_image = os.path.join(l_rush_image, l_basename)

        try :  
            # 1. move image acquired image to tmp dir
            LT.copyf(p_image_path,l_ac_image_temp)

            # 2. resize image result is in l_ac_image_temp_rz
            l_rz_obj = LI.Image_resize(l_ac_image_temp,l_ac_image_temp_rz )
            l_rz_obj.convert()
            
            # 3. move resized image to rush dire 
            LT.movef(l_ac_image_temp_rz,l_rush_image)
        
        except L_EXCEP.LucioException,err :
            raise L_EXCEP.LucioException,err
            l_basename = None  
        return l_basename
 

class Controller_import(object):
    """ This class is used to manage the import of image in project .
        The class use a Thread for importing images (it can takes) long.
        The thread and this class communicate via a queue. Information on queue are progression and finish.
        The queue is checked cyclicly via a gobject timer
    """
    _TIMEOUT = 50        # 50 ms timer

    def __init__(self, filenames, project, gui, rush_obj, ctrl_obj ) : 
        """ Init Thread, init gobject timer and clear progressbar """
        self.filenames = filenames
        self.project = project
        self.gui = gui
        self.rush_obj = rush_obj
        
        self.ctrl_obj = ctrl_obj 

        self._progress_bar_widget = self.gui.status_progress_bar
        
        # initialize thread
        self.queue = Queue.Queue()
        self.t_rush = Import_thread(self.filenames, self.project, self.rush_obj, self.queue)
        
        #clear progressbar
        self._progress_bar_clear()
        
        # start Thread
        self.t_rush.start() 
        
        # start timer 
        gobject.timeout_add(self._TIMEOUT,self._on_timeout)
        
            

    def _on_timeout(self) :
        """ 
        function call peridodically by gobject timeout . The periodicity is ensured 
        by returning True. When False is return timer is stop  
        the goal of the time is too check the queue 
        """ 
        rearm_timer = True
        try:
            qmsg = self.queue.get(block = False)
        except Queue.Empty :
            pass
        else :
            if qmsg.has_key('progression') : 
                self._progress_bar_on_progress(qmsg['progression'])
            if qmsg.has_key('finish') :
                # finisg project load ( Non threaded section )
                self._on_import_finish(qmsg['finish'])
                
                #update as finsih staus/progress bard
                self._progress_bar_complete()
                # stop the timer
                rearm_timer = False
        
        return rearm_timer
            
    def _progress_bar_clear(self):
        """ Clear progress bar  """
        msg = _('Import started')
        self._progress_bar_widget.start(msg)

    def _progress_bar_complete(self):
        """ Progress bar full : Import done   """
        msg = _('All images imported')
        # use of idle_add because gui update not in the same thread
        self._progress_bar_widget.stop(msg)

    def _progress_bar_on_progress(self,ratio = None):
        """ indicate that import  is going on """
        msg = _('Importing images ...')
        self._progress_bar_widget.on_progress(msg,ratio)
 

    def _on_import_finish(self, image_objs = []) :
        """ callback for import finish """
        if image_objs != [] :
            self.ctrl_obj.project_change('rush_images',self.rush_obj.dump_image_name())
            # Not to be don in thread : interacts with gui
            for image_obj in image_objs :
                self.gui.append_capture(image_obj)  
   
    


