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
    dialog_project_properties.py : Dialog who display the luciole project properties
"""
#i18n
from gettext import gettext as _

import gtk
import pango

from .. import luciole_constants as LCONST
from .. import luciole_exceptions as LEXCEP
import webcam_detection_widget as LWDW

import logging 
module_logger = logging.getLogger('luciole')


#type of widgets for displaying webcam data
(LABEL,ENTRY,SCALE)=range(3)



class Project_properties(object):
   
    # This tow 2 tables descibes how to display project info
    _PROJECT_PREFS = {
            'project_dir' :     {    
                                'desc' : _('Project folder :'),
                                'type'  :   LABEL
                                },
            'project_name' :    {    
                                'desc' : _('Project name :'),
                                'type'  :   LABEL
                                },
            'xml_filename' :    {    
                                'desc' : _('XML file :'),
                                'type'  :   LABEL
                                },

            'fpi' :    {    
                                'desc' : _('Number of frames / image'),
                                'type'  :   LABEL
                                },
            'hardtype' :    {    
                                'desc' : _('Device type'),
                                'type'  :   LABEL
                                },

            }

    _WEBCAM_PREFS = {
            'device' :     {    
                                'desc' : _('Device :'),
                                'type'  :   ENTRY
                                },
            'name' :     {    
                                'desc' : _('Webcam name :'),
                                'type'  :   LABEL
                                },
            
            'source_input' :     {    
                                'desc' : _('Video capture driver :'),
                                'type'  :   LABEL
                                },
            'width' :     {    
                                'desc' : _('Video width :'),
                                'type'  :   LABEL
                                },
            'height' :     {    
                                'desc' : _('Video height :'),
                                'type'  :   LABEL
                                },
            'framerate_list':     {    
                                'desc' : _('Webcam framerate \n (number of images per second)'),
                                'type'  :   SCALE
                                },

 
        }


    _title = _('Project properties')
    
    def __init__(self,main_window,  project, cb_project_change) :
        """ create a Dialog with project properties and display it"""
        # init logger
        self.logger = logging.getLogger('luciole')
        self._dialog = gtk.Dialog   (   _(self._title),
                                        main_window,
                                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                        (   gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                            gtk.STOCK_CLOSE,gtk.RESPONSE_CLOSE,
                                            gtk.STOCK_APPLY,gtk.RESPONSE_APPLY)
                                    )
        self._project = project
        self._cb_project_change = cb_project_change
        # keep framerate list and framerate selected those value can change
        self._framerate_selected = None
        self._framerate_list = None
        self.webcam_widget_table_position = 0

        if self._project['hardtype'] == LCONST.WEBCAM and  self._project['webcam_data'] != {} :
            self._framerate_selected = self._project['webcam_data']['framerate_selected']
            self._framerate_list = self._project['webcam_data']['framerate_list']

        # connect destroy signal
        #self._dialog.connect("destroy", self._cb_on_exit)
        self._dialog.connect("delete-event", self._cb_on_exit)
        
        # Created 'entry' widget will be stored here
        self.webcam_widgets = {}

        # make dialog displays
        self.make_widget()
        self._dialog.show_all()
        
        self._exit = False
        while (self._exit == False) : 
            # run dialog
            result = self._dialog.run()
            # wait for reponse
            # nbd@grape : missing what to do when info changed
            # probably add callback to update project
            if result == gtk.RESPONSE_CANCEL :
                self._dialog.destroy()
                self._exit = True
            elif result == gtk.RESPONSE_CLOSE :
                self._dialog.destroy()
                self._exit = True
            elif result == gtk.RESPONSE_APPLY :
                # apply button clicked
                # loop on each entry widget , get the text and compare it with project so see if value changed
                # assumption only enry on webcam data
                # only webcam data can be modified  
                if self._project['hardtype'] == LCONST.WEBCAM  and  self._project['webcam_data'] != {} :
                    webcam_dict = self._project['webcam_data']
                    for (key_entry, widget_entry) in self.webcam_widgets.iteritems() :
                        # specific treatment when the wigdet is associated to framerate_list
                        # store framerate_list and framerate_selected
                        if key_entry == 'framerate_list' :
                            # callback for updated framerate
                            self._cb_project_change('webcam_data', 'framerate_selected',self._framerate_selected)
                            # check if framerate list has changed if yes callback for framerate list
                            if  webcam_dict[key_entry] != self._framerate_list :
                                self._cb_project_change('webcam_data', 'framerate_list',self._framerate_list)
                        else :
                            if widget_entry.get_text() !=  webcam_dict[key_entry] :
                                # entry value changed
                                # emit callback to inidcate project change
                                self._cb_project_change('webcam_data', key_entry, widget_entry.get_text())
    
    def _cb_on_exit(self,widget,event) :
        self._dialog.destroy()
        self._exit = True
        return True

    def make_title_label(self, text) :
        """ set a title label (i.e 1st column of table): play wiyh pango"""
        label= gtk.Label()
        label.set_text("%s"%text)
        attrs = pango.AttrList()
        attrs.insert( pango.AttrWeight(pango.WEIGHT_BOLD,0, -1))
        label.set_attributes(attrs)

        # positionning of label
        label.set_alignment(xalign=0.0,yalign=0.5)    # left justification of label
        # Insert label into the upper left quadrant of the table
        label.show()
        return label 
 
    def make_table_title(self,title) :
        """ set a Table title : play with pango"""
        label= gtk.Label()
        label.set_text(title)
        attrs = pango.AttrList()
        attrs.insert( pango.AttrWeight(pango.WEIGHT_BOLD,0, -1))
        attrs.insert( pango.AttrSize(18000,0, -1))
        label.set_attributes(attrs)

        # positionning of label
        label.set_alignment(xalign=0.5,yalign=0.5)  # center 
        # Insert label into the upper left quadrant of the table
        label.show()
        return label



    def make_table_row(self,table,row,key):
        """ Craate the row for the gtk.Table used for project properties display """
        label= self.make_title_label(_(self._PROJECT_PREFS[key]['desc']))
        table.attach(label, 0, 1, row, row +1 ,xpadding = 10 )

        widget = None
        if key == 'hardtype' :
            widget = gtk.Label(LCONST.HardTypeName[self._project[key]] )
        else :
            if self._PROJECT_PREFS[key]['type'] == LABEL :
                widget = gtk.Label(self._project[key])
        
        widget.set_alignment(xalign=0.0,yalign=0.5)    # left justification of label
        widget.show()
        table.attach(widget, 1, 2, row, row+1,xpadding = 10 )

    def make_table_webcam_row(self,table,row,key):
        """ Craate the row for the gtk.Table used for webcam properties display """
        label= self.make_title_label(_(self._WEBCAM_PREFS[key]['desc']))
        table.attach(label, 0, 1, row, row +1 ,xpadding = 10 )

        widget = None
        if self._WEBCAM_PREFS[key]['type'] == ENTRY :
            widget = gtk.Entry()
            widget.set_alignment(xalign = 0.0)                 # left justification 
            widget.set_text("%s"%self._project['webcam_data'][key])
        elif self._WEBCAM_PREFS[key]['type'] == LABEL : 
            widget = gtk.Label()
            widget.set_alignment(xalign = 0.0, yalign = 0.5)     # left justification 
            widget.set_text("%s"%self._project['webcam_data'][key])
        elif self._WEBCAM_PREFS[key]['type'] == SCALE :
            # display scale bar if several framerates are available 
            if len( self._project['webcam_data'][key]) > 1 :
                widget = Framerate_scale(self._project['webcam_data'][key],
                                        self._project['webcam_data']['framerate_selected'],
                                        self._cb_framerate_selected)
            elif len( self._project['webcam_data'][key]) == 1 :
                widget = gtk.Label()
                widget.set_alignment(xalign = 0.0, yalign = 0.5)     # left justification
                # in that case framerate_selected = framerate_list[0]
                framerate = int(self._project['webcam_data']['framerate_selected'][0]/self._project['webcam_data']['framerate_selected'][1])
                widget.set_text("%s"%framerate)
            else :
                self.logging.debug('Something goes wrong')
            self.webcam_widget_table_position = row

        self.webcam_widgets[key] = widget     # save the widget
        
        widget.show()
        table.attach(widget, 1, 2, row, row+1,xpadding = 10 )


    def make_webcam_data(self) :
        """ build widgets for display of webcam properties"""
        self._dialog.vbox.pack_start(   child = gtk.HSeparator(),
                                        expand = True,
                                        fill =  True,
                                        padding = 5
                                    )
        
        label = self.make_table_title(_('Webcam properties'))       
        self._dialog.vbox.pack_start(   child = label,
                                        expand = True,
                                        fill =  True,
                                        padding = 10
                                    )
        Hbox = gtk.HBox()
        if Hbox :
            #
            # Display Table 
            #
            table = gtk.Table()
            table.set_homogeneous(False)
            self.make_table_webcam_row(table,0,'name')
            self.make_table_webcam_row(table,1,'width')
            self.make_table_webcam_row(table,2,'height')
            self.make_table_webcam_row(table,3,'source_input')
            self.make_table_webcam_row(table,4,'device')
            self.make_table_webcam_row(table,5,'framerate_list')
            # No lines for framerate_selected tag : handled framerate_list tag

            Hbox.pack_start(   child = table,
                                expand = True,
                                fill =  True,
                                padding = 10
                            )
            #
            # Display Button fo webcam detetction 
            #
            button = gtk.Button(_('Webcam detection'))
            button.connect('clicked', self.on_button_webcam_clicked)
            Hbox.pack_start(    child = button,
                                expand = False,
                                fill =  False,
                                padding = 10
                            )
            

        # pack The HBox
        self._dialog.vbox.pack_start(   child = Hbox,
                                        expand = True,
                                        fill =  True,
                                        padding = 10
                                    )

    def make_widget(self) :
        """ build widgets for display of project properties """
        label = self.make_table_title(_(self._title))       
        self._dialog.vbox.pack_start(   child = label,
                                        expand = True,
                                        fill =  True,
                                        padding = 10
                                    )
        
        table = gtk.Table(2, 2, True)
        table.set_homogeneous(False)
        self.make_table_row(table,0,'project_name')
        self.make_table_row(table,1,'project_dir')
        self.make_table_row(table,2,'xml_filename')
        self.make_table_row(table,3,'fpi')
        self.make_table_row(table,4,'hardtype')
        table.show()
        self._dialog.vbox.pack_start(   child = table,
                                        expand = True,
                                        fill =  True,
                                        padding = 10
                                    )
        
        if self._project['hardtype'] == LCONST.WEBCAM :
            # if webcam based project display webcam properties
            self.make_webcam_data()
            
    def on_button_webcam_clicked(self,widget,) :
        """ Button webcam clicked """
        Webcam_detection_dialog(self._dialog,self._cb_webcam_detection)



    def _cb_webcam_detection(self,project_data) :
        """ callback when webcam detection is done update webcam data """
        if project_data.has_key('webcam_data') and project_data['webcam_data'] != {} :
            for (w_key, w_widget) in self.webcam_widgets.iteritems() :
                # Sepcific operation for framerate_list widget
                if w_key == 'framerate_list' :
                    self._framerate_list = project_data['webcam_data']['framerate_list']
                    self._framerate_selected = project_data['webcam_data']['framerate_selected']
                    # 2 cases only one framerate or several framerates : 
                    # display a Label or a Scale 
                    
                    # current widget is a label
                    if type(w_widget) == gtk.Label :
                        # how many framerates in framerate list 
                        if len( self._framerate_list) > 1 :
                            # Sevaral framerates
                            # Hide current widget
                            w_widget.hide()
                            # create a Framerate_scale widget
                            widget = Framerate_scale(self._framerate_list,
                                        self._framerate_selected,
                                        self._cb_framerate_selected)
                            
                            
                            # Parent is a table attach new widget
                            w_widget.parent.attach( widget, 1, 2, 
                                                    self.webcam_widget_table_position, 
                                                    self.webcam_widget_table_position+1,
                                                    xpadding = 10 )
                            
                            self.webcam_widgets[w_key] = widget     # replace the widget
                        
                        elif len( self._framerate_list ) == 1 :
                            # only one framerate update label 
                            w_text = int(   self._framerate_selected[0] / 
                                            self._framerate_selected[1])
                            w_text ="%s"%w_text
                            w_widget.set_text(w_text)
                        else :
                            # Not normal
                            lerr =  " 0 is an invalid number of framerates."
                            raise LEXCEP.LucioException, lerr
 
                    # current widegt is a framerate scale     
                    else :
                        # how many framerates in framerate list 
                        if len(self._framerate_list) > 1 :
                            # Several framerates
                            # refresh Framerate_scale widget 
                            w_widget.refresh(self._framerate_list,self._framerate_selected )

                        elif len( self._framerate_list ) == 1 :
                            # only one framerate is available
                            # Hide current widget
                            w_widget.hide()
                            
                            # create a Label widget
                            widget = gtk.Label()
                            widget.set_alignment(xalign = 0.0, yalign = 0.5)     # left justification
                            w_text = int(   self._framerate_selected[0]/
                                            self._framerate_selected[1])
                            w_text ="%s"%w_text
                            widget.set_text("%s"%framerate)

                            # Parent is a table attach new widget
                            w_widget.parent.attach( widget, 1, 2, 
                                                    self.webcam_widget_table_position, 
                                                    self.webcam_widget_table_position+1,
                                                    xpadding = 10 )
                            
                            self.webcam_widgets[w_key] = widget     # replace the widget
                        else :
                            # Not normal
                            lerr =  " 0 is an invalid number of framerates."
                            raise LEXCEP.LucioException, lerr


                # for other webcam widgets : only text to update
                else :
                    if  project_data['webcam_data'].has_key(w_key) : 
                        w_text ="%s"%project_data['webcam_data'][w_key]
                        w_widget.set_text(w_text)
                    else :
                        w_widget.set_text('')
    
    def _cb_framerate_selected(self,framerate) :
        """ callback to update selected framerate used by Framerate_scale widget """
        self._framerate_selected = framerate

class Webcam_detection_dialog(gtk.MessageDialog) :
    """ Opens Dialog for webcam Detection """

    def __init__(self,parent, cb_ok = None ) :
        """ create a Dialog with project properties and disqpay it
            parent : The parent window
            cb_ok : The callback when on button is clicked 
        """
        super(Webcam_detection_dialog,self).__init__(   
                                        parent = parent,
                                        flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                        type = gtk.MESSAGE_INFO,
                                        buttons = gtk.BUTTONS_OK_CANCEL
                                        )
        self.cb_ok = cb_ok  
        
        # detected data will be stored here 
        self.project_webcam=dict()
        
        self.webcam_widget = LWDW.Webcam_detection_Box(self.project_webcam) 
        
        self.vbox.pack_start(   child = self.webcam_widget ,
                                expand = True ,
                                fill =  True ,
                                padding = 10
                                )
        
        # connect destroy signal
        self.connect("delete-event", self._cb_on_exit)
        
        self.show_all()
        
        #start webcam detection
        self.webcam_widget.prepare_webcam_detection()
        
        result = self.run()
        if result == gtk.RESPONSE_OK :
            # repsonse ok upddate callback
            if self.cb_ok != None : self.cb_ok(self.project_webcam)
        
        self.destroy()

    def _cb_on_exit(self,widget,event) :
        """ On exit callback """
        self.destroy()
        return True


class Framerate_scale(gtk.HScale) :
    """ 
    Widget use to display an horizontal scale : 
    represenation of webcam framerates  in number of images per seconds
    """
    
    def __init__(self,framerate_range,initial_range,cb_framerate_changed) :
        """
            Constructor
            params :
                - framerate_range : The framerate range - a list of framerate tuple
                - initial_range : The initial range to dipslay - a tuple
                - cb_framerate_changed : the callback function to indicate framerate change
        """
        
        # 
        # store params
        #
        self._framerate_range = framerate_range
        self._initial_range = initial_range
        self._cb_framerate_changed = cb_framerate_changed

        
        #
        # configure widget
        #
        
        # compute the initial position on Scale bar
        initial_f_value = float(self._framerate_range.index(self._initial_range))
        
        #
        # compute an adjustment in range [0 .. nb_framerate], icrement is 1 
        # Use floats as ints actually
        # Display framerates instead of float values
        # 
        adj = gtk.Adjustment(value =initial_f_value, 
                            lower = 0.0, 
                            upper = float(len( self._framerate_range)),
                            step_incr = 1.0,
                            page_incr = 1.0)

        
        super(Framerate_scale,self).__init__(adjustment = adj)
        
        # configure signals
        self.connect("format-value", self.on_format_value)
        self.connect("value-changed", self.on_value_changed)
        
        # configure widget display properties
        self.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        self.set_value_pos(gtk.POS_BOTTOM)
        self.show_all()

    def on_format_value(self,widget,value) :
        """
        Signal 'format-value' : Used to display value in scale in image/seconds format.
        Computed according the adjustment value,  the intger round of value is the index
        of framerate_range
        """
        int_val = int(value)
        if int_val >= len(self._framerate_range) :
            int_val = len(self._framerate_range) -1
        val_to_display = self._framerate_range[int_val]
        # compute and return the number of images per second
        return int(val_to_display[0]/val_to_display[1])
 
    def on_value_changed(self,widget) :
        """ 
        Emited when a value is changed and selected by user 
        the signal function get the float value, round it, 
        get the equivalent framerate. 
        """ 
        # TODO : how to update webcam date
        
        # get rounded value
        int_val = int(widget.get_value())
        if int_val >= len(self._framerate_range) :
            int_val = len(self._framerate_range) -1
        # update project data : do callback call
        self._cb_framerate_changed( self._framerate_range[int_val])


    def refresh(self, framerate_list, framerate_selected) :
        """
        Update Scale bar and ajustment according new framerate range
        """

        self._framerate_range = framerate_list
        self._initial_range = framerate_selected
        
        #
        # recompute adjustment
        #
        initial_f_value = float(self._framerate_range.index(self._initial_range))

        adj = gtk.Adjustment(value =initial_f_value, 
                            lower = 0.0, 
                            upper = float(len( self._framerate_range)),
                            step_incr = 1.0,
                            page_incr = 1.0)

        self.set_adjustment(adj)

    
