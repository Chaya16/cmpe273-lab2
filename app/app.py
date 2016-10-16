#!/usr/bin/env python

import logging
import time, collections, re, string
from spyne import Application, srpc, ServiceBase, Iterable, UnsignedInteger, String, Unicode
from spyne.protocol.json import JsonDocument
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication

logger = logging.getLogger(__name__)


import requests
import datetime
import json

dictCrimeTimeHelper = {}
dictCrimeTimeHelper[0] = "12:01am-3am"
dictCrimeTimeHelper[1] = "3:01am-6am"
dictCrimeTimeHelper[2] = "6:01am-9am"
dictCrimeTimeHelper[3] = "9:01am-12noon"
dictCrimeTimeHelper[4] = "12:01pm-3pm"
dictCrimeTimeHelper[5] = "3:01pm-6pm"
dictCrimeTimeHelper[6] = "6:01pm-9pm"
dictCrimeTimeHelper[7] = "9:01pm-12midnight"

def dictCrimeTimeInit():
	d = {}
	for key in dictCrimeTimeHelper:
		d[dictCrimeTimeHelper[key]] = 0
	return d

class CrimeAPIService(ServiceBase):
	@srpc(float, float, float, float, _returns=Iterable(Unicode))
	def checkcrime(lat, lon, radius, key):
		output_dict = {}
		payload={'lat':lat,'lon':lon, 'radius':radius, 'key':'.'}
       		r=requests.get('https://api.spotcrime.com/crimes.json',params=payload) 
       		crime_data=r.json()
       		#yield crime_data

       		dict_crimetype = {}
       		dictCrimeTime = dictCrimeTimeInit()
		streetList =[]
       		for crime in (crime_data["crimes"]):
			
			# get crime type
	       		if (crime["type"]) not in dict_crimetype:
				dict_crimetype[crime["type"]] = 1
	       		else:
		       		dict_crimetype[crime["type"]] += 1
			
			# get crime time
			tme = time.strptime(crime["date"], "%m/%d/%y %I:%M %p")
			t = tme.tm_hour*60 + tme.tm_min
			if t == 0:
				t = 24*60
			t = t - 1
			i = t//(3*60)
			dictCrimeTime[dictCrimeTimeHelper[i]] += 1

			# get crime street
			#yield crime["address"]
			st = re.sub(r'\d+ BLOCK OF ',"", crime["address"] ) 
			st = re.sub(r'\d+ BLOCK ',"", st)
			st = re.sub(r'^\d+ ',"", st)
			for street in re.split(r' & | AND | and | And ', st):
				streetList.append(string.rstrip(string.lstrip(street)))

		#yield dict_crimetype
		output_dict["total_crime"] = len(crime_data["crimes"])
		output_dict["crime_type_count"] = dict_crimetype
		output_dict["event_time_count"] = dictCrimeTime
		
		# set up top 3 streets
		cnt = collections.Counter(streetList).most_common(3)
		top3 = []
		for entry in cnt:
			top3.append(entry[0])

		output_dict["the_most_dangerous_streets"] = top3
		#yield cnt

		yield output_dict

application = Application([CrimeAPIService],
		tns='spyne.examples.hello',
		in_protocol=HttpRpc(validator='soft'),
		out_protocol=JsonDocument()
		)

if __name__ == '__main__':
	# You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    from wsgiref.simple_server import make_server
    wsgi_app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()
