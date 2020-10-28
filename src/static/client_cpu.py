# Generate a token here: 142.93.117.219:5000/
import os
# python3 -m nuitka --follow-imports client_cpu.py
print("Installing")
res = os.system("pip3 -q install psutil requests gputil")
print(res)
print('Installation Complete')

import psutil
import requests
import GPUtil
import time
import json
import multiprocessing
import sys

input("Once your process is running, press Enter\n")


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
        if process_name_on_blacklist(pinfo["name"]) or pinfo["pid"]==0:
            return None
        pinfo['vms_bytes'] = proc.memory_info().vms / (1024 * 1024)
        pinfo['rss_bytes'] = proc.memory_info().rss
        pinfo['cpu'] = proc.cpu_percent(interval=None) / 100.0  # convert to fraction
        pinfo['total_cpu'] = psutil.cpu_percent()
        pinfo['total_gpu_info'] = GPUtil.cpu_percent()
        return pinfo
    except Exception as e:
        if type(e) == psutil.AccessDenied or type(e) == psutil.ZombieProcess:
            return None
        print("Had exception when extracting process info: " % json.dumps(e))
        return None

def post_process_progress(target_process, host_socket, token):
    assert host_socket.endswith("/") is not True
    only_target_name = list(filter(lambda x: x["pid"] == target_process[1], processes_by_cpu()))
    url: str = "%s/update_cpu/?token=%s" % (host_socket, token)
    if len(only_target_name) == 0:
        print("%s process (ID %s) not found! It's likely done" % target_process)
        payload = json.dumps({"name": target_process[0],"pid":target_process[1], "cpu": 0.0000000})
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
        print(response.json)
        # TODO send null result
        return "process_not_found"
    payload: str = json.dumps(only_target_name[0])
    try:
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
        print("%s\n" % payload + str(response.text))
        return "submitted"
        # TODO warn if token is wrong
    except Exception as e:
        # soft err
        print("Error in sending update to server. ERR: %s" % e)


# # ISD * X is the amount of time the process can be dead for before notifying a finished process.
def main(host_and_port, loop_token, inter_sample_delay, cooldown_timer):
    procs = processes_by_cpu()
    for i in range(20):
        print("%s: %s" % (i, procs[i]['name']))
    test_text = input("Type the process # to target and press Enter:\n")
    test_number = int(test_text)
    target_process = (procs[test_number]['name'], procs[test_number]['pid'])
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
    # except KeyboardInterrupt:
    #     print("Ended Tracking")
    #     os.system('afplay /System/Library/Sounds/Glass.aiff')
    #     # TODO print("sending end tracking POST note to server")
    #     return


if __name__ == "__main__":
    print("View your monitor here: %s/webclient?token=%s" % (sys.argv[1],sys.argv[2]))
    cores = multiprocessing.cpu_count()
    print('%s cores detected' % cores)
    print('BC: CPU Tracker Version: 0.0.2')
    input("Once your process is running, press Enter\n")
    main(host_and_port=sys.argv[1], loop_token=sys.argv[2], inter_sample_delay=10, cooldown_timer=0)
