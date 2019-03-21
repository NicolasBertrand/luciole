#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- Mode: Python -*-
# vim:si:ai:et:sw=4:sts=4:ts=4
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
assistant_new_project.py :    
    GTK assistant for creation of new projects
"""

from .. import luciole_constants as LCONST
from .. import luciole_image as LIMG
import webcam_detection_widget as LWDW
import dialog as GMSG

import gtk
import os.path
import re
import threading
from gettext import gettext as _



class Page_intro(gtk.VBox) :
    """ Assistant introduction page """
    
    def __init__(self,assistant, project_data,*args ) :
        """ Init Introduction page of assistant"""
        
        super(Page_intro,self).__init__(homogeneous = False, spacing = 5)
        self.set_name('page_intro')
        self.assistant = assistant
        self.project_data = project_data
        
        self.pattern_filename = re.compile(r'^\w+$') 
        #
        # Initailize widgets for first page 
        #
        
        # A label 
        label = gtk.Label(_('This assistant will help you on configuration of a new Luciole project.'))
        self.pack_start(    child = label,
                            expand = False,
                            fill =  False,
                            padding = 10
                                )
        # A line separator
        self.pack_start(    child = gtk.HSeparator(),
                            expand = False,
                            fill =  False,
                            padding = 10
                                )
        # A label
        label = gtk.Label(_('Select project name and destination folder.'))
        self.pack_start(    child = label,
                            expand = False,
                            fill =  False,
                            padding = 10
                                )
        
        # Use a gtk.table to display project/folder chosse  
        table = gtk.Table(3, 2, True)
        
        label_project_name = gtk.Label(_('Project Name'))
        # positionning of label
        label_project_name.set_alignment(xalign=0.0,yalign=0.5)    # left justification of label
    
        # Insert label into the upper left quadrant of the table
        table.attach(label_project_name, 0, 1, 0, 1,xpadding = 10 )
        
        self.entry_project_name = gtk.Entry()
        self.entry_project_name.set_text('')
        self.entry_project_name.connect('changed',self.on_project_name_changed)
        # Insert entry_project_name into the upper right quadrant of the table
        table.attach(self.entry_project_name, 1, 2, 0, 1, xpadding =10)
        
        label_folder = gtk.Label(_('Folder'))
        # positionning of label
        label_folder.set_alignment(xalign=0.0,yalign=0.5)            # left justification of label
        # Insert label into the lower left quadrant of the table
        table.attach(label_folder, 0, 1, 1, 2,xpadding = 10 )
        
        dialog = gtk.FileChooserDialog(
                                        title = _('Select a folder'),
                                        parent = None,
                                        action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER ,
                                        buttons =  (   gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_OK,gtk.RESPONSE_OK)
                                        )
        self.fileChooser = gtk.FileChooserButton(dialog)
        self.fileChooser.connect('selection-changed',self.on_dir_is_changed) 

        self.fileChooser.set_current_folder(os.path.expandvars('$HOME'))
        self.fileChooser.set_filename(os.path.expandvars('$HOME'))
        # Insert label into the lower right quadrant of the table
        table.attach(self.fileChooser, 1, 2, 1, 2, yoptions=gtk.SHRINK, xpadding =10)
       
        #label for message
        self.message_label =  gtk.Label('')
        self.message_label.set_alignment(xalign=0.0,yalign=0.5)            # left justification of label
        table.attach(self.message_label,0,2,2,3,yoptions=gtk.FILL,xpadding=10)


        # pack table to main widget
        self.pack_start(    child = table,
                            expand = True,
                            fill =  True,
                            padding = 10
                                )
                  
            
       
    def _isProjectExists(self, project_path) :
        """ Check if a project path exists"""
        return os.path.exists(project_path)
    
    def _isProjectNameValid(self, name) :
        """ Check ig entered project name is correct"""
        isValid = False
        if self.pattern_filename.match(name) :
            isValid = True
        return isValid
         

    def UpdateProjectData(self,project_name, project_folder)  :
        """ Update project data like 'project_name' and 'project_fir'.
            projetct dict. is updated if the project project_name is correct
            and if path project_dir/project_name doe not exists yet.
            Return True if project has been updated"""

        isProjectUpdated = False
        # get project name and dir
        self.message_label.set_text(' ')
        self.assistant.set_page_complete(self,False)
        # verify if input date are not balnk
        if project_name != '' and project_folder != None :
            # check projetc name validity
            if self._isProjectNameValid(project_name) :
                # check if project already exist
                fullpath = os.path.join(project_folder, project_name)
                if not self._isProjectExists(fullpath) :
                    # all cons ok update project data
                    self.project_data['project_name'] = project_name
                    self.project_data['project_dir'] = project_folder
                    self.assistant.set_page_complete(self,True)
                    isProjectUpdated = True
                else :
                    # project with same name alreday exists
                    msg = _("The project %s already exists !"%(fullpath)) 
                    self.message_label.set_text(msg)
            else :
                # invalid projetc name
                msg = _("%s isn't a valid project name. It should be a combination of alphanumeric and '_' characters "%project_name) 
                self.message_label.set_text(msg)
        
        return isProjectUpdated



            
    def on_project_name_changed(self,widget):
        """ indicate project name change. Set page complete if non blank text is set."""
        l_project_name =  widget.get_text()
        l_project_folder = self.fileChooser.get_filename()
        self.UpdateProjectData(l_project_name, l_project_folder)
 
    def on_dir_is_changed(self,widget) :
        """ Call back for 'selection-changed' signal """
        l_project_folder = widget.get_filename()
        l_project_name =  self.entry_project_name.get_text()
        self.UpdateProjectData(l_project_name, l_project_folder)

 


class Page_matos(gtk.VBox) :
    """ Asistant page for hardware selection and poject image rate """
    
    def __init__(self,assistant, project_data,*args ) :
        """ Init page for hardware selection """
        super(Page_matos,self).__init__(*args )
        self.set_name('page_matos')
        self.assistant = assistant
        self.project_data = project_data
                
        #
        # set default values
        #
        
        # webcam by default 
        self.project_data['hardtype'] = LCONST.WEBCAM
        
        # choose of a value in the middle of the progress bar 
        l_Hdefault = 3
        
        (fpsDisplay,fpi) = LCONST.VIDEO_FPS_TABLE[int(l_Hdefault)]  
        self.project_data['fpi']= fpi
        
        #
        # Initailize widgets for hardware selection page 
        #
        
        #
        # FIRST VBOX -- hardware selection
            
        VBox = gtk.VBox()
        if VBox :
            label = gtk.Label(_('Select a device'))
            VBox.add(label)
            
            HBox = gtk.HBox()
            if HBox :
                l_hardtype =  LCONST.DVCAM
                radiobutton1 =  gtk.RadioButton(group=None, label=LCONST.HardTypeName[l_hardtype])
                # conect toggled signal to button
                radiobutton1.connect('toggled',self.radiobutton_toggled,l_hardtype)
                HBox.add(radiobutton1)
                
                l_hardtype =  LCONST.WEBCAM
                radiobutton =  gtk.RadioButton(group=radiobutton1, label= LCONST.HardTypeName[l_hardtype])
                # conect toggled signal to button
                radiobutton.connect('toggled',self.radiobutton_toggled,l_hardtype)
                # set webcam button as default button
                radiobutton.set_active(True)
                HBox.add(radiobutton)
                
                l_hardtype =  LCONST.DIGICAM
                desc=_(" Other device.\n(Manual import)")
                radiobutton =  gtk.RadioButton(group=radiobutton1, label= desc )
                # conect toggled signal to button
                radiobutton.connect('toggled',self.radiobutton_toggled,l_hardtype)
                HBox.add(radiobutton)

                # add 1st Hbox to main widget
                VBox.add(HBox)
        
            self.add(VBox)

        #
        # SECOND VBO -- image frame rate selection   
        VBox = gtk.VBox()
        if VBox :
           HBox = gtk.HBox()
           if HBox :
                label = gtk.Label(_('Images per second'))
                HBox.add(label)
                
                # an horizontal scale bar is used to select the framerate
                Hscale = gtk.HScale()
                #set range of fpi [1..6] to be converted to [1..25]
                # with callback scale_fps_value_changed
                Hscale.set_range(1,6)
                Hscale.set_increments(1,1)
                Hscale.set_value(l_Hdefault)
                Hscale.connect('value-changed',self.scale_fps_value_changed)
                Hscale.connect('format-value',self.scale_fps_format_value)
                HBox.add(Hscale)
                
                # add 2nd Hbox to main widget
                VBox.add(HBox)  
          
        self.add(VBox)

    
    def radiobutton_toggled(self,widget,type):
        """ Hardware radio button """
        if (widget.get_active() ) :
            self.project_data['hardtype'] = type
            
    def scale_fps_value_changed(self,widget) :
        """ Fps Scale value changed"""
        value= widget.get_value()
        
        #robustness
        if value > 5 : value =5
        if value < 1 : value =1 
        # get the choosen number of frame per image value 
        
        (fpsDisplay,fpi) = LCONST.VIDEO_FPS_TABLE[int(value)]  
        self.project_data['fpi']= fpi
       
    
    def scale_fps_format_value(self,widget,value) :
        """ Fps Scale value changed.
        This callback allow display of range [1..25 ] in the scale bar instead of [1..6] 
        """
        
        #robustness
        if value > 5 : value =5
        if value < 1 : value =1  
        
        (fpsDisplay, NbFrame) = LCONST.VIDEO_FPS_TABLE[int(value)]
        # return converted value to display  
        return fpsDisplay
        
class Page_webcam(LWDW.Webcam_detection_Box) :
    """ Assistant page for webcam detection """
    
    def __init__(self, assistant, project_data, *args ) :
        super(Page_webcam,self).__init__(project_data,*args )
        self.assistant = assistant

    def assistant_prepare_webcam_detection(self,page) :
        """ prepare assistant page for the webcam detection page """
        # during detection not indicate page complete
        self.assistant.set_page_complete(page,False)
        
        super(Page_webcam,self).prepare_webcam_detection()        

        
    def _on_webcam_detect_complete(self,webcam_obj) :
        """ callback , executed when webcam detection is complete """

        nb_webcam = super(Page_webcam,self)._on_webcam_detect_complete(webcam_obj)        
        if nb_webcam > 0 :
            # almost one webcam detected
            # assisant page can now be set as complete
            self.assistant.set_page_complete(self,True)
class Page_summary(gtk.VBox) :
    """ Asistant summary page : show lucuile project info"""
    
    def __init__(self,assistant, project_data,*args ) :
        """ init class ofr assistnat page summary """
        super(Page_summary,self).__init__(*args )
        self.set_name('Page_summary')
        self.assistant = assistant
        self.project_data = project_data
  
        #
        # Initailize widgets for sumary page -- only a textview widget
        #
        
        self.text_wdg = gtk.TextView()
        self.add(self.text_wdg) 

    def assistant_prepare_summary_page(self,page) :
        """ prepare summary page """
      
        textbuffer = self.text_wdg.get_buffer()
        string=""
        text_list=list()
        
        # display project name
        string = "%s : %s"%( _('Project Name'), self.project_data['project_name'])
        text_list.append(string)

        # display project path
        string = "%s : %s \n"%( _('Project Path'), self.project_data['project_dir'])
        text_list.append(string)

        # display project FPI 
        # loop on FPS TABLE to found the fps value
        fps ="0"
        for k,v in LCONST.VIDEO_FPS_TABLE.iteritems() :
            if v[1] == self.project_data['fpi'] : fps =v[0]
            
        string = "%s : %s "%( _('Number of frames per seconds'), fps)
        text_list.append(string)
        
        # display Hardware type 
        string = "%s : %s "%( _('Hardware type'), LCONST.HardTypeName[self.project_data['hardtype']] )
        text_list.append(string)
        
        # display info specific for webcam
        if ( self.project_data['hardtype'] == LCONST.WEBCAM ) :
            # webcam name
            string = "\n%s : %s"%(_('Webcam name'),self.project_data['webcam_data']['name'])
            text_list.append(string)
            
            #webcam device 
            string = "%s : %s"%(_('Webcam device'),self.project_data['webcam_data']['device'])
            text_list.append(string)

            #webcam resolution 
            string = "%s : %sx%s"%(  _('Webcam resolution used'), 
                                        self.project_data['webcam_data']['width'],
                                        self.project_data['webcam_data']['height'])
            text_list.append(string)

            #webcam device 
            string = "%s : %s"%(_('Webcam driver used'),self.project_data['webcam_data']['source_input'])
            text_list.append(string)
        
            
            # Final message  
            string = "\n %s "%(_('Have fun with luciole !'))
            text_list.append(string)

        string = "\n".join(text_list)         

        textbuffer.set_text(string)

                 

class Assistant_new_project(object) :
    """ Class for managing a Gtk Assitant to configure a luciole project """

    def __init__(self,apply_callback) :
        """ Initialize assistant window """
        self.apply_callback = apply_callback 
        
        #
        # init project datas 
        #
        self.project_data = dict()
 
        self.assistant = gtk.Assistant()
        self.assistant.connect('delete-event',self.on_quit)
        self.assistant.connect('destroy-event',self.on_quit)
        
        self.assistant.connect('apply',self.on_apply)
        self.assistant.connect('cancel',self.on_cancel)
        self.assistant.connect('close',self.on_close)
        self.assistant.connect('prepare',self.on_prepare)
        
        self.assistant.set_property('title',_('Luciole project assistant'))
        
        # assistant logo with no text
        image = LIMG.Image('images/luciole_logo.png',True,2,False)
       

        #
        # configure page 1
        #
        self.p1 = Page_intro( self.assistant,  self.project_data)
        self.assistant.append_page(self.p1)
        self.assistant.set_page_title( self.p1,  _(' Select a project path '))
        self.assistant.set_page_type( self.p1,  gtk.ASSISTANT_PAGE_INTRO)
        self.assistant.set_page_side_image(self.p1,image.pixbuf_thumb)

        #
        # configure page 2
        #
        self.p2 = Page_matos( self.assistant,  self.project_data)
        self.assistant.append_page(self.p2)
        self.assistant.set_page_title( self.p2,  _(' Select hardware '))
        self.assistant.set_page_type( self.p2,  gtk.ASSISTANT_PAGE_CONTENT)
        self.assistant.set_page_complete( self.p2,True)
        self.assistant.set_page_side_image(self.p1,image.pixbuf_thumb)
  
        #
        # configure page 3
        #
        self.p3 = Page_webcam( self.assistant,  self.project_data) 
        self.assistant.append_page(self.p3)
        self.assistant.set_page_title( self.p3,  _(' Webcam detection '))
        #self.assistant.set_page_type( self.p3,  gtk.ASSISTANT_PAGE_PROGRESS)
        self.assistant.set_page_type( self.p3,  gtk.ASSISTANT_PAGE_CONTENT)
        self.assistant.set_page_side_image(self.p1,image.pixbuf_thumb)
        
        #
        # configure page 4
        #
        self.p4 = Page_summary( self.assistant,  self.project_data)
        self.assistant.append_page(self.p4)
        self.assistant.set_page_title( self.p4,  _(' Project overview '))
        self.assistant.set_page_type( self.p4,  gtk.ASSISTANT_PAGE_CONFIRM)
        self.assistant.set_page_complete( self.p4,True)
        self.assistant.set_page_side_image(self.p1,image.pixbuf_thumb)
        
        
        # page_func setup : used to manage the page sequences.
        self.assistant.set_forward_page_func(self.page_func)

        self.assistant.show_all()

        

    def page_func(self,page_num) :
        """ call back to know wcih  next page to load """
        page_out = page_num
        if (page_out == 1 ) and  (self.project_data['hardtype'] != LCONST.WEBCAM) :
            # if web cam selected go to page 2
            # else go to page 3
            page_out = 3
        else :
            page_out = page_out +1
        return page_out


    def on_quit(self,widget,event) :
        """ Quit button clicked """
        self.assistant.destroy()

    def on_apply(self,widget) :
        """ Apply button clicked. send project data to appliation mainframe. """     
        self.apply_callback(self.project_data)       

    def on_cancel(self,widget) :
        """ Quit button clicked """
        self.assistant.destroy()

    def on_prepare(self,widget,page) :
        """ prepare callback for initiating a new page"""
        # prepare webcam detection
        if widget.get_current_page() == 2 : self.p3.assistant_prepare_webcam_detection(page)
        # prepare last page display
        if widget.get_current_page() == 3: self.p4.assistant_prepare_summary_page(page)
        
    def on_close(self,widget) :
        """ close action """
        self.assistant.destroy()
        
        
