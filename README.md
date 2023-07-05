# Loop
I often need to run big XCode builds, lengthy download scripts, installations, etc.

With *Loop*, I can set up a 'predicate' for CPU<20%, scan a QR code on my phone, and I'll get a push notification when the build is done (or crashed).

# Run it
```bash
pip install -r requirements.txt
gunicorn wsgi:app \
    --workers 4 \
    --bind 0.0.0.0:80 \
    --reload \
    --log-file /tmp/gunicorn.log \
    --log-level=DEBUG \
```

# Components
1. Python Flask API
2. Web/Mobile Frontend that predicts the completion ETA using data from progress updates & linear regression.
3. Menubar Application that surveys CPU %
