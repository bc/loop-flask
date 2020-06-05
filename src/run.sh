#!/bin/sh
#sudo cp app.service /etc/systemd/system/app.service
#pip3 install -r requirements.txt

#sudo python3 app.py
#gunicorn --bind 0.0.0.0:5000 --debug-level=debug --access-logfile /home/deployuser/log.txt wsgi:app
cd /home/deployuser/loop-flask/src/
gunicorn wsgi:app \
    --workers 4 \
    --bind 0.0.0.0:5000 \
    --log-file /home/deployuser/gunicorn.log \
    --log-level=DEBUG \
    --reload

#    gunicorn --workers 4 --bind --log-level=DEBUG --access-logfile "/home/deployuser/gunicorn_vals.log" unix:app.sock -m 007 wsgi:app