import logging
import os
import pdb
from dataclasses import dataclass
from enum import Enum

from dataclasses_json import dataclass_json
import sentry_sdk
from flask import Flask, request, jsonify, abort, Response, render_template
from sentry_sdk.integrations.flask import FlaskIntegration

from loop_helpers.authentication import validate_token, gen_new_token
from loop_helpers.datafunctions import get_last_observation_line, try_parse_object_as, compose_CPU, is_normalized, \
    compose_OBS
from loop_helpers.notifications import push_telegram_notification

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


@app.route('/webclient/')
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
            "percent": float(cpu_obs)
        }
    }
    return jsonify(payload)


def parse_predicate(token, ss):
    input_string = ss.replace("=", "").replace(" ", "")

    if ">" in input_string:
        eqn_sides = input_string.split(">")
        eq_type = ">"
    elif "<" in input_string:
        eqn_sides = input_string.split("<")
        eq_type = "<"
    else:
        abort(Response(
            "Error: input should have a > or a < in the statement yours had neither: (%s)." % input_string,
            status=401))
    if len(eqn_sides) != 2:
        abort(Response(
            "Error: input didn't have an element on both sides of the input > or < (%s)." % input_string,
            status=401))
    if eq_type not in accepted_comparator_operators:
        raise Exception("input comparator operator is not valid. input was: %s, should be one of these:"%(eq_type, ",".join(accepted_comparator_operators)))
    return Predicate(token, eqn_sides[0], eq_type, eqn_sides[1])

def trigger_on_true_evaluation(trigger_on_true, x0,x1):
    if trigger_on_true == ">":
        return x0 > x1
    elif trigger_on_true == ">=":
        return x0 > x1
    elif trigger_on_true == "<":
        return x0 < x1
    elif trigger_on_true == "<=":
        return x0 < x1
    elif trigger_on_true == "==":
        return x0 == x1
    elif trigger_on_true == "!=":
        return x0 != x1
    else:
        raise Exception("input trigger was invalid. Input was %s"%trigger_on_true)



accepted_comparator_operators =[
">=",
"<=",
"==",
"!=",
">",
"<"]

@dataclass_json
@dataclass
class Observation:
    feature: str
    value: float

@dataclass_json
@dataclass
class Predicate:
    token: str
    feature: str
    trigger_on_true: str
    value: float
    def evaluate(self, o: Observation):
        if o.feature != self.feature:
            raise Exception("wrong observation type %s given to predicate that was expecting a %s" % (o.feature, self.feature))
        else:
            return trigger_on_true_evaluation(self.trigger_on_true, o.value, self.value)

def list_of_predicate_to_json(L):
    return Predicate.schema().dumps(L, many=True)

def json_to_list_of_predicates(firstline):
    return Predicate.schema().loads(firstline, many=True)


@dataclass_json
@dataclass
class ContactInfo:
    token: str
    type: str
    # phone address is a phone number
    value: str

@app.route('/set_predicates/', methods=['POST', 'GET'])
def set_predicates():
    token:str = validate_token(request, DATAFOLDERPATH)
    preds: [Predicate] = [try_parse_object_as(YY, lambda x: parse_predicate(token, x)) for YY in request.args.get("predicate").split(";")]

    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    #overwrite prior predicate
    with open(target_filepath, "w") as myfile:
        predicate_line_out = list_of_predicate_to_json(preds)  # '[predicatejson]'
        myfile.writelines(predicate_line_out)
    return Response(
        "added new predicates:" + predicate_line_out,
        status=200)


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
    clear_all_predicates(token)
    return Response("cleared",status=200)





def get_predicates(token):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    if not os.path.isfile(target_filepath):
        app.logger.info("No predicates found for token: %s. Returning empty list of predicates"%token)
        return []
    with open(target_filepath, 'r') as f:
        firstline = f.readline()
        preds = json_to_list_of_predicates(firstline)  # [Person(name='lidatong')]
    return preds

def predicate_is_triggered(token, o: Observation):
    predicates = get_predicates(token)
    if len(predicates) == 0:
        #if there are no predicates, they can't be triggered
        return False
    predicate_matches = [p.evaluate(o) for p in predicates if p.feature == o.feature]
    print(predicate_matches)
    result = any(predicate_matches)
    if result==True:
        clear_all_predicates(token)
    return result

def clear_all_predicates(token):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_predicates.txt" % token)
    if os.path.isfile(target_filepath):
        os.remove(target_filepath)
    app.logger.info("predicates for token %s"%token)



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


@app.route('/update_obs/', methods=['POST'])
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
    if predicate_is_triggered(token, Observation("obs",obs)):
        app.logger.info("Sending push notification to BC's phone #TODO twilio")
        telegram_outcome = push_telegram_notification(token, "@ %s percent" % str(obs * 100))
        if telegram_outcome:
            return "posted; notified"
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
    if predicate_is_triggered(token, Observation("cpu",cpu_val)):
        app.logger.info("CPU Predicate triggered")
        telegram_outcome = push_telegram_notification(token, "CPU@ %s percent" % str(cpu_val * 100))
        if telegram_outcome:
            return "posted; notified"
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


@app.route('/start')
def start():
    my_token = gen_new_token(DATAFOLDERPATH)
    return "<h1>Token: %s</h1><br><img src=\"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=%s\"><br>" % (
        my_token, my_token)


@app.route('/debug-sentry')
def trigger_error():
    division_by_zero = 1 / 0
    return (division_by_zero)


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
