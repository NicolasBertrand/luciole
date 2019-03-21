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
    webcam_detection.py :
    Webcam detection module
"""
import gudev
import glib

import gst



class WebcamDetection(object) :

    def _get_webcam_devices(self) : 
        """ getter for webcam_devices"""
        return self._webcam_devices
    webcam_devices = property(  _get_webcam_devices,
                                None,
                                None,
                                "webcam devices description")

    def __init__(self) :
        """ class init"""
        
        self._webcam_devices = []
    
    def detect_webcams(self) :
        client = gudev.Client(["block", "usb"])
        devices = client.query_by_subsystem("video4linux")
        self.device_information(devices)

        return len(self._webcam_devices)

    def device_information(self, devices) :
        
        for _device in devices :
            _device_desc = {}
            _device_desc['device-file'] = _device.get_device_file()
            
            _v4lversion = self._get_prop(_device, 'ID_V4L_VERSION')
            print type(_v4lversion)
            
            if int(_v4lversion) in (1, 2) :
                # getting information related to v4l
                if _v4lversion == 1 : 
                    _device_desc['v4ldriver'] = 'v4lsrc'
                else :
                    _device_desc['v4ldriver'] = 'v4l2src'
             
                _device_desc['name'] = self._get_prop(_device, 'ID_V4L_PRODUCT')
                if not ':capture:' in self._get_prop(_device, "ID_V4L_CAPABILITIES") :
                    self.error('Device %s seems to not have the capture capability',
                            _device_desc['device-file'])
                    continue
            else :
                self.error(
                    "Fix your udev installation to include v4l_id, ignoring %s",
                    _device_desc['device-file'])
                continue
            # append selected element
            self._webcam_devices.append(_device_desc)

            

    def _get_prop(self, device, key_p) :
        _val = "UNKNOW_%s" % key_p
        if device.has_property(key_p) :
            _val = device.get_property(key_p)
        return _val

   

if __name__ == '__main__' :
    
    CamDetect = WebcamDetection()
    _nb = CamDetect.detect_webcams()
    print "Find %s devices"% _nb  
    for _cam in CamDetect.webcam_devices :
        print _cam


