import urllib2
import urllib
from bs4 import BeautifulSoup

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
        destination = ''
        platform = ''
        route = ''
        details = ''

        for cell in row.find_all('td'):
            cell_content = cell.get_text().strip()
            if counter == 0:
                time = cell_content
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
            time_tuple = {'time': time, 'destination': destination, 'platform': platform, 'route': route, 'details': details}
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

print vertrektijden('Amsterdam Centraal')
print werkzaamheden()
