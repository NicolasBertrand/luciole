#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
#
#
# copyright nicolas bertrand (nico@inattendu.org), 2009-2010
#
# this file is part of luciole.
#
#    luciole is free software: you can redistribute it and/or modify
#    it under the terms of the gnu general public license as published by
#    the free software foundation, either version 3 of the license, or
#    (at your option) any later version.
#
#    luciole is distributed in the hope that it will be useful,
#    but without any warranty; without even the implied warranty of
#    merchantability or fitness for a particular purpose.  see the
#    gnu general public license for more details.
#
#    you should have received a copy of the gnu general public license
#    along with luciole.  if not, see <http://www.gnu.org/licenses/>.
#
#
import sys
import pygtk
import gtk
import gtk.glade
import gobject
import gnome.ui   
import glob
import os.path
import locale
import gettext

import time
import gc

import logging 
module_logger = logging.getLogger('luciole')

import luciole_drawaera as GLD
import montage_tree as GMT
import capture_tree as GCAT
import assistant_new_project as GLA
import dialog as GDIALOG
import open_project as GOF
import luciole_export_window as GEXPORT
import luciole_export_tool_window as GEXPORT_TOOL

import open_project_widget as GOPEN
import dialog_project_properties as GDIALOG_PROJ
import dialog_preferences as GPREF

from .. import luciole_constants as LCONST
from .. import luciole_exceptions as LEXCEP

import _version

#  nbd@grape : APP NAME place to change

APP_NAME = "luciole"
_ = gettext.gettext

""" 
    gui_controller.py 
    main file for gui management 
    gui init and call backs
"""
class Gui_status_controller(object) :

    def __init__(self, status_bar, progress_bar=None) :
        """ init gui status controller """
        self._status_bar = status_bar
        self._context_id = self._status_bar.get_context_id("Statusbar example")
        self._progress_bar = progress_bar

    def on_progress(self,msg,ratio) :
        """ update status and progress bar """
        self._status_bar.push(self._context_id, msg)
        if self._progress_bar != None :
            # if a ratio is given update progress bar with set fraction if not update with just a pulse
            if ratio != None :
                self._progress_bar.set_fraction(ratio)
            else :
                self._progress_bar.pulse()


    def start(self,msg) :
        """ Start progress/status bar """
        self._status_bar.push(self._context_id, msg)
        if self._progress_bar != None :
            self._progress_bar.show()
            self._progress_bar.set_fraction(0.0)

    def stop(self,msg) :
        """ Stop progress/status bar """
        self._status_bar.push(self._context_id, msg)
        if self._progress_bar != None :
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.hide()

    def display_message(self,msg) :
        """ display a message on status bar """
        self._status_bar.push(self._context_id, msg)
           
    def clear_message(self) :
        """ clear a message on status bar """
        self._status_bar.pop(self._context_id)
        
        
    


