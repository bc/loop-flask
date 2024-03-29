import webbrowser
from uuid import UUID

import pyperclip
import pdb
import rumps


global app, token, mytoken_menuitem, chosen_process, host_and_port, cooldown_timer, cooldown_timer_full_val
host_and_port = "http://0.0.0.0:8000"
mytoken_menuitem = "TOKEN_ITEM"
cooldown_timer_full_val = 2
cooldown_timer = cooldown_timer_full_val  # allows 2 cycles of MIA before it POSTs process has ended


@rumps.timer(10)
def refresh_update(sender):
    global cooldown_timer
    app.title = "SpookyLoop - CPU"

    outcome = post_process_progress((chosen_process['name'], chosen_process['pid']), host_and_port, token)
    if outcome != "process_not_found":
        cooldown_timer = cooldown_timer_full_val
        app.title = "🎃"
    else:
        print('Process has been missing. %s lives left' % cooldown_timer)
        if cooldown_timer == 0:
            app.title = "💔"
            print("Process died")
            ping_noise()
            rumps.notification("SpookyLoop", "Process died", "RIP process %s" % chosen_process["name"])
            rumps.quit_application()

        # if the process still has 'lives' left
        app.title = "".join(["❤️" for x in range(cooldown_timer)])
        cooldown_timer -= 1


# Generate a token here: 142.93.117.219:5000/
import os
# python3 -m nuitka --follow-imports client_cpu.py
# res = os.system("pip3 -q install psutil requests gputil")
# print(res)

import psutil
import requests
import time
import json
import sys


# Function must be called with root on mac due to an OS limitation
def processes_by_cpu():
    # this one initializes proc. ignore output
    [extract_process_info(proc) for proc in psutil.process_iter()]
    time.sleep(1)
    list_of_procs = [extract_process_info(proc) for proc in psutil.process_iter()]
    list_of_procs = filter(lambda x: x is not None, list_of_procs)
    # Sort list of dict by key i.e. cpu
    sorted_list = sorted(list_of_procs, key=lambda proc: proc['cpu'], reverse=True)
    return sorted_list


# returns None if there's an error.
def process_name_on_blacklist(input_process_name):
    # blacklist = ["routined", "remindd", "Spotify", "Activity Monitor",
    #              "Google Drive File Stream"]
    blacklist = []
    no_hits = sum([input_process_name.lower() in x.lower() for x in blacklist]) != 0
    return no_hits


# defined by blacklist
def extract_process_info(proc):
    try:
        pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
        # if its a known non-process, or it's the root process, ignore.
        if process_name_on_blacklist(pinfo["name"]) or pinfo["pid"] == 0:
            return None
        pinfo['vms_bytes'] = proc.memory_info().vms / (1024 * 1024)
        pinfo['rss_bytes'] = proc.memory_info().rss
        pinfo['cpu'] = proc.cpu_percent(interval=None) / 100.0  # convert to fraction
        pinfo['total_cpu'] = psutil.cpu_percent()
        # pinfo['total_gpu_info'] = GPUtil.cpu_percent()
        return pinfo
    except Exception as e:
        if type(e) in [psutil.AccessDenied ,psutil.ZombieProcess, psutil.NoSuchProcess]:
            return None
        print("Had exception when extracting process info: %s" % json.dumps(e))
        return None


def post_process_progress(target_process, host_socket, token):
    assert host_socket.endswith("/") is not True
    only_target_name = list(filter(lambda x: x["pid"] == target_process[1], processes_by_cpu()))
    url: str = "%s/update_cpu/?token=%s" % (host_socket, token)
    if len(only_target_name) == 0:
        print("%s process (ID %s) not found! It's likely done" % target_process)
        payload = json.dumps({"name": target_process[0], "pid": target_process[1], "cpu": 0.0000000})
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
        print(response.json)
        # TODO send null result
        return "process_not_found"
    payload: str = json.dumps(only_target_name[0])
    try:
        print('starting send')
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
        print("%s\n" % payload + str(response.text))
        return "submitted"
        # TODO warn if token is wrong
    except Exception as e:
        # soft err
        print("Error in sending update to server. ERR: %s" % e)


# # ISD * X is the amount of time the process can be dead for before notifying a finished process.
def main(host_and_port, loop_token, inter_sample_delay, cooldown_timer):
    target_process = ask_which_process_to_monitor()
    print('Tracking process: %s, ID: %s' % target_process)
    while True:
        outcome = post_process_progress(target_process, host_and_port, loop_token)
        if outcome == "process_not_found":
            print('Process has been missing. %s lives left' % cooldown_timer)
            if cooldown_timer == 0:
                print("Process died")
                try:
                    os.system('afplay /System/Library/Sounds/Glass.aiff')
                except:
                    print('Ding!')
                return
                # TODO post_process_at_neg1(target_process_name,host_and_port,loop_token)
            # if the process still has 'lives' left
            cooldown_timer -= 1
        time.sleep(inter_sample_delay)


def ask_which_process_to_monitor(n_to_list=20):
    procs = top_n_processes(n_to_list)
    test_number = int(input("Type the process # to target and press Enter:\n"))
    target_process = (procs[test_number]['name'], procs[test_number]['pid'])
    return target_process


