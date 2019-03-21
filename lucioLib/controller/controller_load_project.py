#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vi:si:ai:et:sw=4:sts=4:ts=4
#
#
# Copyright Nicolas Bertrand (nico@inattendu.org), 2009
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
import os
import gobject
import threading
import Queue

from .. import luciole_tools as LT
from .. import luciole_image as LI
from .. import luciole_acquisition as LACQ
from .. import luciole_constants as LCONST

from gettext import gettext as _

class rush_loader_thread(threading.Thread):
    """ this thread is used to load the rush images, its take a while so this action is threaded """
    def __init__(self,project,queue) :
        """ initilise thread 
            progress_bar : the status/progres bar for diplay info about project load 
            cb_on_finish : The callback function when thread is finished, the rush_obj is returned by thread 
            project : the project dictionary
        """
        # init thread
        super(rush_loader_thread, self).__init__()
        
        self.project = project
        self.queue = queue
        
    def run(self) :
        """ run thread """
        # create rush list object
        rush_dir = os.path.join(self.project['project_dir'],self.project['rush_dir'])
        rush_obj = LI.Rush_images(rush_dir,self.project['rush_images'],self._cb_progression)
        
        # indicate finsih  on queue and send rush_obj
        # send finsih message on queueu
        qmsg = dict()
        qmsg['finish'] = rush_obj
        self.queue.put(qmsg,block=False)

    
    def _cb_progression(self,ratio = None):
        """ indicate progression of rsuh object init """
        # put in on queue
        qmsg = dict()
        qmsg['progression'] = ratio
        self.queue.put(qmsg,block=False)


class Controller_load_project(object):
    """ This class is used to manage the load of a project in application.
        The class use a Thread for launch rush object init. (it can takes) long.
        The thread and this class communicate vai a queue. Information on queue are progression and finish.
        The queue is checked cyclicly via a gobject timer
    """
    _TIMEOUT = 10        # 10 ms timer

    def __init__(self, project, gui, cb_on_finish, cb_acq_error, cb_image_capture_done) : 
        """ Init Thread, init gobject timer and clear progressbar """
        self.project = project
        self.gui = gui
        self._cb_on_finish = cb_on_finish 
        self._cb_acq_error = cb_acq_error
        self._cb_image_capture_done = cb_image_capture_done

        self._progress_bar_widget = self.gui.status_progress_bar
        
        # initialize thread
        self.queue = Queue.Queue()
        self.t_rush = rush_loader_thread(project,self.queue)
        
        #clear progressbar
        self._progress_bar_clear()
        
        # start Thread
        self.t_rush.start() 
        
        # start timer 
        gobject.timeout_add(self._TIMEOUT,self._on_timeout)
        
        #print " Controller load : ", threading.currentThread()
            

    def _on_timeout(self) :
        """ 
        function call peridodically by gobject timeout . The periodicity is ensured 
        by returning True. When False is return timer is stop  
        the goal of the time is too check the queue 
        """ 
        #print " on timeout : ", threading.currentThread()
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
                self._on_rush_finish(qmsg['finish'])
                
                #update as finsih staus/progress bard
                self._progress_bar_complete()
                # stop the timer
                rearm_timer = False
        
        return rearm_timer
            
    def _progress_bar_clear(self):
        """ Clear progress bar  """
        msg = _('Project Load started')
        self._progress_bar_widget.start(msg)

    def _progress_bar_complete(self):
        """ Progress bar full : Project loaded  """
        msg = _( 'Project %s is loaded')%self.project['project_name'] 
        # use of idle_add because gui update not in the same thread
        self._progress_bar_widget.stop(msg)

    def _progress_bar_on_progress(self,ratio = None):
        """ indicate that detection  is going on """
        msg = _('Project %s is loading')%self.project['project_name']
        self._progress_bar_widget.on_progress(msg,ratio)
 

    def _on_rush_finish(self, rush_obj):
        """ Finish the load after rush generation """

        acq_obj = None
        if rush_obj != None :
            # load treeviews
            self.gui.load_treeviews(rush_obj, self.project['capture_images'], self.project['chrono_images']) 
             
            # update acquisition object
            if self.project['hardtype'] == LCONST.DIGICAM :
                # No acquisition for digital camera
                acq_obj = None
            elif self.project['hardtype'] == LCONST.WEBCAM :
                # acquisition for WEBCAM
                acq_obj =  LACQ.luciole_acquisition_webcam(
                                        self.gui.display,
                                        data = self.project['webcam_data'],
                                        project_dir = self.project['project_dir'],
                                        cb_error = self._cb_acq_error,
                                        cb_capture_done = self._cb_image_capture_done)
            else :
                # default acquisition load i.e. DVCAM
                acq_obj =  LACQ.luciole_acquisition(
                                        self.gui.display,
                                        False,
                                        self.project['hardtype'],
                                        project_dir = self.project['project_dir'],
                                        cb_error = self._cb_acq_error,
                                        cb_capture_done = self._cb_image_capture_done)


            
            # for mixer initialisation set image to miw with the last image of the capture view. only if capture image is not empty
            if len( self.project['capture_images'] ) > 0 :
                l_last_image_path = os.path.join(self.project['project_dir'],self.project['rush_dir'],self.project['capture_images'][-1])
                if os.path.exists(l_last_image_path) and acq_obj != None : acq_obj.Image2Mix = l_last_image_path
            
            #  update fpi on gui and show it
            self.gui.update_fpi(int(self.project['fpi']))
            
            # show project  acquisition widgets
            self.gui.project_acquistion_widgets()

            # update project name on Main bar
            self.gui.set_programbar(self.project['project_name'],False)

        # call back to indicate finish at controller
        self._cb_on_finish(rush_obj, acq_obj)
    
    


