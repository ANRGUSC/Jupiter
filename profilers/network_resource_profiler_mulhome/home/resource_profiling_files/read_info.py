__author__ = "Jiatong Wang, Quynh Nguyen, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import requests
import sys
import json
import time
import datetime
import os
import configparser
from os import path



def open_file():
	"""
		- Read node IP information from file. 
		- Request resource profiling info for each node
		- Append time stamp
	
	Returns:
		list: resource profiling information for all of the nodes in the node list
	"""

	INI_PATH = '/network_profiling/jupiter_config.ini'
	config = configparser.ConfigParser()
	config.read(INI_PATH)
	
	MONGO_SVC    = int(config['PORT']['MONGO_SVC'])
	MONGO_DOCKER = int(config['PORT']['MONGO_DOCKER'])
	FLASK_SVC    = int(config['PORT']['FLASK_SVC'])

	node_ip = os.environ['SELF_IP']  

	home_ips = os.environ['HOME_IP']
	home_ips = home_ips.split(':')[1:]  

	list=[]
	ip_path = sys.argv[1]

	with open(ip_path, "r") as ins:
		for line in ins:
			line = line.strip('\n')
			if line in home_ips:
				continue
			print("get the data from http://"+line+ ":" + str(FLASK_SVC))
			try:
				r = requests.get("http://"+line+":" + str(FLASK_SVC))
				result = r.json()
				result['ip']=line
				result['last_update']=datetime.datetime.utcnow().strftime('%B %d %Y - %H:%M:%S')
				data=json.dumps(result)
				list.append(data)
			except Exception as e:
				print("resource request failed. details: " + str(e))
		# print list
		return list

if __name__ == '__main__':
    open_file()