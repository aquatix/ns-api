import sys
import datetime
import logging
from ns_api import ns_api
import settings
from pushbullet import PushBullet
import pylibmc
import urllib2

def unique(my_list): 
    result = []
    for item in my_list:
        if item not in result:
            result.append(item)
    return result

# Only plan routes that are at maximum half an hour in the past or an hour in the future
MAX_TIME_PAST = 1800
MAX_TIME_FUTURE = 3600

# create logger
logger = logging.getLogger('ns_api')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('ns_api.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

api_key = settings.pushbullet_key
p = PushBullet(api_key)
# Get a list of devices. A device to push this to will be selected later on
devices = p.getDevices()

logger.debug(devices)

mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})

should_run = True
if 'nsapi_run' in mc:
    should_run = mc['nsapi_run']
else:
    logger.info('no run tuple in memcache, creating')
    mc['nsapi_run'] = should_run

logger.debug('should_run: %s' % should_run)

if should_run == False:
    sys.exit(0)

delays = []

today = datetime.datetime.now().strftime('%d-%m')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now()

for route in settings.routes:
    route_time = datetime.datetime.strptime(today_date + " " + route['time'], "%d-%m-%Y %H:%M")
    delta = current_time - route_time
    if current_time > route_time and delta.total_seconds() > MAX_TIME_PAST:
        # the route was too long ago ago, lets skip it
        logger.info('route %s was too long ago, skipped' % route)
        continue
    if current_time < route_time and abs(delta.total_seconds()) > MAX_TIME_FUTURE:
        # the route is too much in the future, lets skip it
        logger.info('route %s was too much in the future, skipped' % route)
        continue

    try:
        route_delays, vertrekken = ns_api.vertrektijden(route['departure'])
        for vertrek in vertrekken:
            logger.debug(vertrek)
            #print vertrek
            if route['keyword'] == None:
                if vertrek['delay'] > 0  and route['destination'] in vertrek['route']:
                    delays.append("{4}:\n{2} {3} heeft {0} minuten vertraging naar {1}".format(vertrek['delay'], vertrek['destination'], vertrek['details'], vertrek['route'], route['departure']))
                # 'Rijdt vandaag niet'
                if 'Rijdt' in vertrek['details'] and route['destination'] in vertrek['route']:
                    delays.append("{4}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
            else:
                if vertrek['delay'] > 0  and route['keyword'] in vertrek['route']:
                    delays.append("{4}:\n{2} {3} heeft {0} minuten vertraging naar {1}".format(vertrek['delay'], vertrek['destination'], vertrek['details'], vertrek['route'], route['departure']))
                # 'Rijdt vandaag niet'
                if 'Rijdt' in vertrek['details'] and route['keyword'] in vertrek['route']:
                    delays.append("{3}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
    except urllib2.URLError, e:
        delays.append('Error occurred: {0}'.format(e))

    try:
        planned_route = ns_api.route(route['departure'], route['destination'], '', today, route['time'])
        logger.debug(planned_route)

        if planned_route[0]:
            route_text = 'Route {0} - {1} van {2}'.format(route['departure'], route['destination'], planned_route[0]['departure'])

            if planned_route[0]['departure_delay'] > 0:
                delays.append("{0}\nVertrekvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['departure_delay'], planned_route[0]['departure_platform']))
            if planned_route[0]['arrival_delay'] > 0:
                delays.append("{0}\nAankomstvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['arrival_delay'], planned_route[0]['arrival_platform']))

            if 'arrival_platform_mutation' in planned_route[0]:
                # the platform is changed
                delays.append('{0}\nKomt op ander perron aan, namelijk {1}'.format(route_text, planned_route[0]['arrival_platform']))
    except urllib2.URLError, e:
        delays.append('Error occurred: {0}'.format(e))

logger.debug('all current delays: %s' % delays)

# deduplicate the list (useful when having multiple routes from the same origin):
if len(delays) > 1:
    delays = unique(delays)

logger.debug('current delays, deduped: %s' % delays)

should_send = False

# Check whether there are previous delays in memcache
if 'nsapi_delays' not in mc:
    logger.info('previous delays not found')
    should_send = True
elif mc['nsapi_delays'] != delays:
    logger.info('new delays are different: %s vs %s' % (mc['delays'], delays))
    should_send = True

if should_send == True:
    logger.debug('stored new delays in memcache')
    mc['nsapi_delays'] = delays

    if len(delays) > 0:
        # Send a note with all delays to device 5 of the list from PushBullet:
        logger.info('sending delays to device %s with index %s' % (devices[settings.device_index]["extras"]["model"], settings.device_index))
        p.pushNote(devices[settings.device_index]["id"], 'NS Vertraging', "\n\n".join(delays))
