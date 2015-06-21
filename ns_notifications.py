"""
NS trip notifier
"""
from ns_api import ns_api
from pushbullet import PushBullet
import pylibmc
import urllib2
import __main__ as main



mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})


if hasattr(main, '__file__'):
    """
    Running in interactive mode in the Python shell
    """
    print("Running interactively in Python shell")

elif __name__ == '__main__':
    """
    Notifier is ran standalone, rock and roll
    """
    print("Run!")

    #with open('actuele_vertrektijden.xml') as fd:
    with open('examples.xml') as fd:
        obj = xmltodict.parse(fd.read())

    departures = []

    #for departure in obj['ActueleVertrekTijden']:
    #    print departure['VertrekkendeTrein']
    for departure in obj['ActueleVertrekTijden']['VertrekkendeTrein']:
        #print departure
        newdep = Departure(departure)
        departures.append(newdep)
        print repr(newdep)



    with open('reismogelijkheden.xml') as fd:
        obj = xmltodict.parse(fd.read())

    trips = []

    for trip in obj['ReisMogelijkheden']['ReisMogelijkheid']:
        #print departure
        newtrip = Trip(trip)
        trips.append(newtrip)
        print repr(newtrip)

