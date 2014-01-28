import ns_api
import datetime
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

apiKey = "YOURKEYHERE"
p = PushBullet(apiKey)
# Get a list of devices
devices = p.getDevices()

delays = []

today = datetime.datetime.now().strftime('%d-%m')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now()

routes = [
         {'departure': 'Heemskerk', 'destination': 'Hoofddorp', 'time': '7:40', 'keyword': 'Beverwijk' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Hoofddorp', 'time': '8:19', 'keyword': None },
         {'departure': 'Schiphol', 'destination': 'Hoofddorp', 'time': '8:45', 'keyword': None },
         {'departure': 'Hoofddorp', 'destination': 'Heemskerk', 'time': '17:05', 'keyword': 'Hoorn' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Heemskerk', 'time': '17:39', 'keyword': 'Haarlem' },
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Nijmegen', 'time': '21:40', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Schiphol', 'time': '22:19', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Amersfoort', 'time': '22:09', 'keyword': None }, # test
         ]

for route in routes:
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
