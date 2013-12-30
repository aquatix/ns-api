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
        delay = splitted[2]
        delay_unit = splitted[3]
    return timestamp, delay, delay_unit


def _parse_da_time(time):
    """
    Parse timestamp with D or A from departure or arrival
    """
    return time.split()[1]

def vertrektijden(station):
    #url = 'http://www.ns.nl/actuele-vertrektijden/main.action?xml=false'
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
    times = []
    for row in soup.find_all('tr'):
        counter = 0
        time = ''
        delay = 0
        delay_unit = ''
        destination = ''
        platform = ''
        route = ''
        details = ''

        for cell in row.find_all('td'):
            cell_content = cell.get_text().strip()
            if counter == 0:
                time, delay, delay_unit = _parse_time_delay(cell_content)
            if counter == 1:
                destination = cell_content
            if counter == 2:
                platform = cell_content
            if counter == 3:
                route = cell_content
            if counter == 4:
                details = cell_content
            counter += 1

        if time != '':
            time_tuple = {'time': time, 'delay': delay, 'delay_unit': delay_unit, 'destination': destination, 'platform': platform, 'route': route, 'details': details}
            times.append(time_tuple)

    return times


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
    #req = urllib2.Request(url+data, None, header)
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
                    #print part
                    counter = 0
                    for cell in part.find_all('td'):
                        #print "%s %d %d %d" % (cell, partcounter, rowcounter, counter)
                        if rowcounter == 0 and counter == 0:
                            route_parts[partcounter]['departure'] = _parse_da_time(cell.b.get_text().strip())
                        if rowcounter == 0 and counter == 1:
                            try:
                                #print cell.b.font.get_text().strip()
                                print "depdelay %s" % cell.b.font
                                print cell.b('font')
                                print "depdelay %s" % cell('font')
                                print "depdelay %s" % cell.b.font.Contents()
                                route_parts[partcounter]['departure_delay'] = cell.b.font
                            except:
                                pass
                            route_parts[partcounter]['departure_platform'] = cell.b.get_text().strip()
                        if rowcounter == 1 and counter == 0:
                            route_parts[partcounter]['train'] = cell.get_text()
                        if rowcounter == 2 and counter == 0:
                            route_parts[partcounter]['arrival'] = _parse_da_time(cell.b.get_text().strip())
                        if rowcounter == 2 and counter == 1:
                            try:
                                #print cell.b.font.get_text().strip()
                                print "arrdelay %s" % cell.b.font
                                route_parts[partcounter]['arrival_delay'] = cell.b.font
                            except:
                                pass
                            route_parts[partcounter]['arrival_platform'] = cell.b.get_text().strip()
                        counter += 1
                    rowcounter += 1
                    if rowcounter == 4:
                        rowcounter = 0
                        partcounter += 1
                        route_parts.append({})
        except KeyError:
            continue

    return route_parts


def check_delays_at(station):
    times = vertrektijden(station)
    for time in times:
        if time['delay'] > 0:
            print time

print vertrektijden('Amsterdam Centraal')
#print check_delays_at('Amsterdam Centraal')
#print werkzaamheden()
#print route('heemskerk', 'hoofddorp', '', '30-12', '13:34')
print route('amsterdam centraal', 'hoofddorp', '', '30-12', '14:34')
#for routeparts in route('heemskerk', 'hoofddorp', '', '30-12', '13:34'):
#    print u"departing from {0} at {1}".format(routeparts['departure_platform'], routeparts['departure'])
