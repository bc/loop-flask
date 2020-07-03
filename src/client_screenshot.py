import os
import requests
from time import sleep

import requests

from image_helpers import *
# open colour image
from PIL import ImageGrab

row_pixel_target = 591
count = 1
from scipy.cluster.vq import kmeans
sleep(3)
RR = os.popen("screencapture /tmp/test.png")
sleep(1)
Image.open("/tmp/test.png").show()

x = int(input("Enter X: "))
y = int(input("Enter Y: "))
coord = (x,y)
sleep(2)
RR = os.popen("screencapture /tmp/test.png")
tempVal = img_and_end_px_to_progress(coord,Image.open("/tmp/test.png"), debug=True)


def post_image(target_filepath):
    url = "http://127.0.0.1:5000/update_screenshot/?token=1df19522-b361-467b-b1c4-0a291b2d55ea"
    payload = {}
    files = [
        ('file',
         open(target_filepath, 'rb'))
    ]
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    print(response.text.encode('utf8'))
    return requests


post_image("/tmp/test.png")


input("It thinks the current percentage is %s Press Enter if the image line looks good, or Control+C to exit"%tempVal)

while True:
    #-R20,20,640,380
    target_filepath = "/Users/briancohn/Desktop/output/s_%s.png"%count
    x = os.popen("screencapture -x %s"%target_filepath)
    val = img_and_end_px_to_progress(
        coord,
        Image.open(target_filepath),
        debug=True
    )
    print(val)

    url = "http://0.0.0.0:5000/update_obs/?token=3311f6d4-b4ba-498a-a3ad-b6989fcbb873&obs=%s" % val

    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text.encode('utf8'))

    sleep(2)
    count += 1


    #
    # res = os.popen(
    #     "sleep 2 && screencapture ~/tmp/screen%s.png && tesseract /tmp/screen.png /tmp/out && cat /tmp/out.txt").read()
    # search_result = re.search('Syncing(.*)files', res)
    # # pdb.set_trace()
    # obs = []
    # for i in range(search_result.lastindex + 1):
    #     try:
    #         obs += [int(search_result.group(i).rstrip().lstrip())]
    #     except Exception as e:
    #         print(e)
    # print(obs)
