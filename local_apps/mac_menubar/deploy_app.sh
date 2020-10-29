#!/bin/bash
cd /Users/briancohn/Documents/GitHub/bc/loop-flask/local_apps/mac_menubar
python3 setup.py py2app
cd /Users/briancohn/Documents/GitHub/bc/loop-flask/local_apps/mac_menubar/dist/
zip -r -y temp.zip SpookyLoop.app
cp temp.zip "/Volumes/GoogleDrive/My Drive/kaspect2020/spookyloop_builds/spookyloop_mac.zip"
