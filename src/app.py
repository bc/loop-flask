import logging
import logging
import os
import numpy as np
import requests
import sentry_sdk
from flask import Flask, request, jsonify, abort, Response, render_template, redirect
from sentry_sdk.integrations.flask import FlaskIntegration

from loop_helpers.authentication import validate_token, gen_new_token
from loop_helpers.datafunctions import get_last_observation_line, try_parse_object_as, compose_CPU, is_normalized, \
    compose_OBS, Observation, get_all_logged_lines
from loop_helpers.notifications import push_telegram_notification, Predicate, get_contactinfo, \
    predicate_is_triggered, parse_predicate, list_of_predicate_to_json, get_predicates, clear_all_predicates, \
    clear_contactinfo, DiscordID

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
#
#
# @app.route('/is_token_valid', methods=['GET'])
# def is_token_valid_endpoint():
#     token = validate_token(request, DATAFOLDERPATH)
#     return "token ok"


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


@app.route('/monotonic_obs_eta/', methods=['GET'])
def monotonic_obs_eta():
    token = validate_token(request, DATAFOLDERPATH)
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    res = run_lm_on_loglines_obs(target_filepath)
    try:
        return jsonify(res)
    except:
        return res


def monotonic_obs_eta_direct(token):
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    return run_lm_on_loglines_obs(target_filepath)


def run_lm_on_loglines_obs(target_filepath):
    bigL = get_all_logged_lines(target_filepath, "OBS")
    if len(bigL) < 3:
        return Response("too few datapoints to predict", 200)
    # note that y is the time and x is the value, because i'm interested in the y value where x == 1 (the intercept)
    y = np.asarray([float(x[1]) for x in bigL])
    x = np.asarray([float(x[2]) for x in bigL])
    indices_where_value_dropped = [i for i, val in enumerate(np.diff(x)) if val < 0.0]
    if len(indices_where_value_dropped) == 0:
        x_final = x
        y_final = y
    else:
        last_drop = indices_where_value_dropped[-1] + 1
        x_final = x[last_drop:]
        y_final = y[last_drop:]
    # need at least 2 datapoints that are different to linearly fit
    if len(np.unique(x_final)) < 3:
        return Response("too few datapoints to predict", 200)
    values_to_infer = np.linspace(0.0, 1.0, 21)
    lower, p_y, upper, z, r_squared = lm_with_ci(x=x_final, y=y_final, p_x=values_to_infer)
    payload = {"OBS": {"values": list(x_final), "unixtimes": list(y_final)},
               "predictions": {"values_to_infer": list(values_to_infer), "unixtime_predicted": list(p_y),
                               "unixtime_upperbound": upper, "unixtime_lowerbound": lower, "m": z[0], "b": z[1],
                               "r_squared": float(r_squared)}}
    return payload


def lm_with_ci(x, y, p_x):
    """
    derived from # https://tomholderness.wordpress.com/2013/01/10/confidence_intervals/
    and
    https://stackoverflow.com/questions/893657/how-do-i-calculate-r-squared-using-python-and-numpy
    :param x: ndarray of floats/ints
    :param y: ndarray of floats/ints, same len as x
    :param p_x: values to predict on x with confidence intervals at 95% CI
    :param r_squared: the coefficient of determination
    :return:
    """

    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)

    # fit values, and mean
    yhat = p(x)  # or [p(z) for z in x]
    ybar = np.sum(y) / len(y)  # or sum(y)/len(y)
    ssreg = np.sum((yhat - ybar) ** 2)  # or sum([ (yihat - ybar)**2 for yihat in yhat])
    sstot = np.sum((y - ybar) ** 2)  # or sum([ (yi - ybar)**2 for yi in y])
    r_squared_val = ssreg / sstot
    fit = p(x)
    # get the coordinates for the fit curve
    c_y = [np.min(fit), np.max(fit)]
    c_x = [np.min(x), np.max(x)]
    # predict y values of original data using the fit
    p_y = z[0] * x + z[1]
    # calculate the y-error (residuals)
    y_err = y - p_y
    # create series of new test x-values to predict for

    # now calculate confidence intervals for new test x-series
    mean_x = np.mean(x)  # mean of x
    n = len(x)  # number of samples in original fit
    t = 2.31  # appropriate t value (where n=9, two tailed 95%)
    s_err = np.sum(np.power(y_err, 2))  # sum of the squares of the residuals
    confs = t * np.sqrt((s_err / (n - 2)) * (1.0 / n + (np.power((p_x - mean_x), 2) /
                                                        ((np.sum(np.power(x, 2))) - n * (np.power(mean_x, 2))))))
    # now predict y based on test x-values
    p_y = z[0] * p_x + z[1]
    # get lower and upper confidence limits based on predicted y and confidence intervals
    confs_abs = abs(confs)
    # case where r==1
    lower = list(p_y - confs_abs)
    upper = list(p_y + confs_abs)
    return lower, p_y, upper, z, r_squared_val


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
    payload: str = request.args.get("contact_number")
    my_id: int = try_parse_object_as(payload, int)
    val = DiscordID(my_id)
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_contactinfo.txt" % token)
    # overwrite prior contact info
    with open(target_filepath, "w") as myfile:
        newline = DiscordID.to_json(val)
        myfile.writelines(newline)
    return Response(
        "added new contact info:" + newline,
        status=200)


