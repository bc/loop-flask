import os
import pdb
# app.py
from flask import Flask, request, jsonify, abort, Response
import time
import uuid
from os import listdir
from os.path import isfile, join

app = Flask(__name__)


#helper functions
################
# gets list of strings, one for each filename in a target directory
def get_files(mypath):
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return onlyfiles

# trims filename extensions from a list of filenames, including the dot
def basenames(file_list):
    return [os.path.splitext(f)[0] for f in file_list]

def get_last_observation(filepath):
    with open(filepath, "rb") as f:
        first = f.readline()        # Read the first line.
        f.seek(-2, os.SEEK_END)     # Jump to the second last byte.
        while f.read(1) != b"\n":   # Until EOL is found...
            f.seek(-2, os.SEEK_CUR) # ...jump back the read byte plus one more.
        last = f.readline()         # Read last line.
    return last.decode("utf-8").rstrip().split(",")

# returns the list of tokens in the userdata folder
def active_tokens():
    return basenames(get_files("userdata"))
###############
#API
@app.route('/listen/', methods=['GET'])
def listen():
    token = request.args.get("token")
    if token not in active_tokens():
        abort(Response("Error: The token you tried (%s) is not active. Go make a new one."%token, status=401))

    time, obs = get_last_observation("userdata/%s.txt"%token)
    return jsonify({
        "unixtime": float(time),
        "value": float(obs)
        })

@app.route('/update/', methods=['POST'])
def update():
    token = request.args.get("token")
    if token not in active_tokens():
        abort(Response("Error: The token you tried (%s) is not active. Go make a new one."%token, status=401))

    obs = request.args.get("obs")
    with open("userdata/%s.txt"%token, "a") as myfile:
        myfile.write("%s,%s\n"%(time.time(),obs))
    return "posted"

def gen_new_token():
    new_token = uuid.uuid4()
    user_file = open("userdata/%s.txt"%new_token,"a")
    now = time.time()
    L = ["APN:unknown\n", "init:%s\n"%now]
    user_file.writelines(L) 
    user_file.write("%s,%s\n"%(time.time(),-1))
    user_file.close()
    return new_token

@app.route('/newtoken/', methods=['POST'])
def newtoken():
    return jsonify({
        "token": f"%s"%gen_new_token(),
        "METHOD" : "POST"
        })

# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Token: %s</h1><br><img src=\"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=%s\"><br>"%(gen_new_token(),gen_new_token())

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, host = "0.0.0.0",port=5000)
