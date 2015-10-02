"""
Library to query the official Dutch railways API
"""
import requests
from requests.auth import HTTPBasicAuth
import xmltodict
#import time

from datetime import datetime, timedelta

from pytz.tzinfo import StaticTzInfo
import time

import json
import collections


## ns-api library version
__version__ = '2.3'


## Date/time helpers
NS_DATETIME = "%Y-%m-%dT%H:%M:%S%z"

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


def dump_datetime(value, dt_format):
    """
    Format datetime object to string
    """
    return value.strftime(dt_format)


def simple_time(value):
    """
    Format a datetime or timedelta object to a string of format HH:MM
    """
    if isinstance(value, timedelta):
        return ':'.join(str(value).split(':')[:2])
    return dump_datetime(value, '%H:%M')


## List helpers

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
    if source_list_json == [] or source_list_json == None:
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
                print('Unrecognised Class ' + item['class_name'] + ', skipping')
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
        if not item in list_a:
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
    #return list(collections.OrderedDict.fromkeys(list_a + list_b))
    #result = list(list_b)
    result = []
    for item in list_a:
        if not item in result:
            result.append(item)
    for item in list_b:
        if not item in result:
            result.append(item)
    return result


## NS API objects

class BaseObject(object):
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
        #return json.dumps(self.__getstate__())
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
        #source_dict = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(source_json)
        source_dict = json.JSONDecoder().decode(source_json)
        self.__setstate__(source_dict)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        raise NotImplementedError('subclasses must override __unicode__()')


class Station(BaseObject):
    """
    Information on a railway station
    """

    def __init__(self, stat_dict=None):
        if stat_dict is None:
            return
        self.key = stat_dict['Code']
        self.code = stat_dict['Code']
        self.uic_code = stat_dict['UICCode']
        self.stationtype = stat_dict['Type']
        self.names = {
            'short': stat_dict['Namen']['Kort'],
            'middle': stat_dict['Namen']['Middel'],
            'long': stat_dict['Namen']['Lang']
        }
        self.country = stat_dict['Land']
        self.lat = stat_dict['Lat']
        self.lon = stat_dict['Lon']
        self.synonyms = []
        try:
            raw_synonyms = stat_dict['Synoniemen']['Synoniem']
            if isinstance(raw_synonyms, unicode):
                raw_synonyms = [raw_synonyms]
            for synonym in raw_synonyms:
                self.synonyms.append(synonym)
        except TypeError:
            self.synonyms = []

    def __unicode__(self):
        return u'<Station> {0} {1}'.format(self.code, self.names['long'])


class Disruption(BaseObject):
    """
    Planned and unplanned disruptions of the railroad traffic
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.key = part_dict['id']
        self.line = part_dict['Traject']
        self.message = part_dict['Bericht']

        try:
            self.reason = part_dict['Reden']
        except KeyError:
            self.reason = None

        try:
            self.cause = part_dict['Oorzaak']
        except KeyError:
            self.cause = None

        try:
            self.delay_text = part_dict['Vertraging']
        except KeyError:
            self.delay_text = None

        try:
            self.timestamp = load_datetime(part_dict['Datum'], NS_DATETIME)
        except:
            self.timestamp = None

    def __getstate__(self):
        result = super(Disruption, self).__getstate__()
        result['timestamp'] = result['timestamp'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(Disruption, self).__setstate__(source_dict)
        self.timestamp = load_datetime(self.timestamp, NS_DATETIME)

    def __unicode__(self):
        return u'<Disruption> {0}'.format(self.line)
        return u'<Disruption> {0}'.format(self.key)


class Departure(BaseObject):
    """
    Information on a departing train on a certain station
    """

    def __init__(self, departure_dict=None):
        if departure_dict is None:
            return
        self.key = departure_dict['RitNummer'] + '_' + departure_dict['VertrekTijd']
        self.trip_number = departure_dict['RitNummer']
        self.departure_time = load_datetime(departure_dict['VertrekTijd'], NS_DATETIME)
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

    def __getstate__(self):
        result = super(Departure, self).__getstate__()
        result['departure_time'] = result['departure_time'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(Departure, self).__setstate__(source_dict)
        self.departure_time = load_datetime(departure_dict['VertrekTijd'], NS_DATETIME)

    @property
    def delay(self):
        """
        Return the delay of the train for this instance
        """
        if self.has_delay:
            return self.departure_delay
        else:
            return None

    def __unicode__(self):
        return u'<Departure> trip_number: {0} {1} {2}'.format(self.trip_number, self.destination, self.departure_time)


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

    def __unicode__(self):
        return u'<TripRemark> {0} {1}'.format(self.is_grave, self.message)


class TripStop(BaseObject):
    """
    Information on a stop on a route (station, time, platform)
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.name = part_dict['Naam']
        self.time = load_datetime(part_dict['Tijd'], NS_DATETIME)
        self.key = simple_time(self.time) + '_' + self.name
        self.platform_changed = False
        try:
            self.platform = part_dict['Spoor']['#text']
            if part_dict['Spoor']['@wijziging'] == 'true':
                self.platform_changed = True
        except KeyError:
            self.platform = None
        try:
            self.delay = part_dict['VertrekVertraging']
        except KeyError:
            self.delay = None

    def __getstate__(self):
        result = super(TripStop, self).__getstate__()
        result['time'] = result['time'].isoformat()
        return result

    def __setstate__(self, source_dict):
        super(TripStop, self).__setstate__(source_dict)
        self.time = load_datetime(self.time, NS_DATETIME)

    def __unicode__(self):
        return u'<TripStop> {0}'.format(self.name)


