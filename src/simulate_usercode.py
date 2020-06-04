#bash script for many
# for i in {1..1000}; do python3 simulate_usercode.py &; done


from time import sleep
import requests
import pdb

ip = "loopservice.briancohn.com"
url = "http://%s/start/"%ip
payload = {}
headers= {}
token_response = requests.request("POST", url, headers=headers, data = payload)
token_text = token_response.json()['token']
# pdb.set_trace()
# token_text = response.text.encode('utf8')

print(token_text)

url = "http://%s/update/?token=%s&obs=OBSERVATION"%(ip,token_text)
payload = {}
headers = {}
i = 0.0
N = 900
while True:
	try:
		fraction = i/N
		response = requests.request("POST", url.replace("OBSERVATION",str(fraction),1), headers=headers, data = payload)
	except Exception as e:
		print(e)
	i += 1
	sleep(0.1)
	if i == N:
		i = 0
