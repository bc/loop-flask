import os, logging
from flask import Flask, request, jsonify, abort, Response, render_template
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from loop_helpers.authentication import validate_token, gen_new_token
from loop_helpers.datafunctions import get_last_observation_line, try_parse_object_as, compose_CPU, is_normalized, \
    compose_OBS
from loop_helpers.notifications import push_telegram_notification

app = Flask(__name__)
path_to_datafolder = "../data"

app.logger.debug('this is a DEBUG message')
app.logger.info('this is an INFO message')
app.logger.warning('this is a WARNING message')
app.logger.error('this is an ERROR message')
app.logger.critical('this is a CRITICAL message')

sentry_sdk.init(
    dsn="https://074264e9da2c4444ae74f9e632f3895a@o395868.ingest.sentry.io/5263630",
    integrations=[FlaskIntegration()]
)


@app.route('/')
def website_root():
    return render_template("index.html")


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
        app.logger.info("Sending push notification to bc's phone")
        telegram_outcome = push_telegram_notification(token, "@ %s percent" % str(obs * 100))
        if telegram_outcome:
            return "posted; notified"
        else:
            return "posted; notification failed"
    else:
        return "posted"


@app.route('/process_update/', methods=['POST'])
def process_update():
    # Get the input token
    token = validate_token(request)
    # TODO create assertions for what the json looks like
    top_process = request.json
    if top_process == "process_not_found":
        app.logger.info("it's done! ping person")
        return ("completion acknowledged")
    cpu_val: float = try_parse_object_as(top_process['cpu'], float)  # 0 to e.g. 1600%
    process_name: str = try_parse_object_as(top_process['name'], str)
    # Make the observation
    targetFilepath = os.path.join(path_to_datafolder, "%s.txt" % token)
    with open(targetFilepath, "a") as myfile:
        myfile.write(compose_CPU(process_name, cpu_val))
    # Notify if it's a boundary observation (just started or just finished)
    return "posted"


@app.route('/newtoken/', methods=['POST'])
def newtoken():
    return jsonify({
        "token": f"%s" % gen_new_token(path_to_datafolder),
        "METHOD": "POST"
    })


@app.route('/start')
def start():
    myToken = gen_new_token(path_to_datafolder)
    return "<h1>Token: %s</h1><br><img src=\"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=%s\"><br>" % (
        myToken, myToken)


@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0


# when you run the app directly via python3 app.py or flask run
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.logger.info('Starting Via Flask invocation')
    app.run(threaded=True, host="0.0.0.0", port=5000, ssl_context='adhoc', debug=False)

# this is useful so the logs get passed along to gunicorn when it's running, but don't when you run flask directly.
if __name__ != '__main__':
    app.logger.info('Starting Via gunicorn invocation')
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
