import requests
import sys
import random
import time

key = sys.argv[1]

URL = 'http://10.2.64.115/update/?key=%s&field1=%s'

while True:
    temp = random.uniform(22,27)
    temp = "%.1f" % temp
    print 'update temperature value: %s' % temp
    requests.get(URL % (key,temp))
    time.sleep(10)
