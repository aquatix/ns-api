"""
Library to query the official Dutch railways API
"""

import collections
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import pytz
from pytz.tzinfo import StaticTzInfo

# ns-api library version
__version__ = '3.0.2'


# set placeholder url params
params = urllib.parse.urlencode({})


# Date/time helpers
NS_DATETIME = "%Y-%m-%dT%H:%M:%S%z"


def datetime_to_string(timestamp, dt_format='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime object to string
    """
    return timestamp.strftime(dt_format)


def simple_time(value):
    """
    Format a datetime or timedelta object to a string of format HH:MM
    """
    if isinstance(value, timedelta):
        return ':'.join(str(value).split(':')[:2])
    return datetime_to_string(value, '%H:%M')


# Timezone helpers

def is_dst(zonename):
    """
    Find out whether it's Daylight Saving Time in this timezone
    """
    tz = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.utcnow())
    return now.astimezone(tz).dst() != timedelta(0)


class OffsetTime(StaticTzInfo):
    """
    A dumb timezone based on offset such as +0530, -0600, etc.
    """

    def __init__(self, offset):
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
        if offset != offset.replace(':', ''):
            # strip : from HHMM if needed (isoformat() adds it between HH and MM)
            offset = '+' + offset.replace(':', '')
            value = value[:-1]
        return OffsetTime(offset).localize(datetime.strptime(value, dt_format))

    return datetime.strptime(value, dt_format)


# List helpers

def list_to_json(source_list):
    """
    Serialise all the items in source_list to json
    """
    result = []
    for item in source_list:
        result.append(item.to_json())
    return result


def list_from_json(source_list_json):
    """
    Deserialise all the items in source_list from json
    """
    result = []
    if source_list_json == [] or source_list_json is None:
        return result
    for list_item in source_list_json:
        item = json.loads(list_item)
        try:
            if item['class_name'] == 'Departure':
                temp = Departure()
            elif item['class_name'] == 'Disruption':
                temp = Disruption()
            elif item['class_name'] == 'Station':
                temp = Station()
            elif item['class_name'] == 'Trip':
                temp = Trip()
            elif item['class_name'] == 'TripRemark':
                temp = TripRemark()
            elif item['class_name'] == 'TripStop':
                temp = TripStop()
            elif item['class_name'] == 'TripSubpart':
                temp = TripSubpart()
            else:
                print('Unrecognised Class {}, skipping'.format(item['class_name']))
                continue
            temp.from_json(list_item)
            result.append(temp)
        except KeyError:
            print('Unrecognised item with no class_name, skipping')
            continue
    return result


def list_diff(list_a, list_b):
    """
    Return the items from list_b that differ from list_a
    """
    result = []
    for item in list_b:
        if item not in list_a:
            result.append(item)
    return result


def list_same(list_a, list_b):
    """
    Return the items from list_b that are also on list_a
    """
    result = []
    for item in list_b:
        if item in list_a:
            result.append(item)
    return result


def list_merge(list_a, list_b):
    """
    Merge two lists without duplicating items

    Args:
      list_a: list
      list_b: list
    Returns:
      New list with deduplicated items from list_a and list_b
    """
    # return list(collections.OrderedDict.fromkeys(list_a + list_b))
    result = []
    for item in list_a:
        if item not in result:
            result.append(item)
    for item in list_b:
        if item not in result:
            result.append(item)
    return result


# NS API objects
class BaseObject:
    """
    Base object with useful functions
    """

    def __getstate__(self):
        result = self.__dict__.copy()
        result['class_name'] = self.__class__.__name__
        return result

    def to_json(self):
        """
        Create a JSON representation of this model
        """
        # return json.dumps(self.__getstate__())
        return json.dumps(self.__getstate__(), ensure_ascii=False)

    def __setstate__(self, source_dict):
        if not source_dict:
            # Somehow the source is None
            return
        del source_dict['class_name']
        self.__dict__ = source_dict

    def from_json(self, source_json):
        """
        Parse a JSON representation of this model back to, well, the model
        """
        source_dict = json.JSONDecoder().decode(source_json)
        self.__setstate__(source_dict)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        raise NotImplementedError('subclasses must override __str__()')


class Station(BaseObject):
    """
    Information on a railway station
    """

    def __init__(self, stat_dict=None):
        if stat_dict is None:
            return
        self.eva_code = stat_dict['EVACode']
        self.code = stat_dict['code']
        self.uic_code = stat_dict['UICCode']
        self.stationtype = stat_dict['stationType']
        self.names = {
            'short': stat_dict['namen']['kort'],
            'middle': stat_dict['namen']['middel'],
            'long': stat_dict['namen']['lang']
        }
        self.country = stat_dict['land']
        self.lat = stat_dict['lat']
        self.lon = stat_dict['lng']
        self.synonyms = []
        self.has_facilities = stat_dict['heeftFaciliteiten']
        self.has_travel_assistance = stat_dict['heeftReisassistentie']
        self.has_departure_times = stat_dict['heeftVertrektijden']
        try:
            raw_synonyms = stat_dict['synoniemen']
            if isinstance(raw_synonyms, str):
                raw_synonyms = [raw_synonyms]
            for synonym in raw_synonyms:
                self.synonyms.append(synonym)
        except TypeError:
            self.synonyms = []

    def __str__(self):
        return '<Station> {0} {1}'.format(self.code, self.names['long'])


class Disruption(BaseObject):
    """
    Planned and unplanned disruptions of the railroad traffic
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.key = part_dict['id']
        self.line = part_dict['titel']
        self.disruption = part_dict['verstoring']
        self.timestamp = None

    def __getstate__(self):
        result = super(Disruption, self).__getstate__()
        result['timestamp'] = result['timestamp'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(Disruption, self).__setstate__(source_dict)
        self.timestamp = load_datetime(self.timestamp, NS_DATETIME)

    def __str__(self):
        return '<Disruption> {0}'.format(self.line)


class Departure(BaseObject):
    """
    Information on a departing train on a certain station
    """

    def __init__(self, departure_dict=None):
        if departure_dict is None:
            return
        self.key = departure_dict['product']['number'] + \
            '_' + departure_dict['plannedDateTime']
        self.trip_number = departure_dict['product']['number']
        self.departure_time_planned = load_datetime(
            departure_dict['plannedDateTime'], NS_DATETIME)
        self.departure_time = self.departure_time_planned  # Default to the planned time
        self.departure_status = departure_dict['departureStatus']
        self.cancelled = departure_dict['cancelled']
        self.delay = 0
        try:
            self.departure_time_actual = load_datetime(
                departure_dict['actualDateTime'], NS_DATETIME)
            if self.departure_time_actual is not None and self.departure_time_actual != self.departure_time_planned:
                self.has_delay = True
                delay = (self.departure_time_actual
                         - self.departure_time_planned)
                self.delay = delay.seconds // 60 % 60
        except KeyError:
            self.has_delay = False

        self.departure_platform = departure_dict['plannedTrack']

        try:
            self.departure_platform_actual = departure_dict['actualTrack']
            if self.departure_platform_actual != self.departure_time_planned:
                self.has_platform_changed = True
        except KeyError:
            self.has_platform_changed = False

        self.destination = departure_dict['direction']

        try:
            self.route_text = departure_dict['RouteTekst']
        except KeyError:
            self.route_text = None

        self.train_type = departure_dict['trainCategory']
        self.carrier = departure_dict['product']['operatorName']

    def __getstate__(self):
        result = super(Departure, self).__getstate__()
        result['departure_time'] = result['departure_time'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(Departure, self).__setstate__(source_dict)
        self.departure_time = load_datetime(
            source_dict['plannedDateTime'], NS_DATETIME)

    def __str__(self):
        return '<Departure> trip_number: {0} {1} {2}'.format(
            self.trip_number,
            self.destination,
            self.departure_time_planned
        )


class TripRemark(BaseObject):
    """
    Notes on this route, generally about disruptions
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.key = part_dict['Id']
        if part_dict['Ernstig'] == 'false':
            self.is_grave = False
        else:
            self.is_grave = True
        self.message = part_dict['Text']

    def __str__(self):
        return '<TripRemark> {0} {1}'.format(self.is_grave, self.message)


class TripStop(BaseObject):
    """
    Information on a stop on a route (station, time, platform)
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return

        self.name = part_dict['name']

        if 'passing' in part_dict and part_dict['passing']:
            return

        if 'plannedDepartureDateTime' in part_dict:
            try:
                self.planned_time = load_datetime(
                    part_dict['plannedDepartureDateTime'], NS_DATETIME)
                self.key = simple_time(self.planned_time) + '_' + self.name
            except TypeError:
                self.planned_time = None
                self.planned_key = None
        else:
            self.planned_time = None
            self.planned_key = None
        self.time = self.planned_time  # Default to planned time

        if 'actualDepartureDateTime' in part_dict:
            try:
                self.actual_time = load_datetime(
                    part_dict['actualDepartureDateTime'], NS_DATETIME)
                self.actual_key = simple_time(
                    self.actual_time) + '_' + self.name
            except TypeError:
                self.actual_time = None
                self.planned_key = None
        else:
            self.actual_time = None
            self.planned_key = None

        self.platform_changed = False
        if 'plannedDepartureTrack' in part_dict:
            self.planned_platform = part_dict['plannedDepartureTrack']

        if 'actualDepartureTrack' in part_dict:
            self.actual_platform = part_dict['actualDepartureTrack']
            self.platform_changed = bool(self.actual_platform != self.planned_platform)
        if self.actual_time is not None:
            try:
                self.delay = self.actual_time - self.planned_time
            except KeyError:
                self.delay = None

    def __getstate__(self):
        result = super(TripStop, self).__getstate__()
        result['time'] = result['time'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(TripStop, self).__setstate__(source_dict)
        self.time = load_datetime(self.time, NS_DATETIME)

    def __str__(self):
        return '<TripStop> {0}'.format(self.name)


class TripSubpart(BaseObject):
    """
    Sub route; each part means a transfer
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.trip_type = part_dict['travelType']
        self.transporter = part_dict['product']['operatorName']
        self.transport_type = part_dict['product']['categoryCode']
        self.journey_id = part_dict['product']['number']

        # VOLGENS-PLAN, GEANNULEERD (=vervallen trein), GEWIJZIGD (=planaanpassing in de bijsturing op de dag zelf),
        # OVERSTAP-NIET-MOGELIJK, VERTRAAGD, NIEUW (=extra trein)
        self.going = True
        self.has_delay = False
        if part_dict['cancelled']:
            self.going = False
        if part_dict['punctuality'] != 100.0:
            self.has_delay = True

        self.stops = []
        raw_stops = part_dict['stops']
        for raw_stop in raw_stops:
            stop = TripStop(raw_stop)
            self.stops.append(stop)

    @property
    def destination(self):
        return self.stops[-1].name

    @property
    def departure(self):
        return self.stops[0].name

    @property
    def departure_time_planned(self):
        return self.stops[0].planned_time

    @property
    def departure_time_actual(self):
        return self.stops[0].actual_time

    @property
    def arrival_time_planned(self):
        return self.stops[-1].planned_time

    @property
    def arrival_time_actual(self):
        return self.stops[-1].actual_time

    def has_departure_delay(self, arrival_check=True):
        if not arrival_check and self.has_delay:
            # Check whether one or more stops have delay, except last one
            delay_found = False
            for stop in self.stops:
                if stop.delay and stop:
                    delay_found = True
                elif not stop.delay and stop == self.stops[-1]:
                    # Last stop and it doesn't have a delay
                    return delay_found
            return delay_found
        return self.has_delay

    def __getstate__(self):
        result = super(TripSubpart, self).__getstate__()
        stops = []
        for stop in self.stops:
            stops.append(stop.to_json())
        result['stops'] = stops
        return result

    def __setstate__(self, source_dict):
        super(TripSubpart, self).__setstate__(source_dict)
        trip_stops = []
        for raw_stop in self.stops:
            trip_stop = TripStop()
            trip_stop.from_json(raw_stop)
            trip_stops.append(trip_stop)
        self.stops = trip_stops

    def __str__(self):
        return '<TripSubpart> [{0}] {1} {2} {3}'.format(
            self.going,
            self.journey_id,
            self.trip_type,
            self.transport_type
        )


class Trip(BaseObject):
    """
    Suggested route for the provided departure/destination combination
    """

    def __init__(self, trip_dict=None, trip_datetime=None):
        if trip_dict is None:
            return
        # self.key = ??
        try:
            # VOLGENS-PLAN, GEWIJZIGD, VERTRAAGD, NIEUW, NIET-OPTIMAAL, NIET-MOGELIJK, PLAN-GEWIJZIGD
            self.status = trip_dict['status']
        except KeyError:
            self.status = None

        self.nr_transfers = trip_dict['transfers']
        try:
            self.travel_time_planned = trip_dict['plannedDurationInMinutes']
            self.going = True
        except KeyError:
            # Train has been cancelled
            self.travel_time_planned = None
            self.going = False
        # TODO: CHECK STATUS of actual canceled stuff
        if self.status == 'CANCELLED':
            # Train has been cancelled
            self.going = False
        self.travel_time_actual = trip_dict['actualDurationInMinutes']

        dt_format = "%Y-%m-%dT%H:%M:%S%z"

        self.requested_time = trip_datetime

        try:
            self.departure_time_planned = load_datetime(
                trip_dict['legs'][0]['origin']['plannedDateTime'], dt_format)
        except:
            self.departure_time_planned = None

        try:
            self.departure_time_actual = load_datetime(
                trip_dict['legs'][0]['origin']['actualDateTime'], dt_format)
        except:
            # Fall back to the planned time
            self.departure_time_actual = self.departure_time_planned

        try:
            self.arrival_time_planned = load_datetime(
                trip_dict['legs'][-1]['destination']['plannedDateTime'], dt_format)
        except:
            self.arrival_time_planned = None

        try:
            self.arrival_time_actual = load_datetime(
                trip_dict['legs'][-1]['destination']['actualDateTime'], dt_format)
        except:
            # Fall back to the planned time
            self.arrival_time_actual = self.arrival_time_planned

        try:
            self.departure_platform_planned = trip_dict['legs'][0]['origin']['plannedTrack']
        except:
            self.departure_platform_planned = None

        try:
            self.departure_platform_actual = trip_dict['legs'][0]['origin']['actualTrack']
        except:
            # Fall back to the planned platform
            self.departure_platform_actual = self.departure_platform_planned

        try:
            self.arrival_platform_planned = trip_dict['legs'][-1]['destination']['plannedTrack']
        except:
            self.arrival_platform_planned = None

        try:
            self.arrival_platform_actual = trip_dict['legs'][-1]['destination']['actualTrack']
        except:
            # Fall back to the planned platform
            self.arrival_platform_actual = self.arrival_platform_planned

        self.trip_parts = []
        raw_parts = trip_dict['legs']
        if isinstance(trip_dict['legs'], collections.OrderedDict):
            raw_parts = [trip_dict['legs']]
        for part in raw_parts:
            trip_part = TripSubpart(part)
            self.trip_parts.append(trip_part)

    @property
    def departure(self):
        return self.trip_parts[0].stops[0].name

    @property
    def destination(self):
        return self.trip_parts[-1].stops[-1].name

    @property
    def delay(self):
        """
        Return the delay of the train for this instance
        """
        delay = {'departure_time': None, 'departure_delay': None, 'requested_differs': None,
                 'parts': []}
        if self.departure_time_actual and self.departure_time_actual > self.departure_time_planned:
            delay['departure_delay'] = self.departure_time_actual - self.departure_time_planned
            delay['departure_time'] = self.departure_time_actual
        if self.requested_time != self.departure_time_actual:
            delay['requested_differs'] = self.departure_time_actual
        for part in self.trip_parts:
            if part.has_delay:
                delay['parts'].append(part)
        return delay

    def has_delay(self, arrival_check=True):
        if self.status != 'NORMAL':
            return True
        for subpart in self.trip_parts:
            if subpart['punctuality'] != 100.0:
                if subpart == self.trip_parts[-1]:
                    # Is last part of the trip, check if it is only the arrival
                    return subpart.has_departure_delay(arrival_check)
                return True
        if self.requested_time != self.departure_time_actual:
            return True
        return False

    def __getstate__(self):
        result = super(Trip, self).__getstate__()
        result['requested_time'] = result['requested_time'].isoformat()
        result['departure_time_actual'] = result['departure_time_actual'].isoformat()
        result['arrival_time_actual'] = result['arrival_time_actual'].isoformat()
        result['departure_time_planned'] = result['departure_time_planned'].isoformat()
        result['arrival_time_planned'] = result['arrival_time_planned'].isoformat()
        trip_parts = []
        for trip_part in result['trip_parts']:
            trip_parts.append(trip_part.to_json())
        result['trip_parts'] = trip_parts
        trip_remarks = []
        for trip_remark in result['trip_remarks']:
            trip_remarks.append(trip_remark.to_json())
        result['trip_remarks'] = trip_remarks
        return result

    def __setstate__(self, source_dict):
        super(Trip, self).__setstate__(source_dict)

        # TripSubpart deserialisation
        trip_parts = []
        subparts = self.trip_parts
        for part in subparts:
            subpart = TripSubpart()
            subpart.from_json(part)
            trip_parts.append(subpart)
        self.trip_parts = trip_parts
        # Datetime stamps
        self.departure_time_planned = load_datetime(
            self.departure_time_planned, NS_DATETIME)
        self.departure_time_actual = load_datetime(
            self.departure_time_actual, NS_DATETIME)
        self.arrival_time_planned = load_datetime(
            self.arrival_time_planned, NS_DATETIME)
        self.arrival_time_actual = load_datetime(
            self.arrival_time_actual, NS_DATETIME)
        self.requested_time = load_datetime(self.requested_time, NS_DATETIME)

    def delay_text(self):
        """
        If trip has delays, format a natural language summary
        """
        # TODO implement
        pass

    @classmethod
    def get_actual(cls, trip_list, trip_time):
        """
        Look for the train actually leaving at time
        """
        for trip in trip_list:
            if simple_time(trip.departure_time_planned) == trip_time:
                return trip
        return None

    @classmethod
    def get_optimal(cls, trip_list):
        """
        Look for the optimal trip in the list
        """
        for trip in trip_list:
            if trip.is_optimal:
                return trip
        return None

    def __str__(self):
        return '<Trip> {0} plan: {1} actual: {2} transfers: {3}'.format(
            self.has_delay,
            self.departure_time_planned,
            self.departure_time_actual,
            self.nr_transfers
        )


class NSAPI:
    """
    NS API object
    Library to query the official Dutch railways API
    """

    def __init__(self, subscription_key):
        self.subscription_key = subscription_key

    def _request(self, method, url, postdata=None, params=None):
        headers = {
            # Request headers
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        try:
            conn = http.client.HTTPSConnection('gateway.apiportal.ns.nl')
            conn.request(method, url, "{body}", headers)
            response = conn.getresponse()
            data = response.read().decode('UTF-8')
            conn.close()
            return data
        except Exception as e:
            print("Error during connection: {0}".format(e))

    @staticmethod
    def parse_disruptions(data):
        """
        Parse the NS API json result into Disruption objects
        @param data: raw json result from the NS API
        """
        obj = json.loads(data)
        disruptions = {}
        disruptions['unplanned'] = []
        disruptions['planned'] = []
        if obj['payload']:
            raw_disruptions = obj['payload']
            if isinstance(raw_disruptions, collections.OrderedDict):
                raw_disruptions = [raw_disruptions]
            for disruption in raw_disruptions:
                if disruption['type'] == 'storing' or disruption['type'] == 'verstoring':
                    newdis = Disruption(disruption)
                    disruptions['unplanned'].append(newdis)
                elif disruption['type'] == 'werkzaamheid':
                    newdis = Disruption(disruption)
                    disruptions['planned'].append(newdis)
        return disruptions

    def get_disruptions(self, station=None, actual=True, unplanned=True):
        """
        Fetch the current disruptions, or even the planned ones
        @param station: station to lookup
        @param actual: only actual disruption
        @param unplanned: only unplanned disruption
        """

        if station is None:
            params = urllib.parse.urlencode({
                # Request parameters
                'actual': actual,
                'lang': 'nl',
            })
            url = ("/reisinformatie-api/api/v2/disruptions?%s" % params)
        else:
            url = ("/reisinformatie-api/api/v2/disruptions/station/%s?%s" %
                   (station, params))
        raw_disruptions = self._request('GET', url)
        return self.parse_disruptions(raw_disruptions)

    @staticmethod
    def parse_departures(data):
        """
        Parse the NS API json result into Departure objects
        @param data: raw json result from the NS API
        """
        obj = json.loads(data)
        departures = []

        for departure in obj['payload']['departures']:
            newdep = Departure(departure)
            departures.append(newdep)
            print((newdep.delay))

        return departures

    def get_departures(self, station=None, for_datetime=None, max_journeys='25', uic_code=None, source=None):
        """
        Fetch the current departure times from this station
        @param station: station to lookup
        @param dateTime: Format - date-time (as date-time in RFC3339)
        @param maxJourneys: int32. number of departures or arrivals to return
        @param uicCode: specify a station by UIC code (84xxxxx)
        @param source: forces to use a certain source
        """
        params = urllib.parse.urlencode({
            # Request parameters
            'dateTime': for_datetime,
            'maxJourneys': max_journeys,
            'lang': 'nl',
            'station': station,
            'uicCode': uic_code,
            'source': source,
        })
        url = "/reisinformatie-api/api/v2/departures?%s" % params

        raw_departures = self._request('GET', url)
        return self.parse_departures(raw_departures)

    @staticmethod
    def parse_trips(data, requested_time):
        """
        Parse the NS API xml result into Trip objects
        """
        obj = json.loads(data)
        trips = []

        if 'error' in obj:
            print(('Error in trips: ' + obj['error']['message']))
            return None

        try:
            for trip in obj['trips']:
                newtrip = Trip(trip, requested_time)
                trips.append(newtrip)
        except TypeError:
            # If no options are found, obj['ReisMogelijkheden'] is None
            return None

        return trips

    def get_trips(self, timestamp, start, via, destination, departure=True, prev_advices=1, next_advices=1):
        """
        Fetch trip possibilities for these parameters
        https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips<parameters>
        @param timestamp:       departure time
        @param start:           from station
        @param via:             via station
        @param destination:     Destination station
        @param departure:       if false departure time works as requested arrival time
        @param prev_advices:    number of previous advices
        @param next_advices:    number of next advices
        """
        timezonestring = '+0100'
        if is_dst('Europe/Amsterdam'):
            timezonestring = '+0200'

        if len(timestamp) == 5:
            # Format of HH:MM - api needs yyyy-mm-ddThh:mm
            timestamp = time.strftime("%Y-%m-%d") + 'T' + timestamp
            #requested_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
            # TODO: DST/normal time
            requested_time = load_datetime(
                timestamp + timezonestring, "%Y-%m-%dT%H:%M%z")
        else:
            #requested_time = datetime.strptime(timestamp, "%d-%m-%Y %H:%M")
            requested_time = load_datetime(
                timestamp + timezonestring, "%d-%m-%Y %H:%M%z")
            timestamp = datetime.strptime(
                timestamp, "%d-%m-%Y %H:%M").strftime("%Y-%m-%dT%H:%M")

        params = urllib.parse.urlencode({
            # all possible Request parameters
            # 'originLat': '{string}',
            # 'originLng': '{string}',
            # 'destinationLat': '{string}',
            # 'destinationLng': '{string}',
            # 'viaLat': '{string}',
            # 'viaLng': '{string}',
            # 'viaWaitTime': '{integer}',
            'dateTime': timestamp,
            'searchForArrival': not departure,
            'previousAdvices': prev_advices,
            'nextAdvices': next_advices,
            # 'context': '{string}',
            # 'addChangeTime': '{integer}',
            # 'lang': '{string}',
            # 'originTransit': 'False',
            # 'originWalk': 'False',
            # 'originBike': 'False',
            # 'originCar': 'False',
            # 'originName': '{string}',
            # 'travelAssistanceTransferTime': '0',
            # 'searchForAccessibleTrip': 'False',
            # 'destinationTransit': 'False',
            # 'destinationWalk': 'False',
            # 'destinationBike': 'False',
            # 'destinationCar': 'False',
            # 'destinationName': '{string}',
            # 'accessibilityEquipment1': '{string}',
            # 'accessibilityEquipment2': '{string}',
            # 'excludeHighSpeedTrains': 'False',
            # 'excludeReservationRequired': 'False',
            'passing': 'False',
            # 'travelRequestType': '{string}',
            # 'originEVACode': '{string}',
            # 'destinationEVACode': '{string}',
            # 'viaEVACode': '{string}',
            # 'shorterChange': '{boolean}',
            'fromStation': start,
            'toStation': destination,
            # 'originUicCode': '{string}',
            # 'destinationUicCode': '{string}',
            # 'viaUicCode': '{string}',
            # 'bikeCarriageRequired': '{boolean}',
            'viaStation': via,
            'departure': departure,
            # 'minimalChangeTime': '{integer}',
        })

        url = "/reisinformatie-api/api/v3/trips?%s" % params
        raw_trips = self._request('GET', url)
        return self.parse_trips(raw_trips, requested_time)

    @staticmethod
    def parse_stations(data):
        obj = json.loads(data)
        stations = []

        for station in obj['payload']:
            newstat = Station(station)
            stations.append(newstat)

        return stations

    def get_stations(self):
        """
        Fetch the list of stations
        """
        url = "/reisinformatie-api/api/v2/stations?%s" % params
        raw_stations = self._request('GET', url)
        return self.parse_stations(raw_stations)
