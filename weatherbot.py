#!/bin/python

#Author - Hans Gogia
#Date - 28/07/2016

import requests
from slackclient import SlackClient
import time
import json
import sys
import re
import weatherbot_conf

slack_client = SlackClient(BOT_TOKEN)

def city_id(city):
	with open('city.list.json') as f:
		try:
			for line in f:
				if json.loads(line)['name'].lower() == city.encode('utf-8'):
					return json.loads(line)['_id']
		except e:
			return e
	return None


def announcement(c_id):
	res = ''
	weather = ''
	r = requests.get('http://api.openweathermap.org/data/2.5/weather?id='+ str(c_id) +'&APPID='+ API_KEY)
	res = r.json()
	if 'weather' in res:
		weather = res['weather'][0]['main']
		if weather and weather == WEATHER_CONDITION:
			return WORK_FROM_HOME_MSG
		else:
			return WORKING_MSG
	return "City Name incorrect"


def handle_command(command, channel):
	cityID = '0'
	response = "Not sure what you mean. Use the *" + INIT_COMMAND + "* command with City Name, delimited by spaces."
	if command.startswith(INIT_COMMAND):
		city_name = command.split(INIT_COMMAND)
		if city_name[1] == 'configure':
			slack_client.api_call("chat.postMessage",channel=channel,text="Enter the city, channel and time(24 hours) for daily alerts in the following syntax: <cityname>, <channel>, <time>", as_user=True)
		else:
			cityID = city_id(city_name[1])
			response = announcement(cityID)
			slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
	else:
		response = configure(command, channel)
		slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
	output_list = slack_rtm_output
	print output_list
	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and output['channel'] == BOT_DM and output['user'] != BOT_ID:
				if AT_BOT in output['text']:
					return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']
				else:
					return output['text'], output['channel']
			elif output and 'text' in output and AT_BOT in output['text']:
				return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']
	return None,None


def configure(command, channel):
	city_channel = command.split(',')
	with open('weatherbot.conf', 'a') as conf_file:
		try:
			content = '{' + '"city_name" : "' + city_channel[0] + '", "channel" : "' + city_channel[1] + '", "time" : ' + city_channel[2] + '},'
			conf_file.write(content)
			return "File saved!"
		except:
			e = sys.exc_info()[0]
			print e
			return "File could not opened."


def daily_alerts():
	with open('weatherbot.conf') as conf_file:
		try:
			content = conf_file.read()
			content = content[:-1].strip()
			dict_list = re.findall('(\{.*?\})', content)
			dict_list = [json.loads(i) for i in dict_list]
			for i in dict_list:
				slack_client.api_call("chat.postMessage",channel='G0HT3FF7X',text=AT_BOT + " /" + i['city_name'], as_user=True)
		except:
			e = sys.exc_info()[0]
                        print e
			print "File not found."


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 1 
	if slack_client.rtm_connect():
		print "weatherbot connected and running!"
		while True:
			if time.strftime("%H%M%S") == "073000":
				daily_alerts()
			command, channel = parse_slack_output(slack_client.rtm_read())
			if command and channel:
				handle_command(command, channel)
			time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print "Connection failed. Invalid Slack token or bot ID?"
