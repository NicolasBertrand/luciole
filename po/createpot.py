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
"""
create_pot.py
Used for management of pot file
"""
import os, sys, glob

command = None
locale = None
try:
    command = sys.argv[1]
    locale  =  sys.argv[2]	
except IndexError:
    pass


os.chdir('po')

if command == 'compile':
    files = glob.glob('*.po')
    for f in files:
        print "working on language %s"%f
        l = os.path.splitext(f)
        os.system('mkdir -p -m 0777 %s/LC_MESSAGES' % l[0])
        print "Generating translation for %s locale" % l[0]
        os.system('msgmerge -o - %s luciole.pot | msgfmt -c -o %s/LC_MESSAGES/luciole.mo -' % (f, l[0]))
elif command == 'update_po' :
    os.system('intltool-update --pot --gettext-package=luciole --verbose ')
    files = glob.glob('*.po')
    for f in files:
        l = os.path.splitext(f)
        if l :
          print "Generating po file for %s locale" %l[0]
          os.system('msgmerge -U %s luciole.pot'%(f))
else :
    print "\n\n**********\n"
    print "Now edit luciole.pot, save it as <locale>.po, and post it on\n" \
        "our but tracker (https://bugs.launchpad.net/luciole/)\n\n" \
        "Thank you!"
os.chdir('..')
