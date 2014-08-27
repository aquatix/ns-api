ns_api
======

Query the Dutch railways about your routes, getting info on delays and more. See below for the syntax and example output.

## Example application

For example, I use the library to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). Clone [pyPushBullet](https://github.com/Azelphur/pyPushBullet) and include the pushbullet.py in your project. The program I use to do this is included in the repository as `notifications_pushbullet.py`, which I automated through a crontab entry to check around the times I want. To run it, first install its dependencies if you didn't already have them:

* On Debian-based distro's, install `memcached`, `python-pylibmc` and `python-bs4`, the latter (BeautifulSoup) is needed for `ns_api.py`.
* With pip, install `pylibmc`, `BeautifulSoup4`, `requests`. You need to have memcached running on your system.

As pyPushbullet has been recently rewritten to use Pushbullet's API v2, we also need python-magic and python-websocket:

* On Debian-based distro's, apt-get install `python-magic` and `python-websocket` (might be `websocket-client` on for example Ubuntu 12.04).
* With pip, install `magic` and `websocket`.

Then copy `settings_example.py` to `settings.py` and modify the configuration to your needs. You might want to check which index your desired device is on in the Pushbullet list (you can also go to your account on [Pushbullet.com](https://www.pushbullet.com/) and count in your device list, starting with 0 for the first).

`notifications_pushbullet.py` is best called through a crontab entry, for example:

```
# Call every five minutes from 7 to 10 and then from 16 to 18 hours:
*/5  7-9  * * 1-5 cd /home/username/bin/crontab/ns_api; /usr/bin/python notifications_pushbullet.py
*/5 16-17 * * 1-5 cd /home/username/bin/crontab/ns_api; /usr/bin/python notifications_pushbullet.py
```

It can be disabled by setting the `nsapi_run` tuple in memcache to `False`.

`notifications_server.py` has been included to provide a web interface.

```
pip install Flask
```

## Methods

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
