"""
Library to query the official Dutch railways API
"""
import urllib2
import time

from datetime import datetime, timedelta

from pytz import timezone, utc
from pytz.tzinfo import StaticTzInfo


class OffsetTime(StaticTzInfo):
    def __init__(self, offset):
        """
        A dumb timezone based on offset such as +0530, -0600, etc.
        """
        hours = int(offset[:3])
        minutes = int(offset[0] + offset[3:])
        self._utcoffset = timedelta(hours=hours, minutes=minutes)

def load_datetime(value, format):
    if format.endswith('%z'):
        format = format[:-2]
        offset = value[-5:]
        value = value[:-5]
        return OffsetTime(offset).localize(datetime.strptime(value, format))

    return datetime.strptime(value, format)

def dump_datetime(value, format):
    return value.strftime(format)


class Departure():

    def __init__(self, departure_dict):
        trip_number = departure_dict['RitNummer']
        departure_time = departure_dict['VertrekTijd']
        try:
            has_delay = True
            departure_delay = departure_dict['VertrekVertraging']
            departure_delay_text = departure_dict['VertrekVertragingTekst']
        except:
            has_delay = False
        departure_platform = departure_dict['VertrekSpoor']
        departure_platform_changed = departure_dict['VertrekSpoor']['@wijziging']

        destination = departure_dict['EindBestemming']
        try:
            route_text = departure_dict['RouteTekst']
        except KeyError:
            route_text = None

        train_type = departure_dict=['TreinSoort']
        carrier = departure_dict=['Vervoerder']

        try:
            journey_tip = departure_dict=['ReisTip']
        except KeyError:
            journey_tip = None

        try:
            remarks = departure_dict=['Opmerkingen']
        except KeyError:
            remarks = []


    def __unicode__(self):
        return 'trip_number: ' + self.trip_number


class TripStop():

    def __init__(self, part_dict):
        name = part_dict['Naam']
        time = part_dict['Tijd']
        platform = part_dict['Spoor']


class TripSubpart():

    def __init__(self, part_dict):
        transporter = part_dict['Vervoerder']
        transport_type = part_dict['VervoerType']
        journey_id = part_dict['RitNummer']
        status = part_dict['Status']


class Trip():

    def __init__(self, trip_dict):
        nr_transfers = trip_dict['AantalOverstappen']
        travel_time_planned = trip_dict['GeplandeReisTijd']
        travel_time_actual = trip_dict['ActueleReisTijd']
        is_optimal = True if trip_dict['Optimaal'] == 'true' else False
        status = trip_dict['Status']

        format = "%Y-%m-%dT%H:%M:%S%z"

        #departure_time_planned = time.strptime(trip_dict['GeplandeVertrekTijd'], "%Y-%m-%dT%H:%M:%S%z")
        try:
            #departure_time_planned = time.strptime(trip_dict['GeplandeVertrekTijd'], "")
            departure_time_planned = load_datetime(trip_dict['GeplandeVertrekTijd'], format)
        except:
            departure_time_planned = None
        print departure_time_planned

        try:
            departure_time_actual = load_datetime(trip_dict['ActueleVertrekTijd'], format)
        except:
            departure_time_actual = None

        try:
            arrival_time_planned = load_datetime(trip_dict['GeplandeAankomstTijd'], format)
        except:
            arrival_time_planned = None

        try:
            arrival_time_actual = load_datetime(trip_dict['ActueleAankomstTijd'], format)
        except:
            arrival_time_actual = None


        trip_parts = trip_dict['ReisDeel']
        print(trip_parts)
        print 'wtf'

        trip_parts = []
        for part in trip_dict['ReisDeel']:
            trip_part = TripSubpart(part)
            trip_parts.append(trip_part)

        print trip_parts


    def __unicode__(self):
        return 'departure_time_planned: ' + self.departure_time_planned


def get_departures(self, station):
    url = 'http://www.ns.nl/actuele-vertrektijden/main.action?xml=true'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header = { 'User-Agent' : user_agent }

    values = {
        'van_heen_station' : station,
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data, header)
    response = urllib2.urlopen(req)
    page = response.read()
    soup = BeautifulSoup(page)
    disruptions = []