class Gui_controller(object):
    """ class handling interface with GUI/glade """
    

    #
    # constants 
    #
    
    # UI file specification
    GUI_FILE = "luciole.glade"
    
    # main window name
    GUI_MAIN_WINDOW = "window1"

    
    #
    # properties
    #
    def f_get_display(self) : return self.previsuDrawingArea
    display = property(f_get_display,None,None,"DrawArea widget for display")
   
    
    def f_get_view_image(self) : return self.PreviewObj.isDisplayAllowed
    def f_set_view_image(self,bVal) : 
        if type(bVal) == bool :
            self.PreviewObj.isDisplayAllowed = bVal
    view_image = property(f_get_view_image,f_set_view_image,None,
                                " propert to know if display of image is allowed in drawing area. if True preview of image is possible")
    
    def f_get_pixbufToDisplay(self) :
        """ getter of pixbufToDisplay""" 
        return  self.PreviewObj.pixbufToDisplay
    def f_set_pixbufToDisplay(self,x):
        """ setter of pixbufToDisplay"""
        self.PreviewObj.pixbufToDisplay = x
    pixbufToDisplay = property(f_get_pixbufToDisplay,f_set_pixbufToDisplay,None,"Pixbuf to display")

    def f_get_open_recent_menu(self) : 
        return self.builder.get_object('menu_file_open_recent')
    open_recent_menu = property(f_get_open_recent_menu,None,None, 'The Open recent menu')

    def f_get_status_progress_bar(self) : return Gui_status_controller(self._status_bar,self._status_progress_bar)
    status_progress_bar = property(f_get_status_progress_bar,None,None, 'The status progress bar')
    

    def f_get_is_button_snapshot_sensitive(self) : 
        return self._snapshot_button.get_property('sensitive')
    def f_set_is_button_snapshot_sensitive(self, value) :
        if type(value) == bool :
            self._snapshot_button.set_sensitive(value)
            self._snapshot_button.grab_focus()
    is_button_snapshot_sensitive = property(f_get_is_button_snapshot_sensitive,f_set_is_button_snapshot_sensitive,None, 'Snapshot button sensitivity')

    def _init_i18n(self):
        """ Initialize all translation/i18n stuff """
        self.locale_path = self.ctrl_obj.lcl_program['PO_DIR']

        # Init the list of languages to support
        langs = []
        #Check the default locale
        lc, encoding = locale.getdefaultlocale()
        if (lc):
            #If we have a default, it's the first in the list
            langs = [lc]

        # Now lets get all of the supported languages on the system
        language = os.environ.get('LANGUAGE', None)
        msg = " language : ",language
        self.logger.debug(msg)
        if (language):
            # langage comes back something like en_CA:en_US:en_GB:en
            # on linuxy systems, on Win32 it's nothing, so we need to
            # split it up into a list
            langs += language.split(":")
        # Now add on to the back of the list the translations that we
        # know that we have, our defaults"""
        langs += ["en_US"]
        

        # Now langs is a list of all of the languages that we are going
        # to try to use.  First we check the default, then what the system
        # told us, and finally the 'known' list
        msg = "locale path", self.locale_path
        self.logger.debug(msg)
        
        #
        # nbd@ grape WARNING  : Why it is needed to do a bindtextdomain and textdomain 
        # on glade as glade is no more use. Gtk.builder instead.
        # if the bind on glade is not performed : the translation in glade files are not translated.
        #
        gtk.glade.bindtextdomain(APP_NAME, self.locale_path)
        gtk.glade.textdomain(APP_NAME)
        gettext.bindtextdomain(APP_NAME, self.locale_path)
        gettext.textdomain(APP_NAME)



        #print "langs %s de %s %s" % (APP_NAME,langs,self.local_path)
        # Get the language to use
        self.lang = gettext.translation(APP_NAME, self.locale_path
            , languages=langs, fallback = True)
        # Install the language, map _() (which we marked our
        # strings to translate with) to self.lang.gettext() which will
        # translate them."""
        global _
        _ = self.lang.gettext



    def __init__(self, ctrl_obj) :
        """ init GUI main obkect """
        # init logger
        self.logger = logging.getLogger('luciole')

        self.ctrl_obj = ctrl_obj
        
        self._init_i18n()


        # GtkBuilder File load
        self.builder = gtk.Builder()
        self.builder.add_from_file( os.path.join(self.ctrl_obj.lcl_program['UI_DIR'],self.GUI_FILE) ) 

        self.window = self.builder.get_object(self.GUI_MAIN_WINDOW)
        self.window.set_icon_from_file('images/luciole.png')

        self.window.set_title( "%s : %s"%(APP_NAME, 'No project' )  )     
        self.window.show()


        # widgets for project init
        self._init_project_buttons()
        
        # acquistion buttons initialization
        self._init_acquistion_buttons()
        
        callbacks = {
                'on_acquisition_button_toggled' :self.on_acquisition_button_toggled,
                'on_button_capture_clicked' :self.on_button_capture_clicked,
                'on_button_up_clicked' :self.on_button_up_clicked,
                'on_button_down_clicked' :self.on_button_down_clicked,
                'on_button_trash_clicked' :self.on_button_trash_clicked,
                'on_button_trash_capture_clicked' : self.on_button_trash_capture_clicked,
                'on_button_capture_to_montage_clicked' :self.on_button_capture_to_montage_clicked,
                'on_button_import_clicked' : self.on_button_import_clicked,
                'on_button_play_toggled' : self.on_button_play_toggled,
                'on_mixer_checkbutton_toggled' : self.on_mixer_checkbutton_toggled,
                'on_alpha_hscale_value_changed' : self.on_alpha_hscale_value_changed,
                'on_hscale_fps_value_changed' : self.on_hscale_fps_value_changed,
                'on_hscale_fps_format_value' : self.on_hscale_fps_format_value,
                # menu file signals
                'on_file_new_activate' :self.on_file_new_activate,
                'on_file_save_activate' :self.on_file_save_activate,
                'on_file_save_as_activate' : self.on_file_save_as_activate,
                'on_file_open_activate' : self.on_file_open_activate,
                'on_file_import_activate' : self.on_file_import_activate,
                'on_file_export_activate' : self.on_file_export_activate,                
                'on_file_export_tool_activate' :self.on_file_export_tool_activate,
                'on_file_quit_activate' : self.on_file_quit_activate,
                'on_file_close_activate' : self.on_file_close_activate,
                'on_view_project_activate' : self.on_view_project_activate,
                'on_Preferences_activate' : self.on_Preferences_activate,
                'on_help_about_activate' : self.on_help_about_activate,

                'on_window1_delete_event' : self.on_window_delete_event,
                'on_window1_destroy_event' : self.on_window_delete_event,

                
        }
        self.builder.connect_signals(callbacks)

        #Force destroy event , even if in glade file, for exiting properly
        self.window.connect("destroy",self.on_window_delete_event,"WM destroy")
        
        #preview window load
        self.previsuDrawingArea = self.builder.get_object("drawingarea1")
        self.PreviewObj = GLD.PreviewPixbuf(self.previsuDrawingArea)    
        self.PreviewObj.displayDefault()

        # nbd@grape : to clarify
        self.wdg_capture_default = self.builder.get_object('treeview_capture')
        self.wdg_capture_parent = self.builder.get_object('scrolledwindow_capture')
        self.wdg_montage_default = self.builder.get_object('treeview_montage')
        self.wdg_montage_parent = self.builder.get_object('scrolledwindow_montage')
        self.clear_treeviews_ctr = 0
        self.load_treeviews_ctr = 0

        # initialize export obj, mainly the window gui
        self._exportObj = GEXPORT.luciole_export_window(self.builder,"export1")
        
        #
        # play pause button init
        #
        self._play_button = self.builder.get_object('button_play')
        self._play_pause_image = self.builder.get_object('image_play_pause')


        

        #status bar 
        self._status_bar = self.builder.get_object('statusbar1')
        self._status_progress_bar = self.builder.get_object('progressbar_status')
	


        self.luciole_prefs = GPREF.Luciole_preferences(self.builder) 
		
    def _init_acquistion_buttons(self) :
        """ acquisition buttons init """
        #get objects from glade
        self._snapshot_button =  self.builder.get_object('snapshot_button')
        self._mixer_checkbutton =  self.builder.get_object('mixer_checkbutton')
        self._alpha_hscale = self.builder.get_object('alpha_hscale')
        # get default alpha value for mixer
        self._alpha_hscale.set_value(LCONST.ALPHA_DEFAULT)
        
        # focus disable on Hscale does not work with glade forced here
        self._alpha_hscale.set_property('can-focus',False)
        self._alpha_hscale.set_property('can-default',False)
        
        # load pixbuf for luciole activity in acquisition button
        self._pxb_luciole_sleep = gtk.gdk.pixbuf_new_from_file("images/luciole-dodo.png")
        self._pxb_luciole_wakedup = gtk.gdk.pixbuf_new_from_file("images/luciole-eveillee.png")
        
        self.acquisition_widget_hide() #by default buttons are not active
      
    def acquisition_widget_hide(self) :
        """ set acquisition buttons in non acquisition mode """
        self._acq_button_image.set_from_pixbuf(self._pxb_luciole_sleep)     # by default firefly is sleeping - no acquisition started
        
        self._snapshot_button.hide()            # snapshot button hide by default
        self._mixer_checkbutton.hide()            # mixer checkbox  hide by default
        self._alpha_hscale.hide()            # mixer alpha level Hscale hide by default
        
        if self._acq_button.get_active() == True :
            # the set_active function cause the toggle button signal emitted
            self._acq_button.set_active(False)

        
    def acquisition_widget_show(self) :
        """ Set acquisition for acquisition show """
        # wake up luciole; i.e. change acquisition button logo
        self._acq_button_image.set_from_pixbuf(self._pxb_luciole_wakedup)
        self._snapshot_button.show()            # snapshot button hide by default
        self._mixer_checkbutton.show()            # mixer checkbox  hide by default
        # if toggle button not active : activate it
        if self._acq_button.get_active() == False :
            # the set_active function cause the toggle button signal emitted
            self._acq_button.set_active(True)

    def _init_project_buttons(self) :
        """ initialisation of fpi buttons """

        # get Hbox with acquisition widgets nas prent of this box  
        self._hbox_acq = self.builder.get_object('hbox_acquisition')
        self._parent_hbox_acq = self._hbox_acq.get_parent()

        # get View/menu widget
        self._menu_view_project = self.builder.get_object('view_project')
        # Not allow Menu --> View --> Project window
        self._menu_view_project.set_sensitive(False)

        # create the open/new project widget
        self._open_project_wdg = GOPEN.Gui_open_project_widget(self.on_file_new_activate,self.on_file_open_activate)
        
        # set open/new project widgets
        self.project_open_widgets()
        
        # get fpi hscale
        self._acq_button =  self.builder.get_object('acquisition_button')
        self._acq_button_image =  self.builder.get_object('acquisition_button_image')
        self._fpi_hscale =  self.builder.get_object('hscale_fps')
        # focus disable on Hscalse does not work with glade forced here
        self._fpi_hscale.set_property('can-focus',False)
        self._fpi_hscale.set_property('can-default',False)
        self._fpi_label = self.builder.get_object('label_fpi')
       

    def project_open_widgets(self) :
        """ When this function is called the project open/new buttons are dispalyed
            The acquisition buttons are hidden
        """
        child = self._parent_hbox_acq.get_child()
        if  child != None :
            self._parent_hbox_acq.remove(child)
            self._parent_hbox_acq.add(self._open_project_wdg)
        
        # Not allow access to Prroject properies window
        self._menu_view_project.set_sensitive(False)

    def project_acquistion_widgets(self) :
        """ When this function is called the acquisition widgets are displayed. 
            The open.new buttons are hidden
        """ 

        child = self._parent_hbox_acq.get_child()
        if  child != None :
            self._parent_hbox_acq.remove(child)
            self._parent_hbox_acq.add(self._hbox_acq)
            
        # Allow access to Prroject properies window
        self._menu_view_project.set_sensitive(True)



    def alpha_show(self) :
        """ Show Hscale for alpha mixer """
        self._alpha_hscale.show() 

    def alpha_hide(self) :
        """ Hide Hscale for alpha mixer """
        self._alpha_hscale.hide() 



    def load_treeviews(self, rushs, capture_list, montage_list) :
        """ this function load the treeviews : capture and chrono 
         both treeview defined in the xml/glade file are replaced by
         the Capture_tres and Chrono_tree who are inherited from gtk.treeview
        """
        l_isOk = False

        self.load_treeviews_ctr = self.load_treeviews_ctr +1 
        # get treeview capture and replace it
        wdg_tvcapture = self.wdg_capture_default
        if wdg_tvcapture != None :
            #get parent and remove treeview
            wdg_tvparent =  wdg_tvcapture.get_parent()
            wdg_tvparent.remove(wdg_tvcapture)
            
            # Create capture treeview
            wdg_tv = GCAT.Capture_tree(capture_list, rushs, self.cb_on_treeview_capture_change, self.cb_on_image_preview_capture)
            # add it in gui
            wdg_tvparent.add(wdg_tv)
            wdg_tv.show()

            self._tv_capture = wdg_tv
            
            l_isOk = True
        else :
            # raise error
            lerr =  " unable to find treeview capture "
            raise LEXCEP.LucioException, lerr
        
        wdg_tvcapture =  self.wdg_montage_default
        
        if ( l_isOk == True ) and (wdg_tvcapture != None) :
            #get parent and remove treeview
            wdg_tvparent =  wdg_tvcapture.get_parent()
            wdg_tvparent.remove(wdg_tvcapture)
            
            # Create capture treeview
            wdg_tv = GMT.Montage_tree(montage_list, rushs, self.cb_on_treeview_montage_change, self.cb_on_image_preview_montage)
            # add it in gui
            wdg_tvparent.add(wdg_tv)
            wdg_tv.show()
            
            self._tv_montage = wdg_tv
            
            l_isOk = True
        else :
            # raise errror
            lerr =  " unable to find treeview capture "
            raise LEXCEP.LucioException, lerr

            l_isOk = False

    def clear_treeviews(self):
        """ clear both capture and montage treeviews """
        self.clear_treeviews_ctr = self.clear_treeviews_ctr +1 
        
        wdg_tvcapture = self._tv_capture
        if wdg_tvcapture != None :
            wdg_tvparent =  wdg_tvcapture.get_parent()
            wdg_tvparent.remove(wdg_tvcapture)
            
            wdg_tvparent.add(self.wdg_capture_default)

        wdg_tvcapture = self._tv_montage
        if wdg_tvcapture != None :
            wdg_tvparent =  wdg_tvcapture.get_parent()
            wdg_tvparent.remove(wdg_tvcapture)
            
            wdg_tvparent.add(self.wdg_montage_default)

    def append_capture(self, image) :
        """ append an image on capture treeview """
        self._tv_capture.append_image(image)
    
    def show_capture_trash_button(self,active =  False) :
        """ Indicate to show or not the capture trash button """
        trash_button = self.builder.get_object('button_trash_capture')
        if active == True :
            trash_button.show()
        else :
            trash_button.hide()
            

    def cb_on_treeview_capture_change(self,image_list) :
        """callback for treeview capture change """
        self.ctrl_obj.project_change('capture_images',image_list)


    def cb_on_treeview_montage_change(self,image_list) :
        """callback for treeview montage change """
        self.ctrl_obj.project_change('chrono_images',image_list)

    def cb_on_image_preview_montage(self,image_obj) :
        """ image double click on treeview : means request preview """
        self.ctrl_obj.image_preview(image_obj,LCONST.MONTAGE)
    
    def cb_on_image_preview_capture(self,image_obj) :
        """ image double click on treeview : means request preview """
        self.ctrl_obj.image_preview(image_obj,LCONST.CAPTURE)


    def new_project_assistant(self,cb_apply):
        """ launch the project assistant window 
            cb_apply : call back called when assisnt apply is done
        """
        # start assistant
        self.ass = GLA.Assistant_new_project(cb_apply)

    def open_project(self) :
        """ launch the open project window """
        filename = GOF.Open_file.open()
        return filename
     
    def set_programbar(self,text, isModified = False) :
        if isModified == True :
            self.window.set_title( "%s : %s (*)"%(APP_NAME,text )  )
        else :
            self.window.set_title( "%s : %s"%(APP_NAME,text )  )
        

    def button_preview_deactivate(self) : 
        """ deactivate button """
        widget = self.builder.get_object('acquisition_button')
        if widget.get_active() :
            # deactivate the button 
            widget.set_active(False)

    def import_dialog(self):
        """ launch import Dialog filechooser """
        return GDIALOG.Dialog.ImportDialog(self.window)

    def dir_chooser_dialog(self) :
        """ launch Dir selection filechooser """
        return GDIALOG.Dialog.DirChooserDialog(self.window)
    
    def export_dialog(self,project_data) :
        """ Display export window """
        self._exportObj.gui_export(project_data)

    def export_tool_dialog(self,project_data) :
        """ Display export tool window """
        X = GEXPORT_TOOL.dialog_export_file(project=project_data)
        X.run()

    def update_play_button(self,is_active = False) :
        """ 
        update pressed state and icon image for play pause
        button
        """
        # the set_active function cause the toggle button signal emitted
        self._play_button.set_active(is_active)

    def update_fpi(self,fpi) :
        """ update fpi """
        index = 1
        # loop conversion fps table, the hscale need the key value
        for (k,v) in LCONST.VIDEO_FPS_TABLE.iteritems() :
            #  find the position 
            (l_framerate,l_fpi) = v 
            if l_fpi == fpi : 
                index = k
        self._fpi_hscale.set_value(float(index))
  
    
    def quit(self):
        """ quit appluication/gui """
        gtk.main_quit()


    def display_project_properties(self,project,cb_project_change) :
        GDIALOG_PROJ.Project_properties(self.window,
                                        project,
                                        cb_project_change)
    
    def display_preferences_dialog(self,conf_options, cb_on_finish = None) :
        self.luciole_prefs.run(conf_options,cb_on_finish)
    ############################################################################
    # glade/XML builder callbacks 
    ############################################################################

    def on_acquisition_button_toggled(self,widget):
        """ Acquisition button toggled """
        if widget.get_active() :
            # if butonn set active start acquisition
            self.ctrl_obj.start_acquisition()
        else :
            # button unactive ; Stop acquiistion
            self.ctrl_obj.stop_acquisition()
    
    def on_button_capture_clicked(self,widget) :
        """Capture button clicked """
        self.ctrl_obj.image_capture()

    def on_button_up_clicked(self,widget) :
        """up button clicked"""
        self._tv_montage.move_up() 


    def on_button_down_clicked(self,widget) :
        """down button clicked """
        self._tv_montage.move_down() 

    
    def on_button_trash_clicked(self,widget) :
        """Trash button clicled"""
        self._tv_montage.remove()
        # to remove also preview
        self.PreviewObj.pixbufToDisplay = None

    def on_button_trash_capture_clicked(self,widget) :
        """Trash button capture clicked"""
        self._tv_capture.remove()
        # to remove also preview
        self.PreviewObj.pixbufToDisplay = None



    def on_button_capture_to_montage_clicked(self,widget) :
        """ move to chrono button clicked """
        self.ctrl_obj.move_to_chrono() 

    def on_button_import_clicked(self,widget):
        """button import clicked"""
        self.ctrl_obj.image_import()
    

    def on_button_play_toggled(self,widget) :
        """ Play/Stop button clicked """
        if widget.get_active() == True :
            # display stop button - to allow player stop
            self._play_pause_image.set_from_stock(gtk.STOCK_MEDIA_STOP,gtk.ICON_SIZE_BUTTON) 
            # call play
            l_pos = self._tv_montage.get_position_selected_row()
            self.ctrl_obj.play(l_pos)
        else :
            # display play image
            self._play_pause_image.set_from_stock(gtk.STOCK_MEDIA_PLAY,gtk.ICON_SIZE_BUTTON) 
            
            # call stop on main controller
            self.ctrl_obj.stop()
        

    def on_mixer_checkbutton_toggled(self,widget) :
        """ Mixer button toggle """
        if widget.get_active() == True :
            # active mixer/onion skin
            self.ctrl_obj.mixer_on()
        else :
            # deactive mixer/onion skin
            self.ctrl_obj.mixer_off()
    
    def on_alpha_hscale_value_changed(self,widget) :
        """ Alpha mixer value changed """
        # parameter should be a value between 0 and 1 , so value is divided by max
        self.ctrl_obj.mixer_alpha_changed( widget.get_value()/ widget.get_adjustment().upper)
        
    def on_hscale_fps_value_changed(self,widget) :
        """ Fps Scale value changed"""
        value= widget.get_value()
        
        #robustness
        if value > 5 : value =5
        if value < 1 : value =1 
        # get the choosen number of frame per image value 
        (fpsDisplay,fpi) = LCONST.VIDEO_FPS_TABLE[int(value)]  
        
        self.ctrl_obj.update_fpi(fpi) 
    
        self._fpi_hscale.set_property('has-focus',False)
        self._fpi_hscale.set_property('has-default',False)

    def on_hscale_fps_format_value(self,widget,value) :
        """ Fps Scale value changed.
        This callback allow display of range [1..25 ] in the scale bar instead of [1..6] 
        """
        
        #robustness
        if value > 5 : value =5
        if value < 1 : value =1  
        
        (fpsDisplay, NbFrame) = LCONST.VIDEO_FPS_TABLE[int(value)]
        # return converted value to display  
        return fpsDisplay
 
    def on_file_new_activate(self,widget) :
        """menu new clicked """
        self.ctrl_obj.new_project()

    def on_file_save_activate(self,widget) :
        """menu save clicked """
        self.ctrl_obj.save_project()

    def on_file_save_as_activate(self,widget) :
        """menu save as clicked """
        self.ctrl_obj.save_as_project()

    def on_file_open_activate(self,widget):
        """file open activate """
        self.ctrl_obj.open_project()

    def on_file_import_activate(self,widget):
        """file import activate """
        self.ctrl_obj.image_import()

    def on_file_export_activate(self,widget):
        """file export activate """
        self.ctrl_obj.export()

    def on_file_export_tool_activate(self,widget):
        """file export activate """
        self.ctrl_obj.export_tool()

    def on_file_quit_activate(self,widget):
        """ file quit actovated"""
        self.ctrl_obj.quit() 
        return True


    def on_file_close_activate(self,widget):
        """file close activate """
        self.ctrl_obj.close()

    def on_file_close_activate(self,widget):
        """file close activate """
        self.ctrl_obj.close()
    
    def on_view_project_activate(self,widget):
        """ view project properties """
        self.ctrl_obj.project_properties() 
    
    def on_Preferences_activate(self,widget) :
        """ Prefrences button activated """
        self.ctrl_obj.luciole_preferences()
    
    def __UpdateAbout(self, aboutWidget) :
        """ Update with version of about window"""
        strRev= '%(revno)d' % _version.version_info
        strBranch = '%(branch_nick)s'%  _version.version_info
        strVersion = "\n %s (%s)"%(strBranch,strRev)
        aboutWidget.set_version(strVersion)
    
    def on_help_about_activate(self,widget):
        """On help about activate"""
        aboutdialog = self.builder.get_object('aboutdialog')
        self.__UpdateAbout(aboutdialog)
        aboutdialog.show_all()
        result = aboutdialog.run()
        aboutdialog.hide()


    def on_window_delete_event(self,widget,event):
        """ destroy/delete event : """
        self.ctrl_obj.quit() 
        # the 'return true' avoid the automatic close of application
        return True