def ping_discorder(discord_id, message):
    url = "https://ptb.discord.com/api/webhooks/769345876153729045/wWF2vgmF7a4c1TPiRgEjQTF1QPp8s9JogZYLMgM2e7fjKwPX25l00MeGY9P1i2wLwbmq"

    payload = "{\"username\": \"LoopBot\", \"content\": \"<@%s> %s\"}" % (discord_id.value, message)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text.encode('utf8')


@app.route('/ping_now/', methods=['POST', 'GET'])
def ping_now():
    token = validate_token(request, DATAFOLDERPATH)
    res = ping_discorder(get_contactinfo(token, DATAFOLDERPATH), "Ping_Now: All Done Now!")
    return ('posted')


def ping_discord_general(message):
    url = "https://ptb.discord.com/api/webhooks/769345876153729045/wWF2vgmF7a4c1TPiRgEjQTF1QPp8s9JogZYLMgM2e7fjKwPX25l00MeGY9P1i2wLwbmq"

    payload = "{\"username\": \"LoopBot\", \"content\": \"%s\"}" % (message)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return (response)


@app.route('/ping_general/', methods=['POST', 'GET'])
def ping_general():
    res = ping_discord_general("general_Message")
    return Response("posted; %s" % res, status=200)


@app.route('/set_discord_id/', methods=['POST', 'GET'])
def set_discord_id():
    token: str = validate_token(request, DATAFOLDERPATH)
    discord_id: str = request.args.get("id_no")
    target_filepath = os.path.join(DATAFOLDERPATH, "%s_discord_id.txt" % token)
    # overwrite prior apn info
    with open(target_filepath, "w") as myfile:
        myfile.writelines(discord_id)
    message = "Welcome to the team!"
    ping_discorder(discord_id, message)
    return Response(
        "added new apn info:" + discord_id,
        status=200)


@app.route('/clear_contactinfo/', methods=['POST', 'GET', 'DELETE'])
def clear_contactinfo_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    clear_contactinfo(token, DATAFOLDERPATH)
    return Response("cleared", status=200)


@app.route('/get_contactinfo/', methods=['GET'])
def get_contactinfo_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    contact_info = DiscordID.to_json(get_contactinfo(token, DATAFOLDERPATH))
    return contact_info


@app.route('/get_predicates/', methods=['GET'])
def get_predicates_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    predicates = get_predicates(token, DATAFOLDERPATH)
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


@app.route('/update_obs/', methods=['POST', 'GET'])
def update():
    token = validate_token(request, DATAFOLDERPATH)
    obs: float = try_parse_object_as(request.args.get("obs"), lambda x: float(x))

    # Make sure the float input is between 0 and 1
    if not is_normalized(obs):
        abort(Response(
            "Error: You can only push float numbers between 0 and 1 (e.g. 0.25 or 0.70). You entered (%s)." % obs,
            401))
    # make the observation
    target_filepath = os.path.join(DATAFOLDERPATH, "%s.txt" % token)
    with open(target_filepath, "a") as myfile:
        myfile.write(compose_OBS(obs))
    # notify if it's a boundary observation (just started or just finished)
    if predicate_is_triggered(token, Observation("obs", obs), DATAFOLDERPATH):
        return ping_user(obs, token, "obs")
    else:
        return "posted"


def ping_user(obs, token, message_type):
    app.logger.info("Sending %s push notification to user phone" % message_type)
    discord_id = get_contactinfo(token, DATAFOLDERPATH)
    if message_type == "obs":
        monotonic_lm = monotonic_obs_eta_direct(token)
        try:
            eta = monotonic_lm["predictions"]["unixtime_predicted"][11]
        except:
            eta = "NA"
    else:
        eta = "NA"
    res = ping_discorder(discord_id, "Loop says:%s,%s. Done @ %s" % (message_type, obs, eta))
    if res == b'':
        return ("posted to discord")
    else:
        raise Exception("discord had an issue with your discord ID: %s, %s" % (discord_id, res))


@app.route('/update_screenshot/', methods=['POST'])
def update_screenshot_endpoint():
    token = validate_token(request, DATAFOLDERPATH)
    f = request.files['file']
    f.save(os.path.join(DATAFOLDERPATH, "%s.png" % token))
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
        return ping_user(cpu_val, token, "cpu")
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
