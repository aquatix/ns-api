import argparse
import sys
import json
from pushbullet import PushBullet
from requests.exceptions import HTTPError
import settings

def list_items(self):
    #
    pass


p = PushBullet(settings.pushbullet_key)

latest_modified = 0
total = 0
done = False
delays = []
disruptions = []

print "Cleanup, lets get the list first"

while not done:
    hist = p.getPushHistory(modified_after=latest_modified)
    print len(hist)
    if len(hist) > 0:
        print hist[0]
        sys.stdout.flush() # force flush of the print statements so user sees progress
    total = total + len(hist)
    for item in hist:
        if 'title' in item:
            if item['title'] == 'NS Vertraging':
                delays.append(item)
            elif item['title'] == 'NS Storing':
                disruptions.append(item)
    if len(hist) > 0 and 'modified' in hist[0]:
        latest_modified = hist[0]['modified']
    if len(hist) < 500:
        done = True

print('Total pushes found: {0}'.format(total))
print('Total delays to delete: {0}'.format(len(delays)))
print('Total disruptions to delete: {0}'.format(len(disruptions)))

print ('== Delays, deleting ======')
for delay in delays:
    print('{0} {1}'.format(delay['iden'], delay['title']))
    sys.stdout.flush() # force flush of the print statements so user sees progress
    p.deletePush(delay['iden'])
print ('== Disruptions, deleting ======')
for disruption in disruptions:
    print('{0} {1}'.format(disruption['iden'], disruption['title']))
    sys.stdout.flush()
    p.deletePush(disruption['iden'])
