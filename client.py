import psutil
import time
import json
import requests


# Function must be called with root on mac due to an OS limitation
def getListOfProcessSortedByMemory():
    # this one initializes proc. ignore output
    [extract_process_info(proc) for proc in psutil.process_iter()]
    time.sleep(1)
    listOfProcObjects = [extract_process_info(proc) for proc in psutil.process_iter()]
    listOfProcObjects = filter(lambda x: x is not None, listOfProcObjects)
    # Sort list of dict by key i.e. cpu
    sortedL = sorted(listOfProcObjects, key=lambda procObj: procObj['cpu'], reverse=True)
    return sortedL


# returns None if there's an error.
def extract_process_info(proc):
    try:
        pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
        pinfo['vms_bytes'] = proc.memory_info().vms / (1024 * 1024)
        pinfo['rss_bytes'] = proc.memory_info().rss
        pinfo['cpu'] = proc.cpu_percent(interval=None)
        return pinfo
    except:
        return None


def post_top_n_processes(host_socket, token, N: int):
    assert host_socket.endswith("/") is not True
    res = getListOfProcessSortedByMemory()[0:N]
    payload: str = json.dumps(res)

    url: str = "%s/process_update/?token=%s" % (host_socket, token)
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text.encode('utf8'))
        # todo warn if token is wrong
    except Exception as e:
        print("Couldn't send this observation to the server. Confirm you're connected to the internet! ERR: %s" % e)


post_top_n_processes("https://127.0.0.1:5000", "ffdc1f83-66b0-4386-a1d3-d8b924274b28", 5)
