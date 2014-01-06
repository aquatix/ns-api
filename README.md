ns-api
======

Query the Dutch railways about your routes, getting info on delays and more. See below for the syntax.

For example, I use it to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). Clone [pyPushBullet](https://github.com/Azelphur/pyPushBullet) and include the pushbullet.py in your project. Then do something like this, which I automated through a crontab entry to check around the times I want:

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
                delays.append("{3}:\n{2} naar {1}: {0}".format(vertrek['details'], vertrek['destination'], vertrek['route'], route['departure']))

    route_text = 'Route {0} - {1} van {2}'.format(route['departure'], route['destination'], route['time'])

    planned_route = ns_api.route(route['departure'], route['destination'], '', today, route['time'])
    if planned_route[0]['departure_delay'] > 0:
        delays.append("{0}\nVertrekvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['departure_delay'], planned_route[0]['departure_platform']))
    if planned_route[0]['arrival_delay'] > 0:
        delays.append("{0}\nAankomstvertraging: {1} minuten op {2}".format(route_text, planned_route[0]['arrival_delay'], planned_route[0]['arrival_platform']))

if len(delays) > 0:
	# Send a note with all delays to device 5 of the list from PushBullet:
	p.pushNote(devices[5]["id"], 'NS Vertraging', "\n\n".join(delays))
```

The call `vertrektijden` returns two lists containing dicts. The first list is the list with current disruptions and work (I think those are network-wide). Syntax:

```python
[
	{'route': 'Amsterdam Centraal - Groningen', 'info': 'Stuk'},

]
```

The second list is the info you explicitely requested:

```python
[
    {
        'delay_unit': '',
        'route': u'LeidenC.',
        'destination': u'Den Haag Centraal',
        'delay': 0,
        'platform': u'1',
        'details': u'Sprinter',
        'time': u'12:38'
    },
    {
        'delay_unit': '',
        'route': u'Schiphol, Duivendrecht, Weesp',
        'destination': u'Hilversum',
        'delay': 0,
        'platform': u'4',
        'details': u'Sprinter',
        'time': u'12:52'
    },
    {
        'delay_unit': '',
        'route': u"Schiphol, A'dam Sloterdijk, Amsterdam C.",
        'destination': u'Amersfoort Vathorst',
        'delay': 0,
        'platform': u'3',
        'details': u'Sprinter',
        'time': u'12:53'
    },
    {
        'delay_unit': '',
        'route': u"Schiphol, A'dam Sloterdijk, Zaandam",
        'destination': u'Hoorn Kersenboogerd',
        'delay': 0,
        'platform': u'3',
        'details': u'Sprinter',
        'time': u'13:05'
    },
    {
        'delay_unit': 'm',
        'route': u'Schiphol, Duivendrecht, Weesp',
        'destination': u'Almere Oostvaarders',
        'delay': 6,
        'platform': u'4',
        'details': u'Sprinter',
        'time': u'13:06'
    },
]

```

So, example:

```python
>>> ns_api.vertrektijden('Hoofddorp')
([], [{'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'12:38'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Hilversum', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'12:52'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Amsterdam C.", 'destination': u'Amersfoort Vathorst', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'12:53'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Zaandam", 'destination': u'Hoorn Kersenboogerd', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:05'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Almere Oostvaarders', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:06'}, {'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'13:08'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Hilversum', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:22'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Amsterdam C.", 'destination': u'Amersfoort Vathorst', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:23'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Zaandam", 'destination': u'Hoorn Kersenboogerd', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:35'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Almere Oostvaarders', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:36'}, {'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'13:38'}])

>>> ns_api.route('hoofddorp', 'sloterdijk', '', '06-01', '13:00')
[{'arrival': u'13:20', 'arrival_delay': 0, 'departure_platform': u'Hoofddorp  platform 3', 'departure': u'13:05', 'train': u'Sprinter NS direction Schiphol', 'departure_delay': 0, 'arrival_platform': u'Amsterdam Sloterdijk  platform 9'}]
```
