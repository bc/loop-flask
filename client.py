import psutil
import time
import json
import requests


# Function must be called with root on mac due to an OS limitation
def processes_by_cpu():
    # this one initializes proc. ignore output
    [extract_process_info(proc) for proc in psutil.process_iter()]
    time.sleep(1)
    listOfProcObjects = [extract_process_info(proc) for proc in psutil.process_iter()]
    listOfProcObjects = filter(lambda x: x is not None, listOfProcObjects)
    # Sort list of dict by key i.e. cpu
    sortedL = sorted(listOfProcObjects, key=lambda procObj: procObj['cpu'], reverse=True)
    return sortedL


# returns None if there's an error.
def process_name_on_blacklist(input_process_name):
    blacklist = ["Google Chrome", "routined", "remindd", "Spotify", "firefox", "Activity Monitor",
                 "Google Drive File Stream"]
    blacklist = []
    no_hits = sum([input_process_name.lower() in x.lower() for x in blacklist]) != 0
    return no_hits


# defined by blacklist
def extract_process_info(proc):
    try:
        pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
        if process_name_on_blacklist(pinfo["name"]):
            return None
        pinfo['vms_bytes'] = proc.memory_info().vms / (1024 * 1024)
        pinfo['rss_bytes'] = proc.memory_info().rss
        pinfo['cpu'] = proc.cpu_percent(interval=None)
        return pinfo
    except:
        return None


def post_process_progress(target_process_name, host_socket, token):
    assert host_socket.endswith("/") is not True
    res = processes_by_cpu()  # [0:N]
    only_target_name = list(filter(lambda x: x["name"] == target_process_name, res))
    if len(only_target_name) == 0:
        only_target_name = ["process_not_found"]
        print("%s process not found! Maybe it's done" % target_process_name)
        return "process_not_found"
    payload: str = json.dumps(only_target_name[0])

    url: str = "%s/process_update/?token=%s" % (host_socket, token)
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text.encode('utf8'))
        return "submitted"
        # TODO warn if token is wrong
    except Exception as e:
        # soft err
        print("Couldn't send this observation to the server. Confirm you're connected to the internet! ERR: %s" % e)


res = processes_by_cpu()

print('Note: Your process needs to be running before you run this')
for i in range(20):
    print("%s: %s" % (i, res[i]['name']))
test_text = input("Type the process # to target and press enter:")
test_number = int(test_text)
target_process_name = res[test_number]['name']
print('Tracking process: %s' % target_process_name)
process_missing_counter = 0


def request_process_over_ping(target_process_name, hostport, token):
    url = "%s/process_over_request_ping/?token=%s&process_name=%s" % (hostport, token, target_process_name)
    response = requests.request("GET", url, headers={}, data={})
    return response.text.encode('utf8')


inter_sample_delay = 0  # seconds
# number of seconds a process has to be consecutively dead for us to end.
process_cooldown_seconds = 3

loop_token = "3311f6d4-b4ba-498a-a3ad-b6989fcbb873"
host_and_port = "http://142.93.117.219:5000"
try:
    while True:
        outcome = post_process_progress(target_process_name, host_and_port, loop_token)
        if outcome != "process_not_found":
            # reset if process is found
            last_time_seen = time.time()
        time_since_last_seen = time.time() - last_time_seen
        if time_since_last_seen > process_cooldown_seconds:
            try:
                ping_res = request_process_over_ping(target_process_name, host_and_port, loop_token)
                print(ping_res)
                break
            except Exception as e:
                print("Completed process, but ping didn't work. Error: %s" % e)
                break
        time.sleep(inter_sample_delay)
except KeyboardInterrupt:
    print("Ended Tracking")
#     todo maybe send the server a friendly note that we disconnected
