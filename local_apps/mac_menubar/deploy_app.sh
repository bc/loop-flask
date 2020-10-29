#!/bin/bash
python3 setup.py py2app
zip -r -X "/Volumes/GoogleDrive/My Drive/kaspect2020/spookyloop_builds/spookyloop_mac_$(uuidgen).zip" "/Users/briancohn/Documents/GitHub/bc/loop-flask/local_apps/mac_menubar/dist/SpookyLoop.app"
