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
luciole.py :
    Main file of application luciole
"""
from optparse import OptionParser
from optparse import make_option

import lucioLib
import logging
import sys
import gtk
import os.path

try:  # Import Psyco if available
    import psyco
    psyco.full()
except ImportError:
     pass

def init_logging(is_verbose = False, log_to_file = False ):
    
    # create logger with "spam_application"
    logger = logging.getLogger("luciole")
    if is_verbose == True :
        logger.setLevel(logging.DEBUG)
    else :
        logger.setLevel(logging.INFO)
            
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - (%(filename)s, %(lineno)d) - %(message)s")
    
    # add handler to gui
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # add handler to file
    if log_to_file == True :
        logger.setLevel(logging.DEBUG)
        if is_verbose == False :
            # if verbositoy option is not set only log to file
            ch.setLevel(logging.WARNING)

        # create file handler which logs even debug messages
        home_dir = os.path.expandvars('$HOME')
        home_dir = os.path.join(home_dir,'.luciole')

        if os.path.isdir(home_dir) :
            fh = logging.FileHandler(os.path.join(home_dir,"luciole.log"))
            fh.setLevel(logging.DEBUG)
            log_to_file = True
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logger.info("Starting log to file")

    
    return logger
    
def luciole_option_parser() :

    option_list = [
        make_option("-f", "--file",
                action="store", type="string", dest="filename",
				help=u'"Luciole project file (.xml) to load', metavar="FILE"),
        make_option("-v", "--verbose",
                action="store_true", dest="is_verbose", default=False,
				help=u'Toogle verbosity'),
        make_option("-l", "--logfile",
                action="store_true", dest="is_logfile", default=False,
				help=u'Log verbosity/luciole data to  $HOME/luciole.log')
        ]

    usage = "usage: %prog [options] "
	parser = OptionParser(option_list=option_list,usage=usage)
    (options, args2) = parser.parse_args()
    return options

def main(args) :
    """ Main function of program """

    #parse options
    options = luciole_option_parser()

    try :
        gtk.gdk.threads_init()
    except :
        print " No Threading available with pyGtk, exit !!!"
        sys.exit(1)


       
    # init logging
    logger = init_logging(options.is_verbose, log_to_file = options.is_logfile)

    
    logger.info("Starting luciole")

    # init controller

    app_ctrller = lucioLib.Luciole_controller()

    #load of a project 
    gtk.gdk.threads_enter()
    if ( options.filename and os.path.exists(options.filename)) :
        X= app_ctrller.open_project(options.filename)
    
    gtk.main()
    gtk.gdk.threads_leave()

    logger.info("Leaving luciole")

#import cProfile
#cProfile.run('main(None)', 'profile.out')  

if __name__ == '__main__' :
    sys.exit(main(sys.argv))
