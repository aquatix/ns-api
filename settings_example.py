# Example configuration. Copy to settings.py and modify to your needs

# Pushbullet API key. See their website
pushbullet_key = "YOURKEYHERE"
# Device to push to. See p.getDevices() for the List of which to choose
device_index = 0

routes = [
         {'departure': 'Heemskerk', 'destination': 'Hoofddorp', 'time': '7:40', 'keyword': 'Beverwijk' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Hoofddorp', 'time': '8:19', 'keyword': None },
         {'departure': 'Schiphol', 'destination': 'Hoofddorp', 'time': '9:15', 'keyword': None },
         {'departure': 'Hoofddorp', 'destination': 'Heemskerk', 'time': '17:05', 'keyword': 'Hoorn' },
         {'departure': 'Amsterdam Sloterdijk', 'destination': 'Heemskerk', 'time': '17:39', 'keyword': 'Haarlem' },
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Nijmegen', 'time': '21:40', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Schiphol', 'time': '22:19', 'keyword': None }, # test
         #{'departure': 'Amsterdam Sloterdijk', 'destination': 'Amersfoort', 'time': '22:09', 'keyword': None }, # test
         ]
