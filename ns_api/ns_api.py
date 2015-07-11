"""
Library to query the official Dutch railways API
"""
import requests
from requests.auth import HTTPBasicAuth
import xmltodict
#import time

from datetime import datetime, timedelta

from pytz.tzinfo import StaticTzInfo

import json
import collections


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
        return OffsetTime(offset).localize(datetime.strptime(value, dt_format))

    return datetime.strptime(value, dt_format)

def dump_datetime(value, dt_format):
    """
    Format datetime object to string
    """
    return value.strftime(dt_format)


def list_to_json(source_list):
    """
    Serialise all the items in source_list to json
    """
    result = []
    for item in source_list:
        result.append(item.to_json())
    return result


def list_from_json(source_list):
    """
    Deserialise all the items in source_list from json
    """
    result = []
    for item in source_list:
        result.append(item.from_json())
    return result


def list_changes(list_a, list_b):
    """
    Return the items from list_b that differ from list_a
    """
    result = []
    for item in list_b:
        if not item in list_a:
            result.append(item)
    return result


class BaseObject(object):
    """
    Base object with useful functions
    """

    def __getstate__(self):
        result = self.__dict__.copy()
        return result

    def to_json(self):
        """
        Create a JSON representation of this model
        """
        return json.dumps(self.__getstate__())

    def __setstate__(self, source_dict):
        self.__dict__ = source_dict

    def from_json(self, source_json):
        """
        Parse a JSON representation of this model back to, well, the model
        """
        source_dict = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(source_json)
        self.__setstate__(source_dict)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return self.__unicode__()

    def __str__(self):
        return self.__unicode__()

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

    def __init__(self, part_dict):
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

        dt_format = "%Y-%m-%dT%H:%M:%S%z"

        try:
            self.datetime = load_datetime(part_dict['Datum'], dt_format)
        except:
            self.datetime = None

    def __unicode__(self):
        return u'<Disruption> {0}'.format(self.line)


class Departure(BaseObject):
    """
    Information on a departing train on a certain station
    """

    def __init__(self, departure_dict):
        self.key = departure_dict['RitNummer'] + '_' + departure_dict['VertrekTijd']
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

    def __init__(self, part_dict):
        self.key = part_dict['Id']
        if part_dict['Ernstig'] == 'false':
            self.is_grave = False
        else:
            self.is_grave = True
        self.text = part_dict['Text']

    def __unicode__(self):
        return u'<TripRemark> {0} {1}'.format(self.is_grave, self.text)


class TripStop(BaseObject):
    """
    Information on a stop on a route (station, time, platform)
    """

    def __init__(self, part_dict):
        #self.key =
        self.name = part_dict['Naam']
        self.time = part_dict['Tijd']
        self.platform = part_dict['Spoor']

    def __unicode__(self):
        return u'<TripStop> {0}'.format(self.name)


class TripSubpart(BaseObject):
    """
    Sub route; each part means a transfer
    """

    def __init__(self, part_dict):
        self.trip_type = part_dict['@reisSoort']
        self.transporter = part_dict['Vervoerder']
        self.transport_type = part_dict['VervoerType']
        self.journey_id = part_dict['RitNummer']
        self.status = part_dict['Status']
        if self.status == 'GEANNULEERD':
            self.going = False
        else:
            self.going = True

    def __unicode__(self):
        return u'<TripSubpart> [{0}] {1} {2} {3}'.format(self.going, self.journey_id, self.trip_type, self.status)


class Trip(BaseObject):
    """
    Suggested route for the provided departure/destination combination
    """

    def __init__(self, trip_dict):
        # self.key = ??
        self.status = trip_dict['Status']
        self.nr_transfers = trip_dict['AantalOverstappen']
        try:
            self.travel_time_planned = trip_dict['GeplandeReisTijd']
            self.going = True
        except KeyError:
            # Train has been cancelled
            self.travel_time_planned = None
            self.going = False
        self.travel_time_actual = trip_dict['ActueleReisTijd']
        self.is_optimal = True if trip_dict['Optimaal'] == 'true' else False

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
    def delay(self):
        """
        Return the delay of the train for this instance
        """
        if self.departure_time_actual > self.departure_time_planned:
            return self.departure_time_actual - self.departure_time_planned
        else:
            return None

    def __getstate__(self):
        result = self.__dict__.copy()
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
        self.__dict__ = source_dict

    def from_json(self, source_json):
        """
        Parse a JSON representation of this model back to, well, the model
        """
        # TODO implement
        # json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(source_json)
        # self.__setstate__(source_dict)
        pass

    def delay_text(self):
        """
        If trip has delays, format a natural language summary
        """
        # TODO implement
        pass

    def __unicode__(self):
        return u'<Trip> plan: {0} actual: {1} transfers: {2}'.format(self.departure_time_planned, self.departure_time_actual, self.nr_transfers)


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
        @param station: station to lookup
        """
        url = 'http://www.ns.nl/actuele-vertrektijden/main.action?xml=true'

        values = {
            'van_heen_station' : station,
        }

        raw_departures = self._request('GET', url)
        return self.parse_departures(raw_departures)


    def parse_trips(self, xml):
        """
        Parse the NS API xml result into Trip objects
        """
        obj = xmltodict.parse(xml)
        trips = []

        for trip in obj['ReisMogelijkheden']['ReisMogelijkheid']:
            newtrip = Trip(trip)
            trips.append(newtrip)
            #print('-- trip --')
            #print(newtrip)
            #print(newtrip.__dict__)
            print(newtrip.to_json())
            print(newtrip.delay)
            #print('-- /trip --')

        return trips


    def get_trips(self, starttime, start, via, destination):
        """
        Fetch trip possibilities for these parameters
        """
        # TODO implement
        pass


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