class TripSubpart(BaseObject):
    """
    Sub route; each part means a transfer
    """

    def __init__(self, part_dict=None):
        if part_dict is None:
            return
        self.trip_type = part_dict['@reisSoort']
        self.transporter = part_dict['Vervoerder']
        self.transport_type = part_dict['VervoerType']
        self.journey_id = part_dict['RitNummer']

        # VOLGENS-PLAN, GEANNULEERD (=vervallen trein), GEWIJZIGD (=planaanpassing in de bijsturing op de dag zelf),
        # OVERSTAP-NIET-MOGELIJK, VERTRAAGD, NIEUW (=extra trein)
        self.status = part_dict['Status']
        self.going = True
        self.has_delay = False
        if self.status == 'GEANNULEERD':
            self.going = False
        if self.status == 'GEANNULEERD' or self.status == 'GEWIJZIGD' or self.status == 'VERTRAAGD':
            self.has_delay = True

        try:
            self.disruption_key = part_dict['OngeplandeStoringId']
        except KeyError:
            self.disruption_key = None


        self.stops = []
        raw_stops = part_dict['ReisStop']
        for raw_stop in raw_stops:
            stop = TripStop(raw_stop)
            self.stops.append(stop)

    @property
    def destination(self):
        return self.stops[-1].name

    @property
    def departure_time(self):
        return self.stops[0].time


    def has_departure_delay(self, arrival_check=True):
        if arrival_check==False and self.has_delay:
            # Check whether one or more stops have delay, except last one
            delay_found = False
            for stop in self.stops:
                if stop.delay and stop:
                    delay_found = True
                elif stop.delay == False and stop == self.stops[-1]:
                    # Last stop and it doesn't have a delay
                    return delay_found
        else:
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

    def __unicode__(self):
        return u'<TripSubpart> [{0}] {1} {2} {3} {4}'.format(self.going, self.journey_id, self.trip_type, self.transport_type, self.status)


