"""
Library to query the official Dutch railways API
"""
import urllib2
import urllib
import xmltodict
import time

from datetime import datetime, timedelta

from pytz.tzinfo import StaticTzInfo

import json
from collections import OrderedDict


class OffsetTime(StaticTzInfo):
    def __init__(self, offset):
        """
        A dumb timezone based on offset such as +0530, -0600, etc.
        """
        hours = int(offset[:3])
        minutes = int(offset[0] + offset[3:])
        self._utcoffset = timedelta(hours=hours, minutes=minutes)

def load_datetime(value, dt_format):
    """
    Create timezone-aware datetime object
    """
    if dt_format.endswith('%z'):
        dt_format = dt_format[:-2]
        offset = value[-5:]
        value = value[:-5]
        return OffsetTime(offset).localize(datetime.strptime(value, dt_format))

    return datetime.strptime(value, dt_format)

def dump_datetime(value, dt_format):
    """
    Format datetime object to string
    """
    return value.strftime(dt_format)


class Departure(object):
    """
    Information on a departing train on a certain station
    """

    def __init__(self, departure_dict):
        self.trip_number = departure_dict['RitNummer']
        self.departure_time = departure_dict['VertrekTijd']
        try:
            self.has_delay = True
            self.departure_delay = departure_dict['VertrekVertraging']
            self.departure_delay_text = departure_dict['VertrekVertragingTekst']
        except KeyError:
            self.has_delay = False
        self.departure_platform = departure_dict['VertrekSpoor']
        self.departure_platform_changed = departure_dict['VertrekSpoor']['@wijziging']

        self.destination = departure_dict['EindBestemming']
        try:
            self.route_text = departure_dict['RouteTekst']
        except KeyError:
            self.route_text = None

        self.train_type = departure_dict = ['TreinSoort']
        self.carrier = departure_dict = ['Vervoerder']

        try:
            self.journey_tip = departure_dict = ['ReisTip']
        except KeyError:
            self.journey_tip = None

        try:
            self.remarks = departure_dict = ['Opmerkingen']
        except KeyError:
            self.remarks = []


    def __unicode__(self):
        return 'trip_number: ' + self.trip_number


class TripStop(object):

    def __init__(self, part_dict):
        self.name = part_dict['Naam']
        self.time = part_dict['Tijd']
        self.platform = part_dict['Spoor']


class TripSubpart(object):

    def __init__(self, part_dict):
        self.trip_type = part_dict['@reisSoort']
        self.transporter = part_dict['Vervoerder']
        self.transport_type = part_dict['VervoerType']
        self.journey_id = part_dict['RitNummer']
        self.status = part_dict['Status']

    def __unicode__(self):
        print self.trip_type
        return self.trip_type


class Trip(object):

    def __init__(self, trip_dict):
        self.nr_transfers = trip_dict['AantalOverstappen']
        self.travel_time_planned = trip_dict['GeplandeReisTijd']
        self.travel_time_actual = trip_dict['ActueleReisTijd']
        self.is_optimal = True if trip_dict['Optimaal'] == 'true' else False
        self.status = trip_dict['Status']

        dt_format = "%Y-%m-%dT%H:%M:%S%z"

        try:
            self.departure_time_planned = load_datetime(trip_dict['GeplandeVertrekTijd'], dt_format)
        except:
            self.departure_time_planned = None

        try:
            self.departure_time_actual = load_datetime(trip_dict['ActueleVertrekTijd'], dt_format)
        except:
            self.departure_time_actual = None

        try:
            self.arrival_time_planned = load_datetime(trip_dict['GeplandeAankomstTijd'], dt_format)
        except:
            self.arrival_time_planned = None

        try:
            self.arrival_time_actual = load_datetime(trip_dict['ActueleAankomstTijd'], dt_format)
        except:
            self.arrival_time_actual = None


        trip_parts = trip_dict['ReisDeel']
        print('-- trip_parts --')
        print(trip_parts)
        print '-------'
        print(len(trip_parts))
        print '-------'

        self.trip_parts = []
        for part in trip_dict['ReisDeel']:
            print('-- part --')
            print(part)
            print(type(part))
            if isinstance(part, unicode):
                # Only one item, make it a list
                part = [part]
                print part
                print('-- /changed part --')
            trip_part = TripSubpart(part)
            self.trip_parts.append(trip_part)

        print self.trip_parts

    def to_json(self):
        """
        Create a JSON representation of this model
        """
        # TODO implement
        return json.dumps(OrderedDict(self.__dict__))

    def from_json(self, source_json):
        """
        Parse a JSON representation of this model back to, well, the model
        """
        # TODO implement
        # json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(source_json)
        pass

    def delay_text(self):
        """
        If trip has delays, format a natural language summary
        """
        # TODO implement
        pass

    def __repr__(self):
        #return 'Trip repr'
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<Trip> plan: {0} actual: {1} transfers: {2}'.format(self.departure_time_planned, self.departure_time_actual, self.nr_transfers)


def parse_departures(xml):
    """
    Parse the NS API xml result into Departure objects
    @param xml: raw XML result from the NS API
    """
    obj = xmltodict.parse(xml)
    departures = []

    for departure in obj['ActueleVertrekTijden']['VertrekkendeTrein']:
        newdep = Departure(departure)
        departures.append(newdep)
        print('-- departure --')
        print(newdep)
        print repr(newdep)
        print(newdep.__dict__)
        print('-- /departure --')

    return departures


def get_departures(station):
    """
    Fetch the current departure times from this station
    @param station: station to lookup
    """
    url = 'http://www.ns.nl/actuele-vertrektijden/main.action?xml=true'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header = {'User-Agent' : user_agent}

    values = {
        'van_heen_station' : station,
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data, header)
    response = urllib2.urlopen(req)
    page = response.read()
    #soup = BeautifulSoup(page)
    disruptions = []


def parse_trips(xml):
    """
    Parse the NS API xml result into Trip objects
    """
    obj = xmltodict.parse(xml)
    trips = []

    for trip in obj['ReisMogelijkheden']['ReisMogelijkheid']:
        #print departure
        newtrip = Trip(trip)
        trips.append(newtrip)
        print('-- trip --')
        print repr(newtrip)
        print(newtrip)
        print(newtrip.__dict__)
        print('-- /trip --')


def get_trips(starttime, start, via, destination):
    """
    Fetch trip possibilities for these parameters
    """
    # TODO implement
    pass
