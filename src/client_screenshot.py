import os
from time import sleep
from image_helpers import *
# open colour image
from PIL import ImageGrab

row_pixel_target = 591
count = 1
from scipy.cluster.vq import kmeans
while True:
    #-R20,20,640,380
    target_filepath = "/Users/briancohn/Desktop/output/s_%s.png"%count
    x = os.popen("screencapture -x %s"%target_filepath)
    xx = pilToNumpy(Image.open(target_filepath).convert("L")).astype(np.float32)
    target_row = xx[row_pixel_target]
    clusters = kmeans(target_row, 2)
    np.diff(target_row)

    sleep(1)
    count +=1

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
