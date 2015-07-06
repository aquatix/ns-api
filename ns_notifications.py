"""
NS trip notifier
"""
from ns_api import ns_api
from pushbullet import PushBullet
import pylibmc
#import simplejson as json
import __main__ as main


mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})


#if hasattr(main, '__file__'):
#    """
#    Running in interactive mode in the Python shell
#    """
#    print("Running interactively in Python shell")

#elif __name__ == '__main__':
if __name__ == '__main__':
    """
    Notifier is ran standalone, rock and roll
    """

    departures = []
    with open('examples.xml') as fd:
        departures = ns_api.parse_departures(fd.read())

    trips = []
    with open('reismogelijkheden.xml') as fd:
        trips = ns_api.parse_trips(fd.read())
