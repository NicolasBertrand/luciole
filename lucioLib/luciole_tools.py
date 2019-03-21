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

import dircache
import fnmatch
import os.path
import os
import luciole_exceptions as M_EXCEP
import shutil

def filesInDir (path, pattern='*') :
    """ Return the list of file in a dir according pattern"""
    fl = dircache.listdir(path)
    #split to have only the file path
    ofile=fnmatch.filter(fl,pattern)
    return ofile

def mkdirs(path) :
    """ Make directory. Raise Exception if not possible """
    status = 1
    if not os.path.exists(path):
    	try :
	        os.makedirs(path)
        except OSError,err :
            raise M_EXCEP.LucioException, "Impossible de creer :" + path +"\n"+err.strerror + " on  : "+err.filename
            status = 0
	return status

def movef(src,dest) :
    """ Move file , Raise exception in case of failure"""
    status = None
    try :
        status = shutil.move(src,dest)
    except IOError,err:
        raise M_EXCEP.LucioException, "Impossible de deplacer :" + src +"\n"+err.strerror + " on  : "+err.filename
    return status

def copyf(src,dest) :
    """ Move file , Raise exception in case of failure"""
    status = None
    try :
        status = shutil.copy(src,dest)
    except IOError,err:
        raise M_EXCEP.LucioException, "Impossible de copier :" + src +"\n"+err.strerror + " on  : "+err.filename
    return status

def delf(file) :
    """ delete file , Raise exception in case of failure"""
    status = None
    try :
        status = os.remove(file)
    except OSError,err:
        raise M_EXCEP.LucioException, "Impossible de copier :" + src +"\n"+err.strerror + " on  : "+err.filename
    return status


class Singleton(object):
    """ A Pythonic Singleton """
    _singletons={}
    def __new__(cls, *args, **kwargs):
        if cls not in cls._singletons : 
            cls._singletons[cls] = super(Singleton,cls).__new__(cls)
        return cls._singletons[cls]

class SingletonType(type):
    def __call__(cls):
        if getattr(cls, '__instance__', None) is None:
            instance = cls.__new__(cls)
            instance.__init__()
            cls.__instance__ = instance
        return cls.__instance__
 
