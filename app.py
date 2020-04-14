import os
import pdb
# app.py
from flask import Flask, request, jsonify, abort, Response
import time
import uuid
import requests
from os import listdir
from os.path import isfile, join

app = Flask(__name__)


# helper functions
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
            # ...jump back the read byte plus one more.
            f.seek(-2, os.SEEK_CUR)
        last = f.readline()         # Read last line.
    return last.decode("utf-8").rstrip().split(",")

# returns the list of tokens in the userdata folder


def active_tokens():
    return basenames(get_files("userdata"))


def get_telegram_token(loop_token):
    # TODO make non-hardcoded. will only ping brian via bot.
    return("911638276:AAEe7XkH3B_YNg1mpfRZsjt0jm7QX3nZaCg")


def get_telegram_chat_id(loop_token):
    # TODO make non-hardcoded. will only ping brian via bot.
    return(97634578)


def push_telegram_notification(loop_token, message):
    telegram_token = get_telegram_token(loop_token)
    telegram_chat_id = get_telegram_chat_id(loop_token)
    url = "https://api.telegram.org/bot%s/sendMessage" % telegram_token
    payload = 'chat_id=%s&text=%s' % (telegram_chat_id, message)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text.encode('utf8'))


def is_normalized(float_number):
    return float_number >= 0.0 and float_number <= 1.0
###############
# API


@app.route('/listen/', methods=['GET'])
def listen():
    token = request.args.get("token")
    if token not in active_tokens():
        abort(Response(
            "Error: The token you tried (%s) is inactive or nonexistent. Make a new one." % token, status=401))

    time, obs = get_last_observation("userdata/%s.txt" % token)
    return jsonify({
        "unixtime": float(time),
        "value": float(obs)
    })

# from tinydb import TinyDB, Query
# @app.route('/record_delta/', methods=['POST','GET'])
# def record_delta():

#     # Get the input token
#     try:
#         token = request.args.get("token")
#         if token not in active_tokens():
#             abort(Response(
#                 "Error: The token you tried (%s) is not active. Go make a new one." % token, status=401))
#     except Exception as e:
#         abort(Response("Error: The token wasn't present in your request.", status=401))

#     # Make sure input is a parseable float number
#     try:
#         delta_seconds = float(request.args.get("delta_seconds"))
#         process_id = str(request.args.get("process_id"))
#     except ValueError:
#         abort(Response("Error: The input you tried is not parseable as a float or a str :(. Make sure the delta is recorded in seconds, and that the parameter is 'obs'", status=401))


#     if obs in [0.0, 1.0] and token == "f8992e21-a350-40a5-986f-5221412bdad8":
#         print("Sending push notification to bc's phone")
#         push_telegram_notification(token, "@ %s percent" % str(obs*100))
#         return "posted & notified"
#     else:
#         return "posted"

@app.route('/update/', methods=['POST'])
def update():

    # Get the input token
    try:
        token = request.args.get("token")
        if token not in active_tokens():
            abort(Response(
                "Error: The token you tried (%s) is not active. Go make a new one." % token, status=401))
    except Exception as e:
        abort(Response("Error: The token wasn't present in your request.", status=401))

    # Make sure input is a parseable float number
    try:
        obs = float(request.args.get("obs"))
    except ValueError:
        abort(Response("Error: The input you tried is not parseable as a float. Make sure it's also between 0.0 and 1.0, and that the parameter is 'obs'", status=401))

    # Make sure the float input is between 0 and 1
    if not is_normalized(obs):
        abort(Response("Error: you can only push float numbers between 0 and 1 (e.g. 0.25 or 0.70). You entered (%s)." % obs, status=401))

    with open("userdata/%s.txt" % token, "a") as myfile:
        myfile.write("%s,%s\n" % (time.time(), obs))

    if obs in [0.0, 1.0] and token == "f8992e21-a350-40a5-986f-5221412bdad8":
        print("Sending push notification to bc's phone")
        push_telegram_notification(token, "@ %s percent" % str(obs*100))
        return "posted & notified"
    else:
        return "posted"


def gen_new_token():
    new_token = uuid.uuid4()
    user_file = open("userdata/%s.txt" % new_token, "a")
    now = time.time()
    L = ["APN:unknown\n", "init:%s\n" % now]
    user_file.writelines(L)
    user_file.write("%s,%s\n" % (time.time(), -1))
    user_file.close()
    return new_token


@app.route('/newtoken/', methods=['POST'])
def newtoken():
    return jsonify({
        "token": f"%s" % gen_new_token(),
        "METHOD": "POST"
    })

# A welcome message to test our server


@app.route('/')
def index():
    myToken = gen_new_token()
    return "<h1>Token: %s</h1><br><img src=\"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=%s\"><br>" % (myToken, myToken)


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, host="0.0.0.0", port=80)
