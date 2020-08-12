import sys
import json

def load_names(filename):
	name_file = open(filename, 'r')
	namejson = json.loads(name_file.read())
	name_file.close()
	return namejson

def get_steamid(name_json, name):
	if name in name_json:
		return name_json[name]
	
	return 'None'

def get_name(name_json, steamid):
	for name in name_json:
		if name_json[name] == steamid:
			return name
	
	return steamid