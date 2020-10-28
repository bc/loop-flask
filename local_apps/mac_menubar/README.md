# to build the mac exe:
``  
Right click and select open to avoid security disclaimer message from osx

# install dependencies into a venv
```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
 #to run
python3 SpookyLoopMenulet.py
# to build .app
python3 setup.py py2app
```