class Trip(BaseObject):
    """
    Suggested route for the provided departure/destination combination
    """

    def __init__(self, trip_dict=None, datetime=None):
        if trip_dict is None:
            return
        # self.key = ??

        try:
            # VOLGENS-PLAN, GEWIJZIGD, VERTRAAGD, NIEUW, NIET-OPTIMAAL, NIET-MOGELIJK, PLAN-GEWIJZIGD
            self.status = trip_dict['Status']
        except KeyError:
            self.status = None

        self.nr_transfers = trip_dict['AantalOverstappen']
        try:
            self.travel_time_planned = trip_dict['GeplandeReisTijd']
            self.going = True
        except KeyError:
            # Train has been cancelled
            self.travel_time_planned = None
            self.going = False
        if self.status == 'NIET-MOGELIJK':
            # Train has been cancelled
            self.going = False
        self.travel_time_actual = trip_dict['ActueleReisTijd']
        self.is_optimal = True if trip_dict['Optimaal'] == 'true' else False

        dt_format = "%Y-%m-%dT%H:%M:%S%z"

        self.requested_time = datetime

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


        self.trip_parts = []
        raw_parts = trip_dict['ReisDeel']
        if isinstance(trip_dict['ReisDeel'], collections.OrderedDict):
            raw_parts = [trip_dict['ReisDeel']]
        for part in raw_parts:
            trip_part = TripSubpart(part)
            self.trip_parts.append(trip_part)

        try:
            raw_remarks = trip_dict['Melding']
            self.trip_remarks = []
            if isinstance(raw_remarks, collections.OrderedDict):
                raw_remarks = [raw_remarks]
            for remark in raw_remarks:
                trip_remark = TripRemark(remark)
                self.trip_remarks.append(trip_remark)
        except KeyError:
            self.trip_remarks = []


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
                'remarks': self.trip_remarks, 'parts': []}
        if self.departure_time_actual > self.departure_time_planned:
            delay['departure_delay'] = self.departure_time_actual - self.departure_time_planned
            delay['departure_time'] = self.departure_time_actual
        if self.requested_time != self.departure_time_actual:
            delay['requested_differs'] = self.departure_time_actual
        for part in self.trip_parts:
            if part.has_delay:
                delay['parts'].append(part)
        return delay

    def has_delay(self, arrival_check=True):
        if self.status != 'VOLGENS-PLAN':
            return True
        for subpart in self.trip_parts:
            if subpart.has_delay:
                if subpart == self.trip_parts[-1]:
                    # Is last part of the trip, check if it is only the arrival
                    return subpart.has_departure_delay(arrival_check)
                return True
        if self.requested_time != self.departure_time_actual:
            return True
        return False

    def has_departure_delay(self, subpartcheck=True):
        """
        Deprecated
        """
        if self.status != 'VOLGENS-PLAN':
            return True
        if subpartcheck and self.trip_parts[0].has_delay:
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
        # TripRemark deserialisation
        trip_remarks = []
        remarks = self.trip_remarks
        for raw_remark in remarks:
            remark = TripRemark()
            remark.from_json(raw_remark)
            trip_remarks.append(remark)
        self.trip_remarks = trip_remarks
        # Datetime stamps
        self.departure_time_planned = load_datetime(self.departure_time_planned, NS_DATETIME)
        self.departure_time_actual = load_datetime(self.departure_time_actual, NS_DATETIME)
        self.arrival_time_planned = load_datetime(self.arrival_time_planned, NS_DATETIME)
        self.arrival_time_actual = load_datetime(self.arrival_time_actual, NS_DATETIME)
        self.requested_time = load_datetime(self.requested_time, NS_DATETIME)


    def delay_text(self):
        """
        If trip has delays, format a natural language summary
        """
        # TODO implement
        pass


    @classmethod
    def get_actual(cls, trip_list, time):
        """
        Look for the train actually leaving at time
        """
        for trip in trip_list:
            if simple_time(trip.departure_time_planned) == time:
                return trip
        return None


    @classmethod
    def get_optimal(cls, trip_list, time):
        """
        Look for the optimal trip in the list
        """
        for trip in trip_list:
            if trip.is_optimal:
                return trip
        return None

    def __unicode__(self):
        return u'<Trip> {0} plan: {1} actual: {2} transfers: {3}'.format(self.has_delay, self.departure_time_planned, self.departure_time_actual, self.nr_transfers)


