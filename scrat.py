import ns_api
import datetime
disruption = ns_api.Disruption

nsapi = ns_api.NSAPI("34740ea251b94791a2171fd421a86eb0")
# test = nsapi.get_disruptions()
# print(test)
# test2 = nsapi.get_stations()
# print(test2)
# test3 = nsapi.get_departures('UT')
# print(test3)
test = nsapi.get_trips('20:00', 'Maastricht', '', 'Groningen')
print(test)