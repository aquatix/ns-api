# Example configuration. Copy to settings.py and modify to your needs

# Pushbullet API key. See their website
pushbullet_key = "YOURKEYHERE"
# Device to push to. See p.getDevices() for the List of which to choose
device_id = "DEVICEKEYHERE"

arrival_delays = True
# Uncomment the next two lines if you only want ERROR-level logging (or change to logging.WARNING for example)
#import logging
#debug_level = logging.ERROR

# 'minimum': amount of time a delay needs to be at minimum for which a notification is fired
# 'strict': if True and no connection is found for that exact time stamp, 'train cancelled' is fired
routes = [
        {'departure': 'Heemskerk', 'destination': 'Hoofddorp', 'time': '7:44', 'keyword': 'Beverwijk', 'minimum': 5, 'strict': True },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Hoofddorp', 'time': '8:19', 'keyword': None },
         {'departure': 'Schiphol', 'destination': 'Hoofddorp', 'time': '9:15', 'keyword': None },
         {'departure': 'Hoofddorp', 'destination': 'Heemskerk', 'time': '17:05', 'keyword': 'Hoorn', 'minimum': 3 },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Heemskerk', 'time': '17:39', 'keyword': 'Haarlem', 'strict': True },
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Nijmegen', 'time': '21:40', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Schiphol', 'time': '22:19', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Amersfoort', 'time': '22:09', 'keyword': None }, # test
         ]
