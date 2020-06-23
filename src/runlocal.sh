#!/bin/sh
#sudo cp app.service /etc/systemd/system/app.service
#pip3 install -r requirements.txt

#cd /home/deployuser/loop-flask/src/
gunicorn wsgi:app \
    --workers 4 \
    --bind 0.0.0.0:5000 \
    --reload
#    gunicorn --workers 4 --bind --log-level=DEBUG --access-logfile "/home/deployuser/gunicorn_vals.log" unix:app.sock -m 007 wsgi:app
