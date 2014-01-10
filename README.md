ns-api
======

Query the Dutch railways about your routes, getting info on delays and more. See below for the syntax.

For example, I use it to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). Clone [pyPushBullet](https://github.com/Azelphur/pyPushBullet) and include the pushbullet.py in your project. Then do something like this, which I automated through a crontab entry to check around the times I want:

```python
import ns_api
import datetime
from pushbullet import PushBullet

def unique(my_list): 
    result = []
    for item in my_list:
        if item not in result:
            result.append(item)
    return result

apiKey = "YOUR_KEY_HERE"
p = PushBullet(apiKey)
# Get a list of devices
devices = p.getDevices()

delays = []

today = datetime.datetime.now().strftime('%d-%m')
today_date = datetime.datetime.now().strftime('%d-%m-%Y')
current_time = datetime.datetime.now()

# keyword is used to filter routes. It's generally part of the "Sprinter <city1>, <city2>, <city3> sentence.
routes = [
         {'departure': 'Heemskerk', 'destination': 'Hoofddorp', 'time': '8:40', 'keyword': 'Beverwijk' },
         {'departure': 'Hoofddorp', 'destination': 'Heemskerk', 'time': '17:05', 'keyword': 'Hoorn' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Schiphol', 'time': '22:19', 'keyword': None }, # test
         ]

for route in routes:
    route_time = datetime.datetime.strptime(today_date + " " + route['time'], "%d-%m-%Y %H:%M")
    delta = current_time - route_time
    if current_time > route_time and delta.total_seconds() > 1800:
        # the route was more than half an hour ago, lets skip it
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
```

Which is called through a crontab entry, for example:

```
# Call every five minutes from 7 to 10 and then from 16 to 18 hours:
*/5  7-9  * * 1-5 cd /home/username/bin/crontab/notifications; /usr/bin/python ns_notifications_pushbullet.py
*/5 16-17 * * 1-5 cd /home/username/bin/crontab/notifications; /usr/bin/python ns_notifications_pushbullet.py
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
        'route': u'Leiden C.',
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

So, for example:

```python
>>> ns_api.vertrektijden('Hoofddorp')
([], [{'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'12:38'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Hilversum', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'12:52'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Amsterdam C.", 'destination': u'Amersfoort Vathorst', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'12:53'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Zaandam", 'destination': u'Hoorn Kersenboogerd', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:05'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Almere Oostvaarders', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:06'}, {'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'13:08'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Hilversum', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:22'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Amsterdam C.", 'destination': u'Amersfoort Vathorst', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:23'}, {'delay_unit': '', 'route': u"Schiphol, A'dam Sloterdijk, Zaandam", 'destination': u'Hoorn Kersenboogerd', 'delay': 0, 'platform': u'3', 'details': u'Sprinter', 'time': u'13:35'}, {'delay_unit': '', 'route': u'Schiphol, Duivendrecht, Weesp', 'destination': u'Almere Oostvaarders', 'delay': 0, 'platform': u'4', 'details': u'Sprinter', 'time': u'13:36'}, {'delay_unit': '', 'route': u'Leiden C.', 'destination': u'Den Haag Centraal', 'delay': 0, 'platform': u'1', 'details': u'Sprinter', 'time': u'13:38'}])

>>> ns_api.route('hoofddorp', 'sloterdijk', '', '06-01', '13:00')
[{'arrival': u'13:20', 'arrival_delay': 0, 'departure_platform': u'Hoofddorp  platform 3', 'departure': u'13:05', 'train': u'Sprinter NS direction Schiphol', 'departure_delay': 0, 'arrival_platform': u'Amsterdam Sloterdijk  platform 9'}]

>>> ns_api.werkzaamheden()
[{'info': u'in de nacht van vrijdag 10 op zaterdag 11 januari tot 07.00 uur', 'route': u'Den Helder-Schagen'}, {'info': u'zaterdag 11 januari tot 17.00 uur', 'route': u"Tilburg Universiteit/'s-Hertogenbosch-Eindhoven/Deurne"}, {'info': u'in de nacht van zaterdag 11 op zondag 12 januari vanaf 00.10 uur tot 09.30 uur', 'route': u'Amsterdam Centraal-Haarlem/Zaandam'}, {'info': u'in de nacht van zaterdag 11 op zondag 12 januari na 01.00 uur', 'route': u'Schagen-Den Helder'}, {'info': u'in de nacht van zaterdag 11 op zondag 12 januari vanaf 03.30 uur tot 05.30 uur', 'route': u'Breda-Tilburg'}, {'info': u'zondag 12 januari', 'route': u'Den Haag Centraal-Rotterdam Centraal'}, {'info': u'in de nacht van zondag 12 op maandag 13 januari vanaf 23.20 uur tot 04.00 uur', 'route': u'Sittard-Maastricht Randwyck'}, {'info': u'in de nacht van zondag 12 op maandag 13 januari na 00.15 uur', 'route': u'Utrecht Centraal-Geldermalsen'}, {'info': u'maandag 13 januari tot 05.50 uur', 'route': u'Utrecht Centraal-Geldermalsen'}, {'info': u'in de nacht van maandag 13 op dinsdag 14 januari vanaf 00.20 uur', 'route': u'Emmen-Zwolle'}, {'info': u'in de nacht van maandag 13 op dinsdag 14 januari tussen 00.20 uur en 00.50 uur', 'route': u'Utrecht Centraal-Geldermalsen'}, {'info': u'dinsdag 14 januari tot 06.00 uur', 'route': u'Utrecht Centraal-Geldermalsen'}, {'info': u'in de nacht van dinsdag 14 op woensdag 15 januari vanaf 23.45 uur', 'route': u'Delfzijl-Appingedam'}, {'info': u'in de nacht van donderdag 16 op vrijdag 17 januari vanaf 23.45 uur', 'route': u'Emmen-Zwolle'}, {'info': u'zaterdag 18 januari', 'route': u'Utrecht Centraal-Utrecht Maliebaan'}, {'info': u'zaterdag 18 en zondag 19 januari', 'route': u"'s-Hertogenbosch-Utrecht Centraal/Nijmegen/Boxtel"}, {'info': u'zondag 19 januari', 'route': u'Woerden-Utrecht Centraal'}, {'info': u'in de nacht van zondag 19 op maandag 20 januari na 00.15 uur', 'route': u'Utrecht Centraal-Geldermalsen'}, {'info': u'maandag 20 januari tot 05.50 uur', 'route': u'Utrecht Centraal-Geldermalsen'}]
```