class NSAPI(object):
    """
    NS API object
    Library to query the official Dutch railways API
    """

    def __init__(self, username, apikey):
        self.username = username
        self.apikey = apikey

    def _request(self, method, url, postdata=None, params=None):
        headers = {"Accept": "application/xml",
                   "Content-Type": "application/xml",
                   "User-Agent": "ns_api"}

        if postdata:
            postdata = json.dumps(postdata)

        r = requests.request(method,
                             url,
                             data=postdata,
                             params=params,
                             headers=headers,
                             files=None,
                             auth=HTTPBasicAuth(self.username, self.apikey))

        r.raise_for_status()
        return r.text


    def parse_disruptions(self, xml):
        """
        Parse the NS API xml result into Disruption objects
        @param xml: raw XML result from the NS API
        """
        obj = xmltodict.parse(xml)
        disruptions = {}
        disruptions['unplanned'] = []
        disruptions['planned'] = []

        if obj['Storingen']['Ongepland']:
            raw_disruptions = obj['Storingen']['Ongepland']['Storing']
            if isinstance(raw_disruptions, collections.OrderedDict):
                raw_disruptions = [raw_disruptions]
            for disruption in raw_disruptions:
                newdis = Disruption(disruption)
                #print(newdis.__dict__)
                disruptions['unplanned'].append(newdis)

        if obj['Storingen']['Gepland']:
            raw_disruptions = obj['Storingen']['Gepland']['Storing']
            if isinstance(raw_disruptions, collections.OrderedDict):
                raw_disruptions = [raw_disruptions]
            for disruption in raw_disruptions:
                newdis = Disruption(disruption)
                #print(newdis.__dict__)
                disruptions['planned'].append(newdis)
        return disruptions


    def get_disruptions(self, station=None, actual=True, unplanned=True):
        """
        Fetch the current disruptions, or even the planned ones
        @param station: station to lookup
        @param actual: only actual disruptions, or a

        actuele storingen  (=ongeplande storingen + actuele werkzaamheden)
        geplande werkzaamheden (=geplande werkzaamheden)
        actuele storingen voor een gespecificeerd station (=ongeplande storingen + actuele werkzaamheden)
        """
        url = "http://webservices.ns.nl/ns-api-storingen?station=${Stationsnaam}&actual=${true or false}&unplanned=${true or false}"
        url = "http://webservices.ns.nl/ns-api-storingen?actual=true&unplanned=true"

        raw_disruptions = self._request('GET', url)
        return self.parse_disruptions(raw_disruptions)


    def parse_departures(self, xml):
        """
        Parse the NS API xml result into Departure objects
        @param xml: raw XML result from the NS API
        """
        obj = xmltodict.parse(xml)
        departures = []

        for departure in obj['ActueleVertrekTijden']['VertrekkendeTrein']:
            newdep = Departure(departure)
            departures.append(newdep)
            #print('-- dep --')
            #print(newdep.__dict__)
            #print(newdep.to_json())
            print(newdep.delay)

        return departures


    def get_departures(self, station):
        """
        Fetch the current departure times from this station
        http://webservices.ns.nl/ns-api-avt?station=${Naam of afkorting Station}
        @param station: station to lookup
        """
        url = 'http://webservices.ns.nl/ns-api-avt?station=' + station

        raw_departures = self._request('GET', url)
        return self.parse_departures(raw_departures)


    def parse_trips(self, xml, requested_time):
        """
        Parse the NS API xml result into Trip objects
        """
        obj = xmltodict.parse(xml)
        trips = []

        if 'error' in obj:
            print 'Error in trips: ' + obj['error']['message']
            return None

        for trip in obj['ReisMogelijkheden']['ReisMogelijkheid']:
            newtrip = Trip(trip, requested_time)
            trips.append(newtrip)
            #print('-- trip --')
            #print(newtrip)
            #print(newtrip.__dict__)
            #print(newtrip.to_json())
            #print(newtrip.delay)
            #print('-- /trip --')

        return trips


    def get_trips(self, timestamp, start, via, destination, departure=True, prev_advices=1, next_advices=1):
        """
        Fetch trip possibilities for these parameters
        http://webservices.ns.nl/ns-api-treinplanner?<parameters>
        fromStation
        toStation
        dateTime: 2012-02-21T15:50
        departure: true for starting at timestamp, false for arriving at timestamp
        previousAdvices
        nextAdvices
        """
        url = 'http://webservices.ns.nl/ns-api-treinplanner?'
        url = url + 'fromStation=' + start
        url = url + '&toStation=' + destination
        if via:
            url = url + '&via=' + via
        if len(timestamp) == 5:
            # Format of HH:MM - api needs yyyy-mm-ddThh:mm
            timestamp = time.strftime("%Y-%m-%d") + 'T' + timestamp
            #requested_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
            # TODO: DST/normal time
            requested_time = load_datetime(timestamp + '+0200', "%Y-%m-%dT%H:%M%z")
        else:
            #requested_time = datetime.strptime(timestamp, "%d-%m-%Y %H:%M")
            requested_time = load_datetime(timestamp + '+0200', "%d-%m-%Y %H:%M%z")
            timestamp = datetime.strptime(timestamp, "%d-%m-%Y %H:%M").strftime("%Y-%m-%dT%H:%M")
        url = url + '&previousAdvices=' + str(prev_advices)
        url = url + '&nextAdvices=' + str(next_advices)
        url = url + '&dateTime=' + timestamp
        raw_trips = self._request('GET', url)
        return self.parse_trips(raw_trips, requested_time)


    def parse_stations(self, xml):
        obj = xmltodict.parse(xml)
        stations = []

        for station in obj['Stations']['Station']:
            newstat = Station(station)
            stations.append(newstat)

        print len(stations)
        return stations


    def get_stations(self):
        """
        Fetch the list of stations
        """
        url = 'http://webservices.ns.nl/ns-api-stations-v2'
        raw_stations = self._request('GET', url)
        return self.parse_stations(raw_stations)

