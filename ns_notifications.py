"""
NS trip notifier
"""
from ns_api import ns_api
from pushbullet import PushBullet
import pylibmc
import urllib2



mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})


if __name__ == '__main__':
    """
    Notifier is ran standalone, rock and roll
    """
    print("Run!")
