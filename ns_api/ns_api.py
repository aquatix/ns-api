import xmltodict
import time

from datetime import datetime, timedelta

from pytz import timezone, utc
from pytz.tzinfo import StaticTzInfo

class OffsetTime(StaticTzInfo):
    def __init__(self, offset):
        """A dumb timezone based on offset such as +0530, -0600, etc.
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


class TripSubpart():

    def __init__(self, part_dict):
        transporter = part_dict['Vervoerder']


class Trip():

    def __init__(self, trip_dict):
        nr_transfers = trip_dict['AantalOverstappen']
        travel_time_planned = trip_dict['GeplandeReisTijd']
        travel_time_actual = trip_dict['ActueleReisTijd']
        is_optimal = trip_dict['Optimaal']
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



import urllib2
import urllib
from bs4 import BeautifulSoup

def _parse_time_delay(time):
    """
    Parse timestamp into time and delay
    """
    splitted = time.split()
    timestamp = splitted[0]
    delay = 0
    delay_unit = ''
    if len(splitted) > 1:
        delay = int(splitted[2])
        delay_unit = splitted[3]
    return timestamp, delay, delay_unit


def _parse_routetime_delay(time):
    """
    Parse timestamp into time and delay
    Timestamp has form '+ 3 min' or just an integer
    """
    if isinstance( time, ( int, long ) ):
        return time, None
    splitted = time.split()
    timestamp = splitted[0]
    delay = 0
    delay_unit = ''
    if len(splitted) > 1:
        delay = int(splitted[1])
        delay_unit = splitted[2]
    return delay, delay_unit


def _parse_da_time(time):
    """
    Parse timestamp with D or A from departure or arrival
    """
    return time.split()[1]


def vertrektijden(station):
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

    disruptionlist = soup.find_all('ul', {'class': 'list-faqs'})
    if len(disruptionlist) > 0:
        for row in disruptionlist[0].find_all('li'):
            try:
                if 'drawer-item' in row['class']:
                    disruptions.append({'route': row.strong.get_text(), 'info': row.p.get_text()})
            except KeyError:
                continue

    times = []
    for row in soup.find_all('tr'):
        counter = 0
        time_tuple = {}

        for cell in row.find_all('td'):
            cell_content = cell.get_text().strip()
            if counter == 0:
                time_tuple['time'], time_tuple['delay'], time_tuple['delay_unit'] = _parse_time_delay(cell_content)
            if counter == 1:
                time_tuple['destination'] = cell_content
            if counter == 2:
                time_tuple['platform'] = cell_content
            if counter == 3:
                time_tuple['route'] = cell_content
            if counter == 4:
                time_tuple['details'] = cell_content
            counter += 1

        if 'time' in time_tuple:
            times.append(time_tuple)

    return disruptions, times


def werkzaamheden():
    url = 'http://www.ns.nl/werktrajecten/'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header = { 'User-Agent' : user_agent }

    req = urllib2.Request(url, None, header)
    response = urllib2.urlopen(req)
    page = response.read()
    soup = BeautifulSoup(page)
    routes = []

    for row in soup.find_all('li'):
        try:
            if 'rounded' in row['class']:
                routes.append({'route': row.strong.get_text(), 'info': row.p.get_text()})
        except KeyError:
            continue

    return routes


def route(depart_station, to_station, via, date, time):
    url = 'http://m.ns.nl/planner.action'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    header = { 'User-Agent' : user_agent }

    values = {
        'from': depart_station,
        'to': to_station,
        'via': via,
        'time': time,   # hh:mm
        'date': date,    # dd-mm
        'departure': 'true',
        'planroute': 'Journey advice',
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data, header)
    response = urllib2.urlopen(req)
    page = response.read()
    soup = BeautifulSoup(page)

    route_parts = []
    route_parts.append({})

    tables = soup.find_all('table')
    for table in tables:
        try:
            #print table['class']
            if 'travelAdvice' in table['class']:
                partcounter = 0
                rowcounter = 0
                for part in table.find_all('tr'):
                    counter = 0
                    for cell in part.find_all('td'):
                        if rowcounter == 0 and counter == 0:
                            route_parts[partcounter]['departure'] = _parse_da_time(cell.b.get_text().strip())
                        if rowcounter == 0 and counter == 1:
                            if 'departure' not in route_parts[partcounter]:
                                route_parts[partcounter]['departure'] = 'unknown'
                            departure_mutation = ''
                            try:
                                departure_mutation = cell.b.font.get_text().replace(u'\xa0', u' ')
                            except AttributeError:
                                departure_mutation = '0'
                            route_parts[partcounter]['departure_platform'] = cell.b.get_text().replace(u'\xa0', u' ').strip()
                            route_parts[partcounter]['departure_delay'] = 0
                            if 'min' in departure_mutation:
                                route_parts[partcounter]['departure_delay'] = departure_mutation
                            elif departure_mutation != '0':
                                # platform is different from the planned one
                                route_parts[partcounter]['departure_platform_mutation'] = True
                            if route_parts[partcounter]['departure_delay'] != 0 and route_parts[partcounter]['departure_delay'] != '' and len(route_parts[partcounter]['departure_delay']) > 2:
                                # Strip the delay text, like '+ 4 min' from the platform text
                                route_parts[partcounter]['departure_platform'] = route_parts[partcounter]['departure_platform'][len(route_parts[partcounter]['departure_delay']):].strip()
                        if rowcounter == 1 and counter == 0:
                            route_parts[partcounter]['train'] = cell.get_text().replace(u'\xa0', u' ')
                        if rowcounter == 2 and counter == 0:
                            route_parts[partcounter]['arrival'] = _parse_da_time(cell.b.get_text().strip())
                        if rowcounter == 2 and counter == 1:
                            arrival_mutation = ''
                            try:
                                arrival_mutation = cell.b.font.get_text().replace(u'\xa0', u' ')
                            except AttributeError:
                                arrival_mutation = '0'
                            route_parts[partcounter]['arrival_platform'] = cell.b.get_text().replace(u'\xa0', u' ').strip()
                            route_parts[partcounter]['arrival_delay'] = 0
                            if 'min' in arrival_mutation:
                                route_parts[partcounter]['arrival_delay'] = arrival_mutation
                            elif arrival_mutation != '0':
                                # platform is different from the planned one
                                route_parts[partcounter]['arrival_platform_mutation'] = True
                            if route_parts[partcounter]['arrival_delay'] != 0 and route_parts[partcounter]['arrival_delay'] != '' and len(route_parts[partcounter]['arrival_delay']) > 2:
                                # Strip the delay text, like '+ 4 min' from the platform text
                                route_parts[partcounter]['arrival_platform'] = route_parts[partcounter]['arrival_platform'][len(route_parts[partcounter]['arrival_delay']):].strip()
                        counter += 1
                    rowcounter += 1
                    if rowcounter == 4:
                        if 'departure_delay' not in route_parts[partcounter]:
                            route_parts[partcounter]['departure_delay'] = 0
                        route_parts[partcounter]['departure_delay'], delayunit = _parse_routetime_delay(route_parts[partcounter]['departure_delay'])
                        route_parts[partcounter]['arrival_delay'], arrivalunit = _parse_routetime_delay(route_parts[partcounter]['arrival_delay'])
                        rowcounter = 0
                        partcounter += 1
                        route_parts.append({})
        except KeyError:
            continue

    return route_parts


def check_delays_at(station):
    disruptions, times = vertrektijden(station)
    for time in times:
        if time['delay'] > 0:
            print time
