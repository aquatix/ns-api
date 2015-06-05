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
try:
    logger.setLevel(settings.debug_level)
except:
    logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('ns_api_{0}.log'.format(datetime.date.today().isoformat()))
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

mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})

should_run = True
if 'nsapi_run' in mc:
    should_run = mc['nsapi_run']
else:
    logger.info('no run tuple in memcache, creating')
    mc['nsapi_run'] = should_run

logger.debug('should_run: %s', should_run)

if not should_run:
    sys.exit(0)

delays = []
disruptions = []

today = datetime.datetime.now().strftime('%d-%m')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now()

for route in settings.routes:
    route_time = datetime.datetime.strptime(today_date + " " + route['time'], "%d-%m-%Y %H:%M")
    delta = current_time - route_time
    if current_time > route_time and delta.total_seconds() > MAX_TIME_PAST:
        # the route was too long ago ago, lets skip it
        logger.info('route %s was too long ago, skipped', route)
        continue
    if current_time < route_time and abs(delta.total_seconds()) > MAX_TIME_FUTURE:
        # the route is too much in the future, lets skip it
        logger.info('route %s was too much in the future, skipped', route)
        continue

    try:
        verstoringen, vertrekken = ns_api.vertrektijden(route['departure'])
        for disruption in verstoringen:
            logger.debug(disruption)
            disruptions.append(u'{0}: {1}'.format(disruption['route'], disruption['info']))
        for vertrek in vertrekken:
            logger.debug(vertrek)
            if route['keyword'] == None:
                if vertrek['delay'] > 0  and route['destination'] in vertrek['route'] and ('minimum' in route and vertrek['delay'] >= route['minimum']):
                    delays.append("{4}:\n{2} {3} heeft {0} minuten vertraging naar {1}".format(vertrek['delay'], vertrek['destination'], vertrek['details'], vertrek['route'], route['departure']))
                # 'Rijdt vandaag niet'
                if 'Rijdt' in vertrek['details'] and route['destination'] in vertrek['route']:
                    delays.append("{4}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
                elif route['destination'] in vertrek['route'] and 'strict' in route and route['strict'] == True and vertrek['time'] != route['time']:
                    logger.debug('Rijdt niet: {0}, {1}'.format(vertrek['time'], route['time']))
                    delays.append("{2} naar {1} van {3} rijdt vandaag niet".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
            else:
                if vertrek['delay'] > 0  and route['keyword'] in vertrek['route'] and ('minimum' in route and vertrek['delay'] >= route['minimum']):
                    #delays.append("{4}:\n{2} {3} heeft {0} minuten vertraging naar {1}".format(vertrek['delay'], vertrek['destination'], vertrek['details']))
                    delays.append("{1} {2} van {3} heeft {0} minuten vertraging naar {1}".format(vertrek['delay'], vertrek['destination'], vertrek['details'], vertrek['time']))
                # 'Rijdt vandaag niet'
                if 'Rijdt' in vertrek['details'] and route['keyword'] in vertrek['route']:
                    delays.append("{3}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
                elif route['destination'] in vertrek['route'] and 'strict' in route and route['strict'] == True and vertrek['time'] != route['time']:
                    logger.debug('Rijdt niet: {0}, {1}'.format(vertrek['time'], route['time']))
                    delays.append("{2} naar {1} van {3} rijdt vandaag niet".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))
    except urllib2.URLError, e:
        delays.append('Error occurred: {0}'.format(e))

    try:
        planned_route = ns_api.route(route['departure'], route['destination'], '', today, route['time'])
        logger.debug(planned_route)

        if planned_route[0]:
            route_text = 'Route {0} - {1} van {2}'.format(route['departure'], route['destination'], planned_route[0]['departure'])

            if planned_route[0]['departure_delay'] > 0 and ('minimum' in route and planned_route[0]['departure_delay'] >= route['minimum']):
                delays.append("{0}\nVertrekvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['departure_delay'], planned_route[0]['departure_platform']))
            if settings.arrival_delays and planned_route[0]['arrival_delay'] > 0 and ('minimum' in route and planned_route[0]['arrival_delay'] >= route['minimum']):
                delays.append("{0}\nAankomstvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['arrival_delay'], planned_route[0]['arrival_platform']))
            if 'strict' in route and route['strict'] == True and planned_route[0]['departure'] != route['time']:
                logger.debug('Rijdt niet: {0}, {1}'.format(planned_route[0]['departure'], route['time']))
                delays.append("{0} van {1} naar {2} van {3} rijdt vandaag niet".format(planned_route[0]['train'], route['destination'], route['departure'], route['time']))

            if 'arrival_platform_mutation' in planned_route[0]:
                # the platform is changed
                delays.append('{0}\nKomt op ander perron aan, namelijk {1}'.format(route_text, planned_route[0]['arrival_platform']))
    except urllib2.URLError, e:
        delays.append('Error occurred: {0}'.format(e))

logger.debug('all current delays: %s', delays)

# deduplicate the list (useful when having multiple routes from the same origin):
if len(delays) > 1:
    delays = unique(delays)
if len(disruptions) > 1:
    disruptions = unique(disruptions)

logger.debug('current delays, deduped: %s', delays)
logger.debug('all current disruptions, deduped: %s', disruptions)

should_send_disruptions = False
should_send_delays = False

disruptions_tosend = []
# Check whether there are previous disruptions in memcache
if 'nsapi_disruptions' not in mc:
    logger.info('previous disruptions not found')
    should_send_disruptions = True
    disruptions_tosend = disruptions
else:
    for disruption in disruptions:
        if disruption not in mc['nsapi_disruptions']:
            disruptions_tosend.append(disruption)
            logger.info('new disruption to be sent: %s', disruption)
            should_send_disruptions = True

if should_send_disruptions == True:
    logger.debug('stored new disruptions in memcache')
    mc['nsapi_disruptions'] = disruptions

    if len(disruptions_tosend) > 0:
        # Send a note with all delays to device with index settings.device_id of the list from PushBullet:
        api_key = settings.pushbullet_key
        p = PushBullet(api_key)
        logger.info('sending disruptions to device with id %s', (settings.device_id))
        p.pushNote(settings.device_id, 'NS Storing', "\n\n".join(disruptions_tosend))

delays_tosend = []
# Check whether there are previous delays in memcache
if 'nsapi_delays' not in mc:
    logger.info('previous delays not found')
    should_send_delays = True
    delays_tosend = delays
else:
    for delay in delays:
        if delay not in mc['nsapi_delays']:
            delays_tosend.append(delay)
            logger.info('new delay to be sent: %s', delay)
            should_send_delays = True

if should_send_delays == True:
    logger.debug('stored new delays in memcache')
    mc['nsapi_delays'] = delays

    if len(delays_tosend) > 0:
        # Send a note with all delays to device with index settings.device_id of the list from PushBullet:
        api_key = settings.pushbullet_key
        p = PushBullet(api_key)
        logger.info('sending delays to device with id %s', (settings.device_id))
        p.pushNote(settings.device_id, 'NS Vertraging', "\n\n".join(delays_tosend))
