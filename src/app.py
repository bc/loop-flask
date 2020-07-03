import json
import logging
import os

import sentry_sdk
from flask import Flask, request, jsonify, abort, Response, render_template, redirect
from sentry_sdk.integrations.flask import FlaskIntegration

from loop_helpers.authentication import validate_token, gen_new_token
from loop_helpers.datafunctions import get_last_observation_line, try_parse_object_as, compose_CPU, is_normalized, \
    compose_OBS, Observation
from loop_helpers.notifications import push_telegram_notification, text_update, Predicate, CellPhone, get_contactinfo, \
    predicate_is_triggered, parse_predicate, list_of_predicate_to_json, get_predicates, clear_all_predicates, \
    clear_contactinfo, verify_cellnumber

app = Flask(__name__)
DATAFOLDERPATH = "../data"

# app.logger.debug('this is a DEBUG message')
# app.logger.info('this is an INFO message')
# app.logger.warning('this is a WARNING message')
# app.logger.error('this is an ERROR message')
# app.logger.critical('this is a CRITICAL message')

sentry_sdk.init(
    dsn="https://074264e9da2c4444ae74f9e632f3895a@o395868.ingest.sentry.io/5263630",
    integrations=[FlaskIntegration()]
)


@app.route('/')
def website_root():
    return render_template("index.html")


@app.route('/webclient')
def webclient():
    return render_template("webclient.html")


@app.route('/listen/', methods=['GET'])
def listen():
    token = validate_token(request, DATAFOLDERPATH)
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)

    obs_type, time, obs = get_last_observation_line(target_filepath, "OBS")
    cpu_type, cpu_time, cpu_name, cpu_obs = get_last_observation_line(target_filepath, "CPU")

    payload = {"OBS": {
        "unixtime": float(time),
        "value": float(obs)
    },
        "CPU": {
            "unixtime": float(cpu_time),
            "name": str(cpu_name),
            "value": float(cpu_obs)
        }
    }
    return jsonify(payload)


@app.route('/set_predicates/', methods=['POST', 'GET'])
def set_predicates():
    token: str = validate_token(request, DATAFOLDERPATH)
    input_predicates = request.args.get("predicate")
    preds: [Predicate] = [try_parse_object_as(YY, lambda x: parse_predicate(token, x)) for YY in
                          input_predicates.split(";")]

    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    # overwrite prior predicate
    with open(target_filepath, "w") as myfile:
        predicate_line_out = list_of_predicate_to_json(preds)  # '[predicatejson]'
        myfile.writelines(predicate_line_out)
    return Response(
        "added new predicates:" + predicate_line_out,
        status=200)


@app.route('/set_contactinfo/', methods=['POST', 'GET'])
def set_contactinfo():
    token: str = validate_token(request, DATAFOLDERPATH)
    payload: str = request.args.get("cell")
    cell_int: int = try_parse_object_as(payload, int)
    better_cell_number = verify_cellnumber(cell_int)
    cell_no = CellPhone(better_cell_number)
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_contactinfo.txt" % token)
    # overwrite prior contact info
    with open(target_filepath, "w") as myfile:
        newline = CellPhone.to_json(cell_no)
        myfile.writelines(newline)
    return Response(
        "added new contact info:" + newline,
        status=200)


@app.route('/clear_contactinfo/', methods=['POST', 'GET', 'DELETE'])
def clear_contactinfo_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    clear_contactinfo(token, DATAFOLDERPATH)
    return Response("cleared", status=200)


@app.route('/get_contactinfo/', methods=['GET'])
def get_contactinfo_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    return CellPhone.to_json(get_contactinfo(token, DATAFOLDERPATH))


@app.route('/get_predicates/', methods=['GET'])
def get_predicates_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    predicates = get_predicates(token)
    return Response(
        list_of_predicate_to_json(predicates),
        status=200)


@app.route('/clear_predicates/', methods=['GET'])
def clear_predicates_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    clear_all_predicates(token, DATAFOLDERPATH)
    return Response("cleared", status=200)


