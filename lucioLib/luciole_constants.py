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

# Luciole constants file

from gettext import gettext as _

########################################
# Hardware constants
########################################
FAKE = 0
DVCAM = 1
WEBCAM = 2
DIGICAM= 3
HardType=(FAKE,DVCAM,WEBCAM,DIGICAM)
HardTypeName=(
        "FAKE",
        "DVCAM",
        "WEBCAM",
        _("OTHER DEVICE"),
        )

########################################
# Image screen display constants
########################################
SCREEN_BOTH = 0     # when action on both screen is required
SCREEN_CAMERA = 1   # input stream display
SCREEN_PREVIEW  = 2 # preview screen 


########################################
# LUCIOLE PROJECT CONSTANTS
########################################
PROJECT_NOT_MODIFIED = 0
PROJECT_MODIFIED = 1
ACQUIRED_IMAGE_NAME = 'capture.jpeg'
# name for resized capture
ACQUIRED_IMAGE_NAME_RZ = 'capture_rz.jpeg'
RUSH_FILENAME_TPL = "rush_%05d.jpeg"
TMP_DIR = 'tmp'

(CAPTURE,MONTAGE) = range(2) 

########################################
# VIDEO FORMATS
########################################
VIDEO_PAL_RES = (720,576)
VIDEO_PAL_FPS = 25
VIDEO_FPS_TABLE = {
                0 : ("0",0),
                1 : ("1",25),
                2 : ("2.5",10),
                3 : ("5",5),
                4 : ("12.5",2),
                5 : ("25",1)
                }  


########################################
# IMAGE FORMATS
########################################
THUMB_RATIO         =   4       # ration normal/thumbnail. To set size ot thumbnail images in treeview.
# clor in rgb format muliply by 255 each level to go in gtk.gdk.Color format
THUMB_COLOR_RATIO = 256
THUMB_TEXT_COLOR    =   (
                            191 * THUMB_COLOR_RATIO,  
                            244  * THUMB_COLOR_RATIO,  
                            75 * THUMB_COLOR_RATIO
                        )     
THUMB_TEXT_SIZE     =   8200                # text size
THUMB_TEXT_FAMILY   =   'sans'              # font family


ALPHA_DEFAULT = 0.4 # default alpha value used for mixer

