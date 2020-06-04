import os
from flask import Flask, request, jsonify, abort, Response, render_template
import time
import uuid
import requests
from os import listdir
from os.path import isfile, join

app = Flask(__name__)
path_to_datafolder = "/Users/Olive/Documents/GitHub/bc/loop-backend/data"

@app.route('/')
def website_root():
    return render_template("index.html")

# helper functions
#################
# gets list of strings, one for each filename in a target directory
def get_files(mypath):
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return onlyfiles


# Trims filename extensions from a list of filenames, including the dot
# Useful for getting the list of guid values from a folder
def base_names(file_list):
    return [os.path.splitext(f)[0] for f in file_list]


def get_last_observation_line(filepath, valType="OBS"):
    with open(filepath, "rb") as f:
        observations = [x.decode("utf-8") for x in f.readlines()]
        v = [x for x in observations if x.startswith(valType)][-1].rstrip().split(",")
        return v

# returns the list of tokens in the userdata folder


def active_tokens(path_to_datafolder: str):
    return base_names(get_files(path_to_datafolder))


def get_telegram_token(loop_token: str):
    # TODO make non-hardcoded. will only ping brian via bot.
    return "911638276:AAEe7XkH3B_YNg1mpfRZsjt0jm7QX3nZaCg"


def get_telegram_chat_id(loop_token):
    # TODO make non-hardcoded. will only ping brian via bot.
    return 97634578


def push_telegram_notification(loop_token, message):
    telegram_token = get_telegram_token(loop_token)
    telegram_chat_id = get_telegram_chat_id(loop_token)
    url = "https://api.telegram.org/bot%s/sendMessage" % telegram_token
    payload = 'chat_id=%s&text=%s' % (telegram_chat_id, message)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.json()["ok"]:
            return True
        else:
            return False
    except:
        return False


def is_normalized(float_number):
    return float_number >= 0.0 and float_number <= 1.0


###############
# API


@app.route('/listen/', methods=['GET'])
def listen():
    token = validate_token(request)
    targetFilepath = os.path.join(path_to_datafolder, "%s.txt" % token)

    valtype, time, obs = get_last_observation_line(targetFilepath, "OBS")
    valtype, CPUtime, CPUname, CPUobs = get_last_observation_line(targetFilepath, "CPU")

    payload = {"OBS": {
        "unixtime": float(time),
        "value": float(obs)
    },
        "CPU": {
            "unixtime": float(CPUtime),
            "name": str(CPUname),
            "percent": float(CPUobs)
        }
    }
    return jsonify(payload)


@app.route('/process_over_request_ping/', methods=['GET'])
def process_over_request_ping():
    token = validate_token(request)
    process_name: str = try_parse_object_as(request.args.get("process_name"), str)
    # log this completion to the user's data
    targetFilepath = os.path.join(path_to_datafolder, "%s.txt" % token)
    with open(targetFilepath, "a") as myfile:
        # TODO should do some cleanup of the existing logs as we
        # know the user's completed tracking that process
        myfile.write(compose_CPU(process_name, -1))
    telegram_outcome = push_telegram_notification(token, "Process %s done" % process_name)
    if telegram_outcome:
        return "notified_of_process_end"
    else:
        return "notification_failed"


@app.route('/update/', methods=['GET'])
def update():
    token = validate_token(request)
    obs: float = try_parse_object_as(request.args.get("obs"), float)

    # Make sure the float input is between 0 and 1
    if not is_normalized(obs):
        abort(Response(
            "Error: you can only push float numbers between 0 and 1 (e.g. 0.25 or 0.70). You entered (%s)." % obs,
            status=401))
    # make the observation
    targetFilepath = os.path.join(path_to_datafolder, "%s.txt" % token)
    with open(targetFilepath, "a") as myfile:
        myfile.write(compose_OBS(obs))
    # notify if it's a boundary observation (just started or just finished)
    if obs in [0.0, 1.0] and token == "ffdc1f83-66b0-4386-a1d3-d8b924274b28":
        print("Sending push notification to bc's phone")
        telegram_outcome = push_telegram_notification(token, "@ %s percent" % str(obs * 100))
        if telegram_outcome:
            return "posted; notified"
        else:
            return "posted; notification failed"

    else:
        return "posted"


def compose_OBS(obs):
    return "OBS,%s,%s\n" % (time.time(), obs)


@app.route('/process_update/', methods=['POST'])
def process_update():
    # Get the input token
    token = validate_token(request)
    # TODO create assertions for what the json looks like
    top_process = request.json
    if top_process == "process_not_found":
        print("it's done! ping person")
        return ("completion acknowledged")
    cpu_val: float = try_parse_object_as(top_process['cpu'], float)  # 0 to e.g. 1600%
    process_name: str = try_parse_object_as(top_process['name'], str)

    # Make the observation
    targetFilepath = os.path.join(path_to_datafolder, "%s.txt" % token)
    with open(targetFilepath, "a") as myfile:
        myfile.write(compose_CPU(process_name, cpu_val))
    # Notify if it's a boundary observation (just started or just finished)
    return "posted"


def try_parse_object_as(inputObject, parseFunction):
    try:
        obs = parseFunction(inputObject)
        return obs
    except ValueError:
        abort(Response(
            "Error: Object is not parseable as a %s." % parseFunction.__name__,
            status=401))


def is_valid_uuid(uuid_to_test: str) -> bool:
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=4)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def validate_token(request: Flask.request_class):
    token = str(request.args.get("token"))
    if is_valid_uuid(token) and token in active_tokens(path_to_datafolder):
        return token
    else:
        abort(Response(
            "Error: The token `%s` is not active. Go make a new token." % token, status=401))



def gen_new_token():
    new_token = uuid.uuid4()
    targetAbspath = os.path.join(path_to_datafolder, "%s.txt" % new_token)
    user_file = open(targetAbspath, "a")
    now = time.time()
    L = ["APN:unknown\n", "init:%s\n" % now]
    user_file.writelines(L)
    user_file.write(compose_OBS(-1))
    user_file.write(compose_CPU("INIT", -1))
    user_file.close()
    return new_token


def compose_CPU(name, value):
    return "CPU,%s,%s,%s\n" % (time.time(), name, value)


@app.route('/newtoken/', methods=['POST'])
def newtoken():
    return jsonify({
        "token": f"%s" % gen_new_token(),
        "METHOD": "POST"
    })


@app.route('/start')
def start():
    myToken = gen_new_token()
    return "<h1>Token: %s</h1><br><img src=\"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=%s\"><br>" % (
        myToken, myToken)



import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://074264e9da2c4444ae74f9e632f3895a@o395868.ingest.sentry.io/5263630",
    integrations=[FlaskIntegration()]
)
@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, host="0.0.0.0", port=80, ssl_context='adhoc', debug=False)
