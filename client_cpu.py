import psutil
import time
import json
import requests

loop_token = "533fe6db-e3e6-4075-9fac-e32667684b37"
host_and_port = "http://142.93.117.219:5000"
inter_sample_delay = 30 #

# ISD * X is the amount of time the process can be dead for before notifying a finished process.
cooldown_timer = 3 #this is X


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
        pinfo['cpu'] = proc.cpu_percent(interval=None)/100.0 #convert to fraction
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
        #TODO send null result
        return "process_not_found"
    payload: str = json.dumps(only_target_name[0])
    url: str = "%s/update_cpu/?token=%s" % (host_socket, token)
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




try:
    while True:
        outcome = post_process_progress(target_process_name, host_and_port, loop_token)
        if outcome == "process_not_found":
            cooldown_timer -= 1
            if cooldown_timer == 0:
                print("process definitely died. POSTING completion message")
                break
                #TODO post_process_at_neg1(target_process_name,host_and_port,loop_token)
        time.sleep(inter_sample_delay)
except KeyboardInterrupt:
    print("Ended Tracking")
    # TODO print("sending end tracking POST note to server")