@app.route('/process_over_request_ping/', methods=['GET'])
def process_over_request_ping():
    token = validate_token(request, DATAFOLDERPATH)
    process_name: str = try_parse_object_as(request.args.get("process_name"), str)
    # log this completion to the user's data
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    with open(target_filepath, "a") as myfile:
        # TODO should do some cleanup of the existing logs as we
        # know the user's completed tracking that process
        myfile.write(compose_CPU(process_name, -1))
    telegram_outcome = push_telegram_notification(token, "Process %s done" % process_name)
    if telegram_outcome:
        return "notified_of_process_end"
    else:
        return "notification_failed"


@app.route('/update_obs/', methods=['POST','GET'])
def update():
    token = validate_token(request, DATAFOLDERPATH)
    obs: float = try_parse_object_as(request.args.get("obs"), lambda x: float(x))

    # Make sure the float input is between 0 and 1
    if not is_normalized(obs):
        abort(Response(
            "Error: you can only push float numbers between 0 and 1 (e.g. 0.25 or 0.70). You entered (%s)." % obs,
            status=401))
    # make the observation
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    with open(target_filepath, "a") as myfile:
        myfile.write(compose_OBS(obs))
    # notify if it's a boundary observation (just started or just finished)
    if predicate_is_triggered(token, Observation("obs", obs), DATAFOLDERPATH):
        app.logger.info("Sending push notification to BC's phone #TODO twilio")
        twilio_resp = text_update(token, "Loop Says\nobs:%s" % obs, DATAFOLDERPATH)
        # telegram_outcome = push_telegram_notification(token, "@ %s percent" % str(obs * 100))
        if twilio_resp:
            return "posted; notified @ %s" % twilio_resp
        else:
            return "posted; notification failed"
    else:
        return "posted"


@app.route('/update_cpu/', methods=['POST'])
def process_update():
    # Get the input token
    token = validate_token(request, DATAFOLDERPATH)
    # TODO create assertions for what the json looks like
    top_process = request.json
    if top_process == "process_not_found":
        app.logger.info("it's done! ping person")
        return "completion acknowledged"
    cpu_val: float = try_parse_object_as(top_process['cpu'], float)  # 0 to e.g. 1600%
    process_name: str = try_parse_object_as(top_process['name'], str)
    # Make the observation
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    with open(target_filepath, "a") as myfile:
        myfile.write(compose_CPU(process_name, cpu_val))
    # Notify if it's a boundary observation (just started or just finished)
    if predicate_is_triggered(token, Observation("cpu", cpu_val), DATAFOLDERPATH):
        app.logger.info("CPU Predicate triggered")
        telegram_outcome = push_telegram_notification(token, "CPU@ %s " % str(cpu_val))
        if telegram_outcome:
            return "posted; notified: %s" % json.dumps(telegram_outcome)
        else:
            return "posted; notification failed"
    else:
        return "posted"


@app.route('/newtoken/', methods=['POST', 'GET'])
def newtoken():
    return jsonify({
        "token": f"%s" % gen_new_token(DATAFOLDERPATH),
        "METHOD": "POST"
    })


def newcssheader() -> str:
    return """
    <link rel="stylesheet" href="https://fonts.xz.style/serve/inter.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@exampledev/new.css@1.1.2/new.min.css">
"""


def link_to_webclient(host_url, token):
    href_target = str(host_url) + "webclient/?token=%s" % str(token)
    return href_target


def doublequoteit(s: str) -> str:
    return "\"%s\"" % s


@app.route('/start')
def start():
    my_token = gen_new_token(DATAFOLDERPATH)
    return redirect(f"{request.host_url}webclient?token={my_token}", code=302)


@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero


# when you run the app directly via python3 app.py or flask run
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.logger.info('Starting Via Flask invocation')
    app.run(threaded=True, host="0.0.0.0", port=5000, ssl_context='adhoc', debug=True)

# this is useful so the logs get passed along to gunicorn when it's running, but don't when you run flask directly.
if __name__ != '__main__':
    app.logger.info('Starting Via gunicorn invocation')
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
