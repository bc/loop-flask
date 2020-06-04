#!/bin/sh
sudo cp src/app.service /etc/systemd/system/app.service
pip3 install -r requirements.txt
sudo systemctl status app
sudo systemctl stop app
sudo systemctl disable app
sudo systemctl start app
sudo systemctl reload app
sudo systemctl enable app
#sudo python3 app.py
#gunicorn --bind 0.0.0.0:5000 wsgi:app