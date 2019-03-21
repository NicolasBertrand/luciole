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
import gtk

import luciole_exceptions as L_EXCEP
import os.path

#i18n
from gettext import gettext as _

class luciole_recent(object):
    """ Manage recent projects, display
    5 projects can be dsiplayed at max """

    __MAX_PROJECT = 5
    __ui_recent_path = '/menubar1/menu_file/menu_file_open_recent'

    def __init__(self,ProjectList,gui,cb_open,conf) :
        """ Init of module """
        self.__ProjectList = list()
        self.gui = gui 
        self._open_recent_menu = self.gui.open_recent_menu

        self._cb_open = cb_open     # callback for open project 
        self._conf = conf

        # create a List of valid projects : i.e Existing projects
        _valid_project = []
        if ProjectList != [] :
            for project in ProjectList :
                if os.path.exists(project) :
                    _valid_project.append(project)

        if len(ProjectList) <= self.__MAX_PROJECT : self.__ProjectList.extend(_valid_project)
        
        

        self._displayRecentProject()

    
    def add_project(self,project) :
        """ add a project ro recent used projects """
        # verify project is not yet present
        # count shall return 0
        if self.__ProjectList.count(project) == 0 :    
            if len(self.__ProjectList) >= self.__MAX_PROJECT : 
                # remove older project
                self.__ProjectList.pop()
            #insert project
            self.__ProjectList.insert(0,project)
            self._displayRecentProject()
            self._conf.update_last_project(self.__ProjectList)

    def _displayRecentProject(self) :
        """ Update submenu widget with recently used projects """
        # Get submenus
        Menu = self._open_recent_menu.get_submenu()
        MenuChilds = Menu.get_children()
        # first clean menu by removing all menu childs
        for child in MenuChilds : Menu.remove(child)
        ## then add menuItem for eachProject
        for project in self.__ProjectList :
            MenuItem = gtk.MenuItem(project)
            MenuItem.connect("activate",self.menu_activate,project)
            Menu.append(MenuItem)
            MenuItem.show()

    def menu_activate(self,widget,project):
        """ Callback on menu activation. open selected project """
        try :
            self._cb_open(project)
        except L_EXCEP.LucioException,err :
            import gui as LTK
            msg = _("Project %s no more exist"%project)
            LTK.Dialog.ErrorMessage(self.gui.window, msg)

