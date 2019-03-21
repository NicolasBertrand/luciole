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
#
# Project      : Luciole
#
# Url          : <A HREF="http://https://launchpad.net/luciole"> Location </A>
#
# File         : Makefile
#
# Owner        : Nicolas Bertrand 
#
# Type         : makefile
#
#
# Name          : Makefile  
#
# Synopsis      : make 
#
# Arguments     : none
#
# Description   : Makefile for building luciole and installation of luciole 
#
# See Also      : 
#


SOURCE_DIR=./
PREFIX ?= /usr
LIBDIR ?= /lib
BASEDIR= `basename $(PWD)`

all: compile trans-compile
	@echo "Done"
	@echo "Type: 'make install' now"

version_update :
	bzr version-info --format python > _version.py
compile:
	python -m compileall lucioLib
	python -m py_compile luciole.py
	python -m py_compile _version.py
	python -O -m compileall lucioLib
	python -O -m py_compile luciole.py
	python -O -m py_compile _version.py

trans-compile :
	python po/createpot.py compile

trans-po-update :
	python po/createpot.py update_po

make-install-dirs: 
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_export
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_gst
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/gui
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lucioWebCamDetect
	mkdir -p $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/controller
	mkdir -p $(DESTDIR)$(PREFIX)/share/
	mkdir -p $(DESTDIR)$(PREFIX)/share/pixmaps
	mkdir -p $(DESTDIR)$(PREFIX)/share/applications
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/templates
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/images
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/sounds
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/po
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/ui
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/themes
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/themes/Tropical
	mkdir -p $(DESTDIR)$(PREFIX)/share/luciole/themes/Tropical/icons
	mkdir -p $(DESTDIR)$(PREFIX)/share/man/man1

install: make-install-dirs
	install -m 644 $(CURDIR)/$(SOURCE_DIR)luciole.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole
	install -m 644 $(CURDIR)/$(SOURCE_DIR)_version.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole
	install -m 644 $(CURDIR)/$(SOURCE_DIR)ui/*.glade $(DESTDIR)$(PREFIX)/share/luciole/ui
	install -m 644 $(CURDIR)/$(SOURCE_DIR)images/*.png $(DESTDIR)$(PREFIX)/share/luciole/images
	install -m 644 $(CURDIR)/$(SOURCE_DIR)sounds/*.ogg $(DESTDIR)$(PREFIX)/share/luciole/sounds
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lcl_export/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_export
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lcl_export/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_export
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lcl_gst/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_gst
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lcl_gst/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lcl_gst
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/gui/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/gui
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/gui/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/gui
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lucioWebCamDetect/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lucioWebCamDetect
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/lucioWebCamDetect/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/lucioWebCamDetect
	install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/controller/*.py $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/controller
	-install -m 644 $(CURDIR)/$(SOURCE_DIR)lucioLib/controller/*.py[co] $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole/lucioLib/controller
	install -m 644 $(CURDIR)/$(SOURCE_DIR)templates/*.xml $(DESTDIR)$(PREFIX)/share/luciole/templates
	install -m 644 $(CURDIR)/$(SOURCE_DIR)templates/*.kdenlive $(DESTDIR)$(PREFIX)/share/luciole/templates
	install -m 644 $(CURDIR)/$(SOURCE_DIR)templates/*.xptv $(DESTDIR)$(PREFIX)/share/luciole/templates
	install -m 644  $(CURDIR)/$(SOURCE_DIR)luciole.desktop $(DESTDIR)$(PREFIX)/share/applications/
	install -m 644 $(CURDIR)/$(SOURCE_DIR)images/luciole.xpm  $(DESTDIR)$(PREFIX)/share/pixmaps/
	install -m 644 $(CURDIR)/$(SOURCE_DIR)themes/*.rc $(DESTDIR)$(PREFIX)/share/luciole/themes/
	install -m 644 $(CURDIR)/$(SOURCE_DIR)themes/Tropical/icons/*.png $(DESTDIR)$(PREFIX)/share/luciole/themes/Tropical/icons/

	cd $(DESTDIR)$(PREFIX)/bin && \
	  /bin/echo -e \
	    "#!/bin/sh\n" \
	    "cd $(PREFIX)/share/luciole\n" \
	    "exec python $(PREFIX)$(LIBDIR)/luciole/luciole.py \"\$$@\"" \
	    > luciole && \
	  chmod 755 luciole
	# traduction
	for f in `find po -name luciole.mo` ; do \
	  install -d -m 755 \
	    `echo $$f | sed "s|^po|$(DESTDIR)$(PREFIX)/share/luciole/po|" | \
	      xargs dirname` && \
	  install -m 644 $$f \
	    `echo $$f | sed "s|^po|$(DESTDIR)$(PREFIX)/share/luciole/po|"` ; \
	  done
tarball: clean
	@echo "Creating tarball $(BASEDIR).tar.gz archive in parent dir "
	@cd .. && tar --exclude .bzr --exclude .bzrignore --exclude debian -czf $(BASEDIR).tar.gz $(BASEDIR)

debian-orig: clean cleanbzr
	@echo "Creating debian $(BASEDIR).orig.tar.gz archive in parent dir"
	@cd .. && tar --exclude .bzr --exclude .bzrignore --exclude debian  -czf $(BASEDIR).orig.tar.gz $(BASEDIR)
 
uninstall:
	rm -rf $(DESTDIR)$(PREFIX)/share/luciole
	rm -rf $(DESTDIR)$(PREFIX)$(LIBDIR)/luciole
	rm -rf $(DESTDIR)$(PREFIX)/bin/luciole
	rm -f $(DESTDIR)$(PREFIX)/share/applications/luciole.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/pixmaps/luciole.xpm

clean :
	@echo "Removing temporary files" 
	@find . -name "*.py[co]" -exec rm -f {} \;
	@find . -name "*~" -exec rm -f {} \;
	@find . -name "*.swp" -exec rm -f {} \;

cleanbzr :
	rm -rf .bzr
	rm -f .bzrignore



