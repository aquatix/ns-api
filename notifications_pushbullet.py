import ns-api.ns_api
import datetime
import settings
from pushbullet import PushBullet

def unique(my_list): 
    result = []
    for item in my_list:
        if item not in result:
            result.append(item)
    return result

# Only plan routes that are at maximum half an hour in the past or an hour in the future
MAX_TIME_PAST = 1800
MAX_TIME_FUTURE = 3600

api_key = settings.pushbullet_key
p = PushBullet(apiKey)
# Get a list of devices
devices = p.getDevices()

delays = []

today = datetime.datetime.now().strftime('%d-%m')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now()

for route in settings.routes:
    route_time = datetime.datetime.strptime(today_date + " " + route['time'], "%d-%m-%Y %H:%M")
    delta = current_time - route_time
    if current_time > route_time and delta.total_seconds() > MAX_TIME_PAST:
        # the route was too long ago ago, lets skip it
        continue
    if current_time < route_time and abs(delta.total_seconds()) > MAX_TIME_FUTURE:
        # the route is too much in the future, lets skip it
        continue

    route_delays, vertrekken = ns_api.vertrektijden(route['departure'])
    for vertrek in vertrekken:
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

    route_text = 'Route {0} - {1} van {2}'.format(route['departure'], route['destination'], route['time'])

    planned_route = ns_api.route(route['departure'], route['destination'], '', today, route['time'])
    if planned_route[0]['departure_delay'] > 0:
        delays.append("{0}\nVertrekvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['departure_delay'], planned_route[0]['departure_platform']))
    if planned_route[0]['arrival_delay'] > 0:
        delays.append("{0}\nAankomstvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['arrival_delay'], planned_route[0]['arrival_platform']))

# deduplicate the list (useful when having multiple routes from the same origin):
if len(delays) > 1:
    delays = unique(delays)

if len(delays) > 0:
    # Send a note with all delays to device 5 of the list from PushBullet:
    p.pushNote(devices[5]["id"], 'NS Vertraging', "\n\n".join(delays))
