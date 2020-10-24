import time
import json
import requests

test_text = input("Type the rest time (in seconds, e.g. 5) between loop progress updates")
rest_time = float(test_text)

import requests


import random
progress = 0
try:
    while True:
        progress += 0.01
        xx = progress % 1
        val = xx
        token = "ec2a7f38-8767-40ae-a1ca-c859b1fa450b" #generate one at loop.kaspect.com
        print(requests.request("POST", "http://0.0.0.0:5000/update_obs/?token=%s&obs=%s"%(token,val), headers={}, data = {}).text.encode('utf8'))
        print(val)
        #TODO post the update
        time.sleep(rest_time + random.uniform(-rest_time, rest_time))
except KeyboardInterrupt:
    #TODO maybe send the server a friendly note that we disconnected
    print("Ended Looping")
