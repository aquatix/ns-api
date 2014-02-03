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
    disruptions = []

    disruptionlist = soup.find_all('ul', {'class': 'list-faqs'})
    if len(disruptionlist) > 1:
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
