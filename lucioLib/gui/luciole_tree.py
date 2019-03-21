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
#   The origin for this code is quod libet, file view.py,  Authors :Joe Wreschnig, Michael Urman
#

import gtk
import gobject
import pango

import capture_list_store as CLS

class MultiDragTreeView(gtk.TreeView):

    """
    This class origin is from quod Libet , file view.py . Author :Joe Wreschnig, Michael Urman
 
    TreeView with multirow drag support:
    * Selections don't change until button-release-event...
    * Unless they're a Shift/Ctrl modification, then they happen immediately
    * Drag icons include 3 rows/2 plus a "and more" count"""
    
    def __init__(self, *args):
        super(MultiDragTreeView, self).__init__(*args)
        self.connect_object(
            'button-press-event', MultiDragTreeView.__button_press, self)
        self.connect_object(
            'button-release-event', MultiDragTreeView.__button_release, self)
        self.connect_object('drag-begin', MultiDragTreeView.__begin, self)
        self.__pending_event = None

    def __button_press(self, event):
        if event.button == 1: return self.__block_selection(event)

    def __block_selection(self, event):
        x, y = map(int, [event.x, event.y])
        try: path, col, cellx, celly = self.get_path_at_pos(x, y)
        except TypeError: return True
        self.grab_focus()
        selection = self.get_selection()
        if ((selection.path_is_selected(path)
            and not (event.state & (gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK)))):
            self.__pending_event = [x, y]
            selection.set_select_function(lambda *args: False)
        elif event.type == gtk.gdk.BUTTON_PRESS:
            self.__pending_event = None
            selection.set_select_function(lambda *args: True)

    def __button_release(self, event):
        if self.__pending_event:
            selection = self.get_selection()
            selection.set_select_function(lambda *args: True)
            oldevent = self.__pending_event
            self.__pending_event = None
            if oldevent != [event.x, event.y]: return True
            x, y = map(int, [event.x, event.y])
            try: path, col, cellx, celly = self.get_path_at_pos(x, y)
            except TypeError: return True
            self.set_cursor(path, col, 0)

    def __begin(self, ctx):
        """ callback dor drag-begin signal 
        Enable the display of moved rows.

        At MAX 3 rows ares shown during motion.
        """
        model, paths = self.get_selection().get_selected_rows()
        MAX = 3
        if paths:
            icons = map(self.create_row_drag_icon, paths[:MAX])
            height = (
                sum(map(lambda s: s.get_size()[1], icons))-2*len(icons))+2
            width = max(map(lambda s: s.get_size()[0], icons))
            final = gtk.gdk.Pixmap(icons[0], width, height)
            gc = gtk.gdk.GC(final)
            gc.copy(self.style.fg_gc[gtk.STATE_NORMAL])
            gc.set_colormap(self.window.get_colormap())
            count_y = 1
            for icon in icons:
                w, h = icon.get_size()
                final.draw_drawable(gc, icon, 1, 1, 1, count_y, w-2, h-2)
                count_y += h - 2
            if len(paths) > MAX:
                count_y -= h - 2
                bgc = gtk.gdk.GC(final)
                bgc.copy(self.style.base_gc[gtk.STATE_NORMAL])
                final.draw_rectangle(bgc, True, 1, count_y, w-2, h-2)
                more = ("and %d more...") % (len(paths) - MAX + 1)
                layout = self.create_pango_layout(more)
                attrs = pango.AttrList()
                attrs.insert(pango.AttrStyle(pango.STYLE_ITALIC, 0, len(more)))
                layout.set_attributes(attrs)
                layout.set_width(pango.SCALE * (w - 2))
                lw, lh = layout.get_pixel_size()
                final.draw_layout(gc, (w-lw)//2, count_y + (h-lh)//2, layout)

            final.draw_rectangle(gc, False, 0, 0, width-1, height-1)
            self.drag_source_set_icon(final.get_colormap(), final)
        else:
            gobject.idle_add(ctx.drag_abort, gtk.get_current_event_time())
            self.drag_source_set_icon_stock(gtk.STOCK_MISSING_IMAGE)
            
class Luciole_tree(MultiDragTreeView) :
    """ capture list list of images """ 
        
    # 3 types of tagrets : same widget ; same application ; external ( not used) 
    
    # source target : type of allowed drag
    targets_source = [
                ('tree_model', gtk.TARGET_SAME_WIDGET, 0),
                ("text/x-luciole-images", gtk.TARGET_SAME_APP, 1),
                ("text/uri-list", 0, 2)]
    
    # source target : type of allowed drop
    targets_dest = [
                ('tree_model', gtk.TARGET_SAME_WIDGET, 0),
                ("text/x-luciole-images", gtk.TARGET_SAME_APP, 1),
                ("text/uri-list", 0, 2)]
    
    def __init__(self, capture_list , images_source, cb_on_treeview_change,cb_on_image_preview):
        """ 
        capture_list : list of image by name
        images_source : object with list of all images ( rush)
        """

        super(Luciole_tree, self).__init__()
        
        # save the callback 
        self.cb_on_treeview_change = cb_on_treeview_change
        self.cb_on_image_preview = cb_on_image_preview
        
        # Create the model (liststore)
        self._capture_list = capture_list
        self._images_source = images_source
        self.liststore = CLS.capture_list_store(self._capture_list, self._images_source, gtk.gdk.Pixbuf,str)
        self.set_model(self.liststore)

        # Create 1 columns :
        #   1st column  : thumbnail pixbuf
        self.cell = gtk.CellRendererPixbuf()
        # black color not good : The motion maks are noo seen
        # self.cell.set_property('cell-background','black')
        self.tvcolumn = gtk.TreeViewColumn('   Image',self.cell,pixbuf=0)
        # fix column size
        self.tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.tvcolumn.set_fixed_width(100)

        self.append_column(self.tvcolumn)
        #   2nd column : name of image
        #self.cell = gtk.CellRendererText()
        #tvcolumn = gtk.TreeViewColumn(' Image',self.cell,text=1)
        #self.append_column(tvcolumn)
       
        #Apparence :


        # Allow multiple selection
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        # Enable Drag and Drop
        self.enable_drop()

        # connect signals
        #    signal drag-data-get : origin of drag
        #    signal drag-data-received : where drag is done   
        self.connect("drag-data-get", self.__drag_data_get)
        self.connect("drag-data-received",
                              self.__drag_data_received)

        # why this signal ?
        # self.connect(
        #    'drag-leave', lambda s, ctx, time: s.parent.drag_unhighlight())
        self.connect('drag-motion', self.__drag_motion)
        
        self.connect('button-press-event', self._button_press)
        self.connect('key-press-event', self._key_press)
 
        

    def enable_drop(self, by_row=True):
        """ enable DnD , use of global DnD methods not treeview specific """
        # enable drag and drop 
        self.drag_source_set(
            gtk.gdk.BUTTON1_MASK, self.targets_source,
            gtk.gdk.ACTION_DEFAULT|
            gtk.gdk.ACTION_MOVE)
        
      
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, self.targets_dest,
                           gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)
        
        
        self.__drop_by_row = by_row


    def set_model(self, model):
        """ save the model """
        super(Luciole_tree, self).set_model(model)
        self.model = model


    def dump_images(self) :
        """ return the images list name"""
        l_list = [] 
        
        for row in self.liststore :
            l_list.append(row[1])
        
        return l_list

        
    
    def remove(self) :
        """ remove selected images """

        model, pathlist = self._get_selected_rows()
        if pathlist :
            # in model the remov function is for iter so transform pathlist in iter list 
            iterList = [ model.get_iter(path) for path in pathlist]
            for iter in iterList : model.remove(iter)
        
            # model trreview changed emit signal
            self.cb_on_treeview_change(self.dump_images())

   
    
    def __drag_motion(self, view, ctx, x, y, time):
        """ Used to know if Drag and Drop are action type MOVE or COPY.
            MOVE : for same WIDGET
            COPY : for another WIDGET
            
            This function indicates/highlight the destination.

            The origin of this function is the Treeview class SongList
            in quodLibet
        """
        if self.__drop_by_row:
            # This try/except strutcure allow the 
            # display a bar to indicate where the 
            # draged rows will be droped
            try:
                self.set_drag_dest_row(*self.get_dest_row_at_pos(x, y))
            except TypeError:
                if len(self.get_model()) == 0: 
                    path = 0
                else: 
                    # this TypeError exception manage the case of a motion over
                    # an empty zone of a treeview. 
                    # the last path is choosen 
                    path = len(self.get_model()) - 1
                self.set_drag_dest_row(path, gtk.TREE_VIEW_DROP_AFTER)
            
            # when drag on same treeview do a move
            # drag elsewhere is a copy
            if ctx.get_source_widget() == self: 
                kind = gtk.gdk.ACTION_MOVE
            else: 
                kind = gtk.gdk.ACTION_COPY
            ctx.drag_status(kind, time)
        else:
            self.parent.drag_highlight()
            ctx.drag_status(gtk.gdk.ACTION_COPY, time)
        # Why return True
        return True


    def __drag_data_delete(self, view, ctx):
        map(view.get_model(), self.__drag_iters)
        self.__drag_iters = []

    def __drag_data_get(self, view, ctx, sel, tid, etime):
        """ drag-data-get callback : get date on slected rows for drag
        Params :  
            view : the treeview widget
            ctx : the drag context cf. gtk.gdk.DragContext
            sel :	a gtk.SelectionData object
            tid : an integer ID for the drag
            etime : the time of the drag event
        """
        model, paths = self.get_selection().get_selected_rows()
        if tid == 1:
            # move on SAME_APP from widget to widget
            # get image name
            # image name ares transmitted to another widget
            images = [model[path][1] for path in paths]
            sel.set("text/x-luciole-images", 8, "\x00".join(images))
        elif tid == 0 :
            # move inside treeviw 
            sel.set("tree_model", 8, " SAME_WIDGET")
        else:
            # move to external
            # action to be defined
            # in quod libet uri are send 
            pass


    def _get_selected_rows(self) :
        """ get selected rows , sort it ans rever list """
        treeselection = self.get_selection()
        model, pathlist = treeselection.get_selected_rows()
        if pathlist : pathlist.sort()
        return model, pathlist

    def _move_rows(self,pathlist,path,position,model) :
        """ Move rows in pathlist after or before path acorring value of
        position """
        if path != None :
            # nbd@tf number of pathliostreverse to optimize ... check wiyh  
            # _get_selected_rows , move_up and moved_down function
            if position == gtk.TREE_VIEW_DROP_AFTER :
                # path list is reverse sorted when action is drop after
                # this is needed to ensure, during moving loop, element 
                # moved in the right order 
                # first Last item is copied after drop, than the previous  after drop etc ...
                # if list is A, B, C, D, E  and B and C have to be moved after D so :
                # first move C inserted after D : A, B, D, C, E
		        # second move B inserted after D : A, D, B, C, E 
                pathlist.reverse()
            # get iter from dest row
            iter = self.model.get_iter(path)
            # create a list of slected iters, best to work with iters 
            # absolute id according who change after move operation
            selected_iters = [self.model.get_iter(path_s) for path_s in pathlist] 
            for selected_iter in selected_iters :
                if ( position == gtk.TREE_VIEW_DROP_BEFORE
                        or 
                    position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE
                    ):
                    model.move_before(selected_iter,
                                            iter)
                else:
                    model.move_after(selected_iter,
                                            iter)
                    #scroll also to new position
                    self.scroll_to_cell(self.model.get_path(selected_iter))
            # model trreview changed emit signal
            self.cb_on_treeview_change(self.dump_images())

    def _insert_rows(self, image_names, path, position, model ) :
        """ Inert rows in treeview  after or before path acorring value of
        position """
        if path != 0 :
            # path, position = drop_info
            # get iter from dest row
            if position == gtk.TREE_VIEW_DROP_AFTER :
                # image_names list is reverse  when action is drop after
                # this is needed to ensure, during moving loop, element 
                # moved in the right order 
                # first Last item is copied after drop, than the previous  after drop etc ...
                # if list is A, B, C, D, E  and B and C have to be moved after D so :
                # first move C inserted after D : A, B, D, C, E
                # second move B inserted after D : A, D, B, C, E 
                image_names.reverse()

            iter = model.get_iter(path)
            # reverse image list cf. reason in "if" statement
            #image_names.reverse()
            for image_name in image_names :
                image = self._images_source.get_image(image_name)
                #move each selected rows BEFORE or AFTER dest row according position
                if ( position == gtk.TREE_VIEW_DROP_BEFORE
                    or 
                    position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE
                    ):
                    model.insert_before(iter,
                                        [image.pixbuf_thumb,image.name])
                else:
                    model.insert_after( iter,
                                        [image.pixbuf_thumb,image.name])

            
            # scroll to drop poistion
            self.scroll_to_cell(path)        
            # model treeview changed emit signal
        else :
            # No row  on treeview so append it
            for image_name in image_names :
                image = self._images_source.get_image(image_name)
                model.append([image.pixbuf_thumb,image.name])
            
            # scroll to last cell on treeview
            self.scroll_to_cell( ( len(model)-1 , ) )
        # model treeview changed emit signal
        self.cb_on_treeview_change(self.dump_images())



    def __drag_data_received(self, treeview, context, x, y, selection,
                                info, etime):
        """ drag-data-received callback 

        Params :  
            treeview : the treeview that received the signal
            context : the gtk.gdk.DragContext
            x : the X position of the drop
            y : the Y position of the drop
            selection : a gtk.SelectionData object
            info : an integer ID for the drag
            etime : the time of the drag event
        """

		data = selection.data
        if info == 0 : 
            # move from same widget
            model, pathlist = self._get_selected_rows()
            
            # get info on dest row position
            try: 
                path, position = treeview.get_dest_row_at_pos(x, y)
            except TypeError:
                # this TypeError exception manage the case of a drop in the empty zone
                # of a treeview
                # the last path is choosen 
                path = max(0, len(model) - 1)
                position = gtk.TREE_VIEW_DROP_AFTER
            # now move the rows in path list
            self._move_rows(pathlist,path,position,model)

        elif info == 1 :
            # get data from another widget
            # copy operation
            image_names = selection.data.split("\x00")
             # get info on dest row position
            try: 
                path, position = treeview.get_dest_row_at_pos(x, y)
            except TypeError:
                # this TypeError exception manage the case of a drop in the empty zone
                # of a treeview
                # the last path is choosen
                path = max(0, len(self.model) - 1)
                position = gtk.TREE_VIEW_DROP_AFTER
            self._insert_rows( image_names, path, position, self.model )

    def append_image(self,image) :
        """ append an image as row on treeview """
        self.model.append([image.pixbuf_thumb,image.name])
        
        # scroll to the last object i.e. the object appended
        self.scroll_to_cell( ( len(self.model)-1 , ) )
 
        # model treeview changed emit signal
        self.cb_on_treeview_change(self.dump_images())


    
    def _button_press(self,view,event) :
        if event.type ==  gtk.gdk._2BUTTON_PRESS :
            x, y = map(int, [event.x, event.y])
            try: path, col, cellx, celly = view.get_path_at_pos(x, y)
            except TypeError: return True
            # Image preview request on double click
            self.cb_on_image_preview(self._images_source.get_image(self.model[path][1]))


    def _key_press(self,view,event) :
        pass