def top_n_processes(n_to_list):
    procs = processes_by_cpu()
    printout = ["%s: %s" % (i, procs[i]['name']) for i in range(n_to_list)]
    return procs, printout


def validate_uuid4(uuid_string):
    """
    https://gist.github.com/ShawnMilo/7777304
    Validate that a UUID string is in
    fact a valid uuid4. Input can have the dashes or not

    Happily, the uuid module does the actual
    checking for us.

    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    """

    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False

    # If the uuid_string is a valid hex code,
    # but an invalid uuid4,
    # the UUID.__init__ will convert it to a
    # valid uuid4. This is bad for validation purposes.
    return val.hex == uuid_string.replace("-", "")


def ask_for_token():
    clipboard_element = pyperclip.paste()
    # has token
    newwindow = rumps.Window(message='Right click to paste your token below', default_text=str(clipboard_element),
                             title='SpookyLoop', ok="Submit Token", cancel="Cancel", dimensions=(320, 160))
    outcome = newwindow.run()
    # test whether the text input is actually a valid v4 UUID
    try:
        the_token = str(UUID(outcome.text, version=4))
    except:
        rumps.alert(title="SpookyLoop Error", message='not a UUID')
        sys.exit(0)

    # if they get to this point then it's a valid UUID.
    # now the question is whether it's a registered token on the server side.

    url = "%s/is_token_valid/?token=%s" % (host_and_port, the_token)
    response = requests.request("GET", url, headers={}, data={})
    result = response.text.encode('utf8')
    if result == b'token ok':
        # rumps.alert(title="SpookyLoop Response", message="response from server on token %s: %s" % (the_token, result))
        return the_token
    else:
        rumps.alert(title="SpookyLoop Error",
                    message="uuid is fine but token uuid is not registered on the server. Err: %s" % result)
        sys.exit(0)


@rumps.clicked(mytoken_menuitem)
def mytoken_menuitem_function(_):
    webbrowser.open(f'{host_and_port}/webclient?token={token}', new=2)


@rumps.clicked('Quit')
def clean_up_before_quit(_):
    print('TODO notify server of disconnect')
    rumps.quit_application()


def get_process_from_user():
    procs, printout = top_n_processes(20)
    question_window = rumps.Window(title="SpookyLoop",
                                   message="Which process do you want to monitor?\n---------\n %s" % "\n".join(
                                       printout), default_text="0", dimensions=(100, 20))
    proc_choice = question_window.run()
    try:
        index = int(proc_choice.text)
    except:
        rumps.alert(title="SpookyLoop Error",
                    message="You typed in %s, but that wasn't a valid number" % proc_choice.text)
        sys.exit(0)
    if 0 > index > len(procs) - 1:
        rumps.alert(title="SpookyLoop Error",
                    message="You typed in %s, but the number needs to be between 0 and %s!" % (
                        proc_choice.text, len(procs) - 1))
    return procs[index]


def ping_noise(sound_filepath="/System/Library/Sounds/Glass.aiff"):
    try:
        os.system('afplay %s'%sound_filepath)
    except:
        print("Could not play ping noise")


if __name__ == "__main__":
    ping_noise()
    print("starting pycode at %s" % time.time())
    app = rumps.App('SpookyLoop', menu=[mytoken_menuitem, "🎃 means running", "💔 means your program quit", 'Quit'],
                    quit_button=None)

    token_menuitem_val = app.menu[mytoken_menuitem]
    # if it's passed in via:  then the 0th argument is the app path,
    # and 1st argument is the token `loopit://26b78511-8690-4d07-b852-464ce10372b2`
    input_arguments = "\n".join(sys.argv)
    # rumps.alert(title="SL Inputs:", message=input_arguments)
    if len(sys.argv) > 1:
        token = str(sys.argv[1]).replace("loopit://", "").strip().lower()
        if validate_uuid4(token):
            # rumps.alert(title="Extracted token is valid", message=token)
            pass
        else:
            # the passed token is not a uuid
            # rumps.alert(title="Extracted token looked weird", message="%s, len: %s" % (token, len(token)))
            # replace token with manual input token
            token = ask_for_token()

    else:
        # rumps.alert(title="SpookyLoop", message="Get your token ready to paste")
        token = ask_for_token()
    try:
        chosen_process = get_process_from_user()
        token_menuitem_val.title = "Token: %s; %s; %s" % (token, chosen_process['name'], chosen_process['pid'])
    except:
        rumps.alert(title=None, message='some err in getting process')
        sys.exit(0)

    if token is not None:
        # TODO check if the token is valid on the server by sending a sample CPU val or ping
        rumps.alert(title="SpookyLoop", message="🎃: I'm up in the menubar!")
        webbrowser.open(f'{host_and_port}/webclient?token={token}', new=2, autoraise=True)
        app.run()
    else:
        rumps.alert(title=None, message='Bad token, contact @bcal on Discord if this happens again')
        print('token was None and whole app crashed')
        sys.exit(0)
