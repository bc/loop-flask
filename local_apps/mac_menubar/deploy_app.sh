#!/bin/bash
cd /Users/briancohn/Documents/GitHub/bc/loop-flask/local_apps/mac_menubar || echo "Error: Mac Menubar Path doesn't exist"

# Remove old builds
rm -rf build dist

# Build app
python3 setup.py py2app

# Compress a zip file to the Drive Folder
zip -r -y dist/temp.zip dist/SpookyLoop.app
mv dist/temp.zip "/Volumes/GoogleDrive/My Drive/kaspect2020/spookyloop_builds/spookyloop_mac.zip"

# Run locally with a viable UUID (not necessarily valid on server though)
./dist/SpookyLoop.app/Contents/MacOS/SpookyLoop loopit://26b78511-8690-4d07-b852-464ce10372b2