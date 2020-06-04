#!/bin/sh
cd flaskapp
#pip3 install -r requirements.txt
#sudo python3 app.py
gunicorn --bind 0.0.0.0:5000 wsgi:app