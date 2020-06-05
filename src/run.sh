#!/bin/sh
sudo cp app.service /etc/systemd/system/app.service
pip3 install -r requirements.txt

#sudo python3 app.py
#gunicorn --bind 0.0.0.0:5000 --debug-level=debug --access-logfile /home/deployuser/log.txt wsgi:app
