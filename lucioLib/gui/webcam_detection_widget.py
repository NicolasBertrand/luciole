#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vi:si:ai:et:sw=4:sts=4:ts=4
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
"""
    webcam detetction widget
"""
import gtk
import gobject
import threading
import time

from gettext import gettext as _
from .. import lucioWebCamDetect as M_WEBCAM

class Webcam_detection_thread_worker(threading.Thread):
    """  Thread in charge of calling the webcam detection """
        
    def __init__(self,on_finish) :
        """ init thread for webcam detection """ 
        super(Webcam_detection_thread_worker, self).__init__()
        self._on_finish = on_finish

    def run (self) :
        """ run thread for webcam detection """
        WebCamObj = M_WEBCAM.luciole_webcam_detection()
        nb_webcam = WebCamObj.detect_webcam()
        self._on_finish(nb_webcam, WebCamObj )


class Webcam_detection_thread(object):
    """ Manages webcam detection : comunication between gui and webcam
    detection thread 
    """
    _TIMEOUT = 100 
    
    def __init__(self,progress_bar_widget,on_finish) :
        """ init thread communication : finsih status and progress bar """ 
        self._is_worker_finished = False
        self._webcam_obj = None 
        self._progress_bar_widget = progress_bar_widget
        self._on_finish = on_finish
         
        # initialize thread
        t_worker = Webcam_detection_thread_worker(self._worker_finished)

        #clear progressbar
        self._progress_bar_clear()
        
        # start Thread
        t_worker.start()
        
        # start timer 
        gobject.timeout_add(self._TIMEOUT,self._on_timeout)

   
    def _worker_finished(self, nb_webcam, webcam_obj) :
        """ callback to indicate that thread is finished"""
        self._is_worker_finished = True
        if nb_webcam > 0 : 
            self._webcam_obj = webcam_obj

    def _on_timeout(self) :
        """ Call cyclicly to check worker thread job """
        rearm_timer = True

        if self._is_worker_finished == False  :
            self._progress_bar_on_progress()
        else : 
            # detection is finished 
            self._progress_bar_complete()
            rearm_timer = False     #stop timer 
            self._on_finish(self._webcam_obj)   # finish callback 
        return rearm_timer

    def _progress_bar_clear(self):
        """ Clear progress bar  """
        self._progress_bar_widget.set_fraction(0.0)
        self._progress_bar_widget.set_text(_('Please wait for webcam detection'))

    def _progress_bar_complete(self):
        """ Progress bar full : detecyion complete  """
        self._progress_bar_widget.set_fraction(1.0)
        self._progress_bar_widget.set_text(_('Webcam detection done'))
    
    def _progress_bar_on_progress(self):
        """ indicate that detection  is going on """
        self._progress_bar_widget.pulse()

class  Webcam_detection_Box(gtk.VBox) :
    """ Assistant page for webcam detection """
    
    def __init__(self, project_data, *args ) :
        super(Webcam_detection_Box,self).__init__(*args )
        self.set_name('Page_webcam')
        self.project_data = project_data
        
        #
        # set default values
        #
        self.project_data['webcam_data'] = dict()
        
        #
        # Initailize widgets for webcam detection page 
        #
        
        # Progress bar widget
        self.progressbar =  gtk.ProgressBar()
        self.progressbar.set_size_request(width =400, height = 50)
        self.pack_start(    child = self.progressbar, 
                            expand=False, 
                            fill=False, 
                            padding=3)

        # label to indicate result of detection 
        self.label = gtk.Label('')
        self.pack_start(    child = self.label, 
                            expand=False, 
                            fill=False, 
                            padding=3)


        # Hbox used to list the detecteds webcams
        HBox = gtk.HBox()
        if HBox :
            self.VBox = gtk.VBox()
            
            HBox.add(self.VBox)
        self.pack_start(    child = HBox, 
                            expand = True, 
                            fill = True , 
                            padding = 3)

   

    def prepare_webcam_detection(self) :
        """ prepare assistant page for the webcam detection page """
        
        # Hide label  for webcam status 
        self.label.hide()

        # launch webcam detection thread
        t_webcam = Webcam_detection_thread(self.progressbar,self._on_webcam_detect_complete)
        
    def _on_webcam_detect_complete(self,webcam_obj) :
        """ callback , executed when webcam detection is complete 
            Return the number of detected webcams"""
        status = 0

        if webcam_obj != None and webcam_obj.webcam_devices != None:
            vbox = self.VBox
            # firt clean childs on the vbox widget
            for my_child in vbox.get_children() : vbox.remove(my_child)
            # loop on detected webcams 
            RadioButton = None

            for (webcam_index, webcam ) in enumerate(webcam_obj.webcam_devices) :
                RadioButton = gtk.RadioButton(group=RadioButton, label= webcam["name"] )
                vbox.pack_start(RadioButton)
                RadioButton.show()
                
                #connect event 
                RadioButton.connect("clicked",self.on_webcam_radio_button_clicked,webcam_index,webcam_obj )
                
                # First set 
                if webcam_index == 0 :
                    # select by default. 
                    self.project_data['webcam_data'] = webcam_obj.get_gst_best_input(webcam_index) 
            self.label.set_text(_('Detected webcam(s)'))
            status = len(webcam_obj.webcam_devices)
        else :
            self.project_data['webcam_data'] = None
            self.label.set_text(_('No webcam detected'))
        self.label.show()
        return status
    
    def on_webcam_radio_button_clicked(self,widget,webcam_index,webcam_obj):
        """ callback for webcam rasdio button.
        Save info on selected webcam 
        """
        # when a webcam is selected select webcam data
        self.project_data['webcam_data'] = webcam_obj.get_gst_best_input(webcam_index) 

        


