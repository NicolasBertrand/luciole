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
luciole_controller.py :
   Software controller manage interactions between elements 
"""
import logging 
module_logger = logging.getLogger('luciole')


import luciole_tools as LT
import luciole_project as LP
import luciole_image as LI
import luciole_constants as LCONST
import luciole_exceptions as L_EXCEP
import luciole_conf as LCONF
import luciole_manage_recent as LRECENT
import controller.controller_import as LC_IMPORT
import controller.controller_load_project as LC_LOAD
import luciole_player as LPLAYER

from lcl_gst import lcl_gst_play_sound as LSOUND

import gui as LTK
import time
import threading
import os.path

from gettext import gettext as _

# project type status
(NO_PROJECT,ON_CONFIGURATION,LOADED,MODIFIED) = range(4)




class Luciole_controller(object) :
    __metaclass__ = LT.SingletonType
   
    def __init__(self) :
        """ controller init """
        # init logger
        self.logger = logging.getLogger('luciole')
        self.lcl_program = {}
        
        self._set_program_path()

        # init Luciole conf obj
        self.conf_obj =  LCONF.LucioleConf()
        
        # load theme
        self.conf_obj.load_theme()

        #init gui
        self.gui = LTK.Gui_controller(self)
        
        if  self.conf_obj.conf_options['CaptureTrashDisplay'] == 'yes' :
            self.gui.show_capture_trash_button(True)

        # init project object
        self.project_ctrller =  LP.project_controller()
        
        
        
        # get the recent project list 
        self.recent_project_list = self.conf_obj.conf_options["LastProjects"]
        
        # init the recent project manager
        self.recent_project_obj = LRECENT.luciole_recent(self.recent_project_list, self.gui, self.open_project ,self.conf_obj)   

        # get status bar
        self.status_bar = self.gui.status_progress_bar

        #init sound player
        self.sound_player = LSOUND.Lcl_gst_sound('./sounds/camera.ogg')

        self.acq_obj = None
        self.rush_obj = None
        self.project = None
        self.lucio_player = None
        self._imager_active = True
        self._player_active = False
        self._acquirer_active = False
        self._mixer_active = False

        self.time = 0.0

####################################################################################################
##### PUBLIC  METHODS
####################################################################################################
    def new_project (self) :
        """ action for create a new project """
        
        # if project exist clos it
        if self.project != None : self.close()

        #  launch project assistant
        self.gui.new_project_assistant(self.cb_new_project)
        
         
    def cb_new_project(self,project_data) :
        """ callback to indicate that project assistant is finsihed """
        # 1. copy data in a project_dico object
        project_dico_data = LP.project_dico() 
        for k,v in project_data.iteritems() :
            project_dico_data[k] = project_data[k]
        self.project = project_dico_data

        # 2. create project ( folder structure ,etc ...)
        self.project_ctrller.create(project_dico_data)
        
        # 3. load created project in application
        self.__load_project_in_app()

    def open_project(self,project_path = None) :
        """ open project if param projecet_path is None 
        start a Gui dialog """
        if project_path == None  :
            # if no project_path as paramter open dialog to choose one
            project_path = self.gui.open_project()
        if self.project != None : 
            # if a project is loaded close it
            self.logger.debug("Close a project Before loading a new one") 
            self.close()
       
        # checj if a projetct path was entered
        if project_path != None:
            try :
                (is_valid,self.project) = self.project_ctrller.open(project_path)
            except L_EXCEP.LucioException,err :
                raise L_EXCEP.LucioException,err
        
            # webcam data are not valid
            if is_valid == False :
                msg = _(" Webcam data not valid in project. Please restart webcam detection")
                LTK.Dialog.ErrorMessage(self.gui.window, msg)


            #load project in application
            self.__load_project_in_app()


    def save_project(self):
        """ save the current project """
        self.project_ctrller.save(self.project)
        self.project['is_modified'] = LCONST.PROJECT_NOT_MODIFIED
        self.gui.set_programbar(self.project['project_name'],False)

        # add project to recent list
        self.recent_project_obj.add_project(os.path.join( self.project['project_dir'], self.project['xml_filename'] ))
        
        msg = _('Project %s saved'%self.project['project_name'])
        self.status_bar.display_message(msg)

    def save_as_project(self):
        """ save into a new project"""
        if self.project != None :
            #launch dir chooser
            l_dir = self.gui.dir_chooser_dialog()
            if l_dir != None :
                # launch project save as
                self.project_ctrller.save_as(l_dir,self.project)
               
                self._set_acquirer(False)   # stop acquirer
                self._set_imager(True)      # allow imager    
                self._set_player(False)     # diasallow player
                
                self.project['is_modified'] = LCONST.PROJECT_NOT_MODIFIED
                
                #
                # Minimal actions to destroy a project before loading it 
                #
                self.acq_obj = None
                self.rush_obj = None 
                self.gui.clear_treeviews()

                self.__load_project_in_app()

                msg = _('Project saved as %s'%self.project['project_name'])
                self.status_bar.display_message(msg)

            

    def image_capture(self) :
        """ add an image from capture """
        if self._acquirer_active == True and self.acq_obj.IsStreamingActive == True :
            # play sound 
            self.sound_player.play()
            
            #inactive(sentitivity) snapshot button
            self.gui.is_button_snapshot_sensitive = False

            # streaming is active video capture can be made is active
            self.acq_obj.capture_image() 
           
    def _cb_image_catpure_done(self):
        """ callback to indicate capture is done. Now image can be proccessed into poject"""
        try : 
            # 1. copy it to rush dir and rename it
            l_rush_imagename = self.__move_capture_to_rush_folder() 
        except L_EXCEP.LucioException,err :
            err_msg = " ERROR in image capture :", err
            raise L_EXCEP.LucioException,err_msg
        else : 
            #2.append it to rush and capture obj
            self.__append_image_to_project(l_rush_imagename)
           
        #active(sentitivity) snapshot button
        self.gui.is_button_snapshot_sensitive = True
   
    def image_import(self) :
        """ import images from external source """
        if self.project != None :
            # import imges ony if a project is loaded

            # open filename chooser dialog    
            filenames = self.gui.import_dialog()
            
            if filenames != [] :
                # start import controller
                LC_IMPORT.Controller_import(filenames, self.project, self.gui, self.rush_obj , self)
            else :
                
                msg = _("No files or valid files choosen for image import.")
                LTK.Dialog.ErrorMessage(self.gui.window, msg)
        
        else :
            msg = _("Impossible to import images when no project are loaded.")
            LTK.Dialog.ErrorMessage(self.gui.window, msg)

        
    def image_preview(self,image_obj, tv_type = LCONST.CAPTURE) :
        """ image preview """
        # image preview when image is not in correct foramt not allowed when player is active 
        if  type(image_obj) == LI.Image and self._player_active == False :
            
            if self._mixer_active == True and tv_type == LCONST.CAPTURE :
                # Mix image
                self.acq_obj.Image2Mix = image_obj.path
                
            else :
                # Display image 
                # stop acquisition to display image  
                if self._acquirer_active == True : self._set_acquirer(False)
            
                self.gui.pixbufToDisplay = image_obj.pixbuf_normal
                self._set_imager(True)  # imager display


        
    def export(self) :
        """ manage exports """
        if self.project != None :
            self.gui.export_dialog(self.project)
        else :
            msg = _("Nothing to export. No project loaded")
            LTK.Dialog.ErrorMessage(self.gui.window, msg)
    
    def export_tool(self) :
        """ Manage tool exports """
        if self.project != None :
            self.gui.export_tool_dialog(self.project)
        else :
            msg = _("Nothing to export. No project loaded")
            LTK.Dialog.ErrorMessage(self.gui.window, msg)
 
    def play(self,index_chrono) :
        """ play video """
        # Test if project exists
        if self.project != None :
            # test if images are availbale in chron widget zone
            if self.project['chrono_images'] != [] :
                try :
                    # Initialize player player 
                    self.lucio_player = LPLAYER.luciole_player(
                                            self.gui.previsuDrawingArea,
                                            self.cb_player_eos,
                                            os.path.join(self.project['project_dir'], LCONST.TMP_DIR)
                                            )
                except L_EXCEP.LucioException,err :
                    # nbd@grape specify action to do err message or raise exception ?
                    err_msg = "Imposible to initialize player.\n", err
                    raise L_EXCEP.LucioException,err_msg
                    
                else :
                    # disable imager and acquirer
                    self._set_imager(False)
                    self._set_acquirer(False)

                    # Init OK play can be started. 
                    player_data = {}
                    # creation of image list  In  chrono_images the image names are listed, but the full path is need by export module
                    # so each file is concated with abasolute pathname to rush_dir
                    player_data['image_list'] = [ os.path.join(
                                                            self.project['project_dir'], self.project['rush_dir'],image_name
                                                            ) for image_name in self.project['chrono_images'] ]

                    #Slice with index_monatge to remove all images before selection
                    player_data['image_list'] =  player_data['image_list'][index_chrono:]
                    player_data['fpi'] = self.project['fpi']
                    self.lucio_player.start_play(player_data)
                
                    self._set_player(True)  # player is active
            else :
                # nbd@grape to transform as error message
                msg =  _("Can not play animantion : No image on montage view ")
                LTK.Dialog.ErrorMessage(self.gui.window, msg)

                # set play button as deacivated
                self.gui.update_play_button(is_active = False)


        else :
            # nbd@grape to transform as error message
            masg = _("Can not play animantion : No project loaded ")
            LTK.Dialog.ErrorMessage(self.gui.window, msg)
            
            # set play button as deacivated
            self.gui.update_play_button(is_active = False)
    
    def cb_player_eos(self) :
        """ callback for end of stream signal from player """
        # set play button as deacivated
        self.gui.update_play_button(is_active = False)
        
        # set player as inactive 
        self._set_player(False)
        # allow imager activity
        self._set_imager(True) 

        # destroy player object
        self.lucio_player = None
    
    def stop(self) :
        """ Stop video playing """
        if self.lucio_player != None :
            self.lucio_player.stop_play()
        # set player as inactive 
        self._set_player(False)
        # allow imager activity
        self._set_imager(True) 

    def project_change(self,project_key,data) :
        """ function called to update a project. usualy called by gui to indicate change 
        on capture or chrono list """
        if self.project != None :
            if self.project.has_key(project_key) :
                self.project[project_key] = data
                self.project['is_modified'] = LCONST.PROJECT_MODIFIED
                self.gui.set_programbar(self.project['project_name'],True)
            else :
                #raise Error/Exception 
                err =  "key %s not in project "%project_key 
                raise L_EXCEP.LucioException,err

        else :
            # raise Error/Exception 
            err = " Project not loaded "
            raise L_EXCEP.LucioException,err

    def close(self) :
        """ Close current project """
        if self.project != None :
            # project exist
            if self.project['is_modified'] == LCONST.PROJECT_MODIFIED :
                # nbd@grape  : ask for save if save set status as loaded
                l_bRes = LTK.Dialog.QuestionMessage(self.gui.window, _('Save Project before closing'))
                if l_bRes == True : 
                    self.save_project()
            
            self._set_acquirer(False)   # stop acquirer
            self._set_imager(True)      # allow imager    
            self._set_player(False)     # diasallow player
   
            # 1. clear acq_obj
            self.acq_obj = None
                
            # 2. Preview widget deactivate
            self.gui.button_preview_deactivate()
                
            # 3. Clear widget treeviews
            self.gui.clear_treeviews()

            # 4. Clear rush list
            self.rush_obj = None

            # 5. Clear program name bar
            self.gui.set_programbar('',False)
                
            # 6. show open/new project widgets
            self.gui.project_open_widgets()
            
            msg = _('Project %s is closed'%self.project['project_name'])
            self.status_bar.display_message(msg)

            # 7.. Remove project obj
            self.project = None


    def start_acquisition(self) :
        """ start the acquisition """

        if self.project != None :
            #a project is loaded
            # test if player is not active
            if self._player_active == False : 
                if self.acq_obj != None :
                    # acqusition is not active so it can be started
                    if self._acquirer_active == False :
                        self.acq_obj.start_acquisition()
                        self.gui.acquisition_widget_show()
                        
                        # clear message status bar
                        self.status_bar.display_message(_('Acquiring'))
                        
                        self._set_acquirer(True)    # set acquirer as active
                        self._set_imager(False)     # set imager  as inactive 
                        self._set_player(False)     # set player as inactive 
                    else :
                        #acquisition yet started
                        self.logger.debug("acquisition Yet started : Not expected event ")
                        # State not normal - stop acquirer
                        self._set_acquirer(False)   # stop acquirer
                        self._set_imager(True)      # allow imager    
                        self._set_player(False)     # diasallow player
                else :
                    # check if ack obj is None due to DIGICAM hardware 
                    if self.project['hardtype'] == LCONST.DIGICAM :
                        self.gui.acquisition_widget_hide()
                        self._set_acquirer(False)   # stop acquirer
                        msg =  _("No acquisition available. Use 'import image' button to load images in project.")
                        LTK.Dialog.ErrorMessage(self.gui.window, msg)

            else :
                # deactivate acqusition button acquisition not allowed when palyer is active
                self.gui.acquisition_widget_hide()
                self._set_acquirer(False)   # stop acquirer
                

        else :
            # deactivate acqusitionn button 
            self.gui.acquisition_widget_hide()
            msg =  _(' Can not start acquisition when no project are loaded.')
            LTK.Dialog.ErrorMessage(self.gui.window, msg)
            #robustness
            self._set_acquirer(False)   # stop acquirer
            self._set_imager(True)      # allow imager    
            self._set_player(False)     # diasallow player

    def _cb_acq_error(self,message) :
        """ callback for detection of acquistion errors """
        msg = _("Acquisition error. %s"%message)
        #LTK.Dialog.ErrorMessage(None, msg)
        self.status_bar.display_message(msg)

        self._set_acquirer(False)   # stop acquirer
        self._set_imager(True)      # allow imager    
        self._set_player(False)     # diasallow player robsutness


    def stop_acquisition(self) :
        """ stop the acquisition """
        # acqusition active so it can be stoped
        # check also used to avoid loopback problem with the toggle button of acquisition
        if self._acquirer_active == True :
            self.status_bar.display_message(_('No Acquistion'))
            self._set_acquirer(False)   # deactivate acquirer 
            self._set_imager(True)      # allow imager 
            self._set_player(False)     # Player not activated (robsutness)
    
    def move_to_chrono(self) :
        """ move selected images in capture view to Montage view """
        # get images to move from capture widget
        images_name = self.gui._tv_capture.images_to_move()
        # append this images in montage widget
        images_obj = [ self.rush_obj.get_image(image) for image in images_name ]
        for image in images_obj :
            self.gui._tv_montage.append_image(image)

    def mixer_on(self) :
        """ Request for mixer activation """
        # check some conidtions :
        # acq object is active
        # mixer is not yet active 
        if ( (self._acquirer_active == True)
            and
                (self._mixer_active == False)
            and
                (self.acq_obj.IsStreamingActive == True)
            and
                (self.acq_obj.IsOnionSkinActive == False )
            ) :
            # active mixer
            self.acq_obj.active_onion_skin()

            # show alpha bar 
            self.gui.alpha_show()

            #indicate mixer active 
            self._set_mixer(True)


    def mixer_off(self) :
        """ Request for mixer desactivation """
        # check some conditions 
        # acquisition acive and running ok
        if (    (self._acquirer_active == True)
            and
                (self._mixer_active == True)
            and
                (self.acq_obj.IsStreamingActive == True)
            and
                (self.acq_obj.IsOnionSkinActive == True )
            ) :
             # desactive mixer
            self.acq_obj.deactive_onion_skin()

            # show alpha bar 
            self.gui.alpha_hide()

            #indicate mixer active 
            self._set_mixer(False)
    
    def mixer_alpha_changed(self,alpha) :
        """ update value of alpha """
        # check some conditions 
        # acquisition acive and running ok
        if (    (self._acquirer_active == True)
            and
                (self._mixer_active == True)
            and
                (self.acq_obj.IsStreamingActive == True)
            and
                (self.acq_obj.IsOnionSkinActive == True )
            ) :
            # check alpha range
            if alpha < 0.0 : alpha = 0.0
            if alpha > 1.0 : alpha = 1.0
            # update alph on acquiistion object
            self.acq_obj.set_alpha_onion_skin(alpha)

    def update_fpi(self,fpi) : 
        """ update frame per image (fpi) of projetct """
        if self.project != None :
            # update fpi on projetct
            self.project_change('fpi',fpi)

    def quit(self) :
        """ quit application """
        
        if self.project != None :
            # project exist
            if self.project['is_modified'] == LCONST.PROJECT_MODIFIED :
                # nbd@grape  : ask for save if save set status as loaded
                l_bRes = LTK.Dialog.QuestionMessage(self.gui.window, _('Project modified. Save project before exit ?'))
                if l_bRes == True : 
                    self.save_project()
                    self.gui.quit()
                elif l_bRes == False :
                    self.gui.quit()
            else :
                self.gui.quit()
        else :
            self.gui.quit()
        
    def project_properties(self) :
        """ request Display of project properties """ 
        if self.project != None :
            if self._acquirer_active == True :
                self.status_bar.display_message(_('No Acquistion'))
                self._set_acquirer(False)   # deactivate acquirer 
                self._set_imager(True)      # allow imager 
                self._set_player(False)     # Player not activated (robsutness)
 
            self.gui.display_project_properties(self.project,self._cb_project_change)
             
       
    def _cb_project_change(self,key,key_webcam= None, data =None) :
        """ Project change callback """ 
        # webcam_data field of project dictionaty is a dictionaty
        # Test if webcam data change key
        if key == 'webcam_data':
            # make a local copy of webcam_data
            webcam_dict = self.project['webcam_data']
            #test if webcam dict key exists
            if webcam_dict.has_key(key_webcam) :
                # update webcal key and call project change
                webcam_dict[key_webcam] = data
                self.project_change('webcam_data',webcam_dict)
                
                # stop acquirer
                self._set_acquirer(False)   # stop acquirer
                self._set_imager(True)      # allow imager    
                self._set_player(False)     # diasallow player robsutness

    def luciole_preferences(self) :
        """ Display Luciole prefrences """
        self.gui.display_preferences_dialog(self.conf_obj.conf_options,self._cb_preferences_change)

    def _cb_preferences_change(self,modif_options):
        """ Called after preference change """
        # get the intersecttion of modified dict with conf dict to get the differences
        intersect = []
        for item in self.conf_obj.conf_options.keys():
            #check key
            if modif_options.has_key(item):
                # check if value different
                if self.conf_obj.conf_options[item] != modif_options[item] :
                    intersect.append(item)
        for item in intersect :
            if item == 'Theme' :
                self.conf_obj.conf_options[item] =  modif_options[item]
                msg = _('Please restart Luciole to take into account the new theme ')
                self.status_bar.display_message(msg)
            
            if item == 'CaptureTrashDisplay' :
                if modif_options[item] == 'yes' :
                    # show the trash on capture view
                    self.gui.show_capture_trash_button(True)
                    self.conf_obj.conf_options[item] =  modif_options[item]
                else :
                    # hide the trash on capture view
                    self.gui.show_capture_trash_button(False)
                    self.conf_obj.conf_options[item] = 'no'
            # save modofied options to file
            self.conf_obj.save_options()
                

        
####################################################################################################
##### PRIVATE  METHODS
####################################################################################################
    def __load_project_in_app(self) :
        """ load treview, pepare acquiistion rush list , etc .."""
        self.time = time.time()
        if self.project != None :
            self.logger.debug("---------------------------------------------------------------------")
            self.logger.debug("Luciole_controller project info: ")
            self.logger.debug("---------------------------------------------------------------------")
            for k,v in self.project.iteritems() :
                self.logger.debug("**%s** : %s "%(k,v))
            self.logger.debug( "---------------------------------------------------------------------")

            # Initilaisation of rush ogbj is threaded because its take a while (generation of images pixbufs)
            # When rush load is finish : __on_rush_finish is called 
           
            LC_LOAD.Controller_load_project(self.project, self.gui, self.__cb_project_load_finsih, self._cb_acq_error, self._cb_image_catpure_done)

    def __cb_project_load_finsih(self,rush_obj,acq_obj) :
        if (rush_obj != None)  : 
        
            self.rush_obj = rush_obj
            self.acq_obj = acq_obj
        
            # add project to recent list
            self.recent_project_obj.add_project(os.path.join( self.project['project_dir'], self.project['xml_filename'] ))
        
            # set project as not modified 
            self.project['is_modified'] = LCONST.PROJECT_NOT_MODIFIED

            self.logger.debug('load time = %s'%( time.time() - self.time ))
        else :
            msg =  _("Failed to load project ")
            LTK.Dialog.ErrorMessage(self.gui.window, msg)


    def __move_capture_to_rush_folder(self):
        """ move acquired  image to rush dir : 
            1. move image to tmp dir.
            2. resize it.
            3. move it to rush image dir """
        # get acquired image name
        l_acq_image = self.acq_obj.Image2save

        # build temp impage path
        l_temp_dir =  os.path.join(self.project['project_dir'], 'tmp')
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
            LT.movef(l_acq_image,l_ac_image_temp)

            # 2. resize image result is in l_ac_image_temp_rz
            l_rz_obj = LI.Image_resize(l_ac_image_temp,l_ac_image_temp_rz )
            l_rz_obj.convert()
            
            # 3. move resized image to rush dire 
            LT.movef(l_ac_image_temp_rz,l_rush_image)
        
        except L_EXCEP.LucioException,err :
            raise L_EXCEP.LucioException,err
            l_basename = None  
        return l_basename
    
    
    def __append_image_to_project(self, p_image_name):
        """ append an imge to the project. 
        the parameter p_image_name is the image name . Image is supposed to be in rush dir"""
        # 1. append image to rush list
        self.rush_obj.append(p_image_name)
        # indicate project change (rush list)
        self.project_change('rush_images',self.rush_obj.dump_image_name())

             
        # 2. append image object to capture list
        l_rush_image = self.rush_obj.get_image(p_image_name)
        
        self.gui.append_capture(l_rush_image)  

        
        # always update the image 2 mix, even if mixer is not active
        # used to memorize the last capture 
 
        self.acq_obj.Image2Mix = l_rush_image.path 
    
     
    def _stop_acquisition(self):
        """ private stop acquisition method """
        if self.acq_obj != None :
            # stop gstreamer acquisition
            self.acq_obj.stop_acquisition()
            # infor gui to close/hide the acqsuisition widgets
            self.gui.acquisition_widget_hide()

    def _set_imager(self,is_active = False):
        """ """
        # test type and change only on transition 
        if (type(is_active) == bool) and (self._imager_active != is_active) :
            self._imager_active = is_active
            self.gui.view_image = self._imager_active
            if is_active == False :
                # clear the displayed buffer .
                self.gui.pixbufToDisplay = None

    def _set_player(self,is_active = False):
        """ """
        # test type and change only on transition 
        if (type(is_active) == bool) and (self._player_active != is_active) :
             self._player_active = is_active

    def _set_acquirer(self,is_active = False):
        """ """
        # test type and change only on transition 
        if (type(is_active) == bool) and (self._acquirer_active != is_active) :
            self._acquirer_active = is_active
            if self._acquirer_active == False :
                # stop acquisition 
                self._stop_acquisition()
                
    def _set_mixer(self,is_active = False):
        """ """
        # test type and change only on transition 
        if (type(is_active) == bool) and (self._mixer_active != is_active) :
            self._mixer_active = is_active

    def _set_program_path(self) :
        """
         set some program path usefull for other luciole objects
        """
        
        # get execution path
        BASE_DIR = os.path.realpath('.')
        self.lcl_program['BASE_DIR'] = BASE_DIR
        self.lcl_program['THEMES_DIR'] = os.path.join(BASE_DIR,'themes')
        self.lcl_program['UI_DIR'] = os.path.join(BASE_DIR,'ui')
        self.lcl_program['PO_DIR'] = os.path.join(BASE_DIR,'po')



