ns-api
======

Query the Dutch railways about your routes, getting info on delays and more.

For example, I use it to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). Clone [pyPushBullet](https://github.com/Azelphur/pyPushBullet) and include the pushbullet.py in your project. Then do something like this:

```python
import ns_api
import datetime
from pushbullet import PushBullet

apiKey = "YOUR_KEY_HERE"
p = PushBullet(apiKey)
# Get a list of devices
devices = p.getDevices()

delays = []

today = datetime.datetime.now().strftime('%d-%m')

# keyword is used to filter routes. It's generally part of the "Sprinter <city1>, <city2>, <city3> sentence.
routes = [
         {'departure': 'Heemskerk', 'destination': 'Hoofddorp', 'time': '8:40', 'keyword': 'Beverwijk' },
         {'departure': 'Hoofddorp', 'destination': 'Heemskerk', 'time': '17:05', 'keyword': 'Hoorn' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Schiphol', 'time': '22:19', 'keyword': None }, # test
         ]

for route in routes:
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
                delays.append("{4}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))

    route_text = 'Route {0} - {1} van {2}'.format(route['departure'], route['destination'], route['time'])

    planned_route = ns_api.route(route['departure'], route['destination'], '', today, route['time'])
    if planned_route[0]['departure_delay'] > 0:
        delays.append("{0}\nVertrekvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['departure_delay'], planned_route[0]['departure_platform']))
    if planned_route[0]['arrival_delay'] > 0:
        delays.append("{0}\nAankomstvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['arrival_delay'], planned_route[0]['arrival_platform']))

if len(delays) > 0:
	# Send a note
	p.pushNote(devices[5]["id"], 'NS Vertraging', "\n".join(delays))
```
