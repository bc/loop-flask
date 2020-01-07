#bash script for many
# for i in {1..1000}; do python3 simulate_usercode.py &; done


from time import sleep
import requests
import pdb

url = "http://169.254.49.227/newtoken/"
payload = {}
headers= {}
token_response = requests.request("POST", url, headers=headers, data = payload)
token_text = token_response.json()['token']
# pdb.set_trace()
# token_text = response.text.encode('utf8')

print(token_text)

url = "http://169.254.49.227/update/?token=%s&obs=OBSERVATION"%token_text

payload = {}
headers = {

}
i = 0
while True:
	i += 1.03
	try:
		response = requests.request("POST", url.replace("OBSERVATION",str(i),1), headers=headers, data = payload)
	except Exception as e:
		print(e)
	sleep(0.5)
