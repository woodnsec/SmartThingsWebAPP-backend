# @Author: Matthew Hale <matthale>
# @Date:   2018-02-28T00:25:25-06:00
# @Email:  mlhale@unomaha.edu
# @Filename: controllers.py
# @Last modified by:   matthale
# @Last modified time: 2018-03-02T04:06:42-06:00
# @Copyright: Copyright (C) 2018 Matthew L. Hale


# Handy Django Functions
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout

# Models and serializers
from django.contrib.auth.models import User
import api.models as api

# REST API Libraries
from rest_framework import viewsets, parsers, renderers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import list_route
from rest_framework.authentication import *
#email
from templated_email import send_templated_mail
# filters
# from filters.mixins import *
from api.pagination import *
from django.core import serializers
from django.core.exceptions import ValidationError
import json, pytz, time
from datetime import datetime
import requests
# bleach for input sanitizing input
import bleach
# re for regex
import re
# os for environment variables
import os

from api.pagination import *
from django.core import serializers
from django.core.validators import validate_email, validate_image_file_extension

def home(request):
	"""
	Send requests to '/' to the ember.js clientside app
	"""

	return render(request, 'index.html')


# weather api stuff definitions here
zipcode = "zip=68116"

# cron schedules - not needed at this time.
fiveMin = {"name":"schedule-interval-5-minutes", "'cron'": {"expression": "0/5 * * * ? *", "timezone":"CST"}}
tenMin = {"name":"schedule-interval-10-minutes", "'cron'": {"expression": "0/10 * * * ? *", "timezone":"CST"}}
fifteenMin = {"name":"schedule-interval-15-minutes", "'cron'": {"expression": "0/15 * * * ? *", "timezone":"CST"}}
# need to have a local file for storage that is ignored by github
with open("./api/tokenWeather.txt", "r") as f:
	weatherApiKey = f.read().rstrip()

APPID = "APPID=" + weatherApiKey
weatherURL = ("https://api.openweathermap.org/data/2.5/weather?")# + str(zipcode) + "&" + str(APPID))

# SmartThings API URL and parameters
smartThingsURL = ("https://api.smartthings.com/v1/")
devicesEndpoint = "devices/"
installedAppsEndpoint = "installedapps/"
subscriptionEndpoint = "/subscriptions"
deviceStatusCheckEndpoint = "/components/main/status"
"""
# hard coded test info for GET testing below. 
# need to have a local file for storage that is ignored by github
with open("./api/deviceId_darts.txt", "r") as f:
	dartsLight = f.read().rstrip()

# need to have a local file for storage that is ignored by github
with open("./api/deviceId_darkSwitch.txt", "r") as f:
	darkSwitch = f.read().rstrip()
"""
# need to have a local file for storage that is ignored by github
componentsEndpoint = "/commands"
with open("./api/tokenST.txt", "r") as f:
	smartThingsAuth = f.read().rstrip()



class Lifecycles(APIView):
	# interacting with SmartThings Lifecycles
	permission_classes = (AllowAny,)
	parser_classes = (parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser)
	renderer_classes = (renderers.JSONRenderer,)

	def get(self, request):
		"""
		this get request is for testing api calls to weather API and SmartThings API
		"""

		params = {"zip": "68116", "APPID": weatherApiKey}

		currentWeather = requests.get(url = weatherURL, params = params)

		currentWeatherDict = json.loads(currentWeather.text) # converts JSON into dictionary
		location = currentWeatherDict['name']
		weatherMain = currentWeatherDict['weather'][0]['main']
		weatherId = currentWeatherDict['weather'][0]['id']
		weatherDescription = currentWeatherDict['weather'][0]['description']
		cloudinessInt = currentWeatherDict['clouds']['all']
		sunrise = currentWeatherDict['sys']['sunrise']
		sunset = currentWeatherDict['sys']['sunset']
		# summary for console output
		weatherSummary = ("##########\nWeather Summary:\nLocation: " + location + "\nWeather Type: " + weatherMain + "\nWeather ID: " + str(weatherId) + "\nWeather Description: " + weatherDescription + "\nCloudiness: " + str(cloudinessInt) + "%\n##########")
		sunTimes = ("Sun Times in Epoc UTC:\nSunrise: " + str(sunrise) + "\nSunset: " + str(sunset) + "\n##########\n" )
		print(weatherSummary)
		print(sunTimes)

		# API call to SmartThings GET device
		smartThingsGetDevices = requests.get(url = (smartThingsURL + devicesEndpoint + dartsLight + deviceStatusCheckEndpoint), headers={'Authorization': ('Bearer ' + smartThingsAuth)})
		#print("smartThingsGetDevices return code: " + str(smartThingsGetDevices))
		smartThingsGetDevicesDict = json.loads(smartThingsGetDevices.text)
		#print("ST API GET Return: " + str(smartThingsGetDevicesDict) + "\n\n")
		# trying to get device status
		deviceStatus = smartThingsGetDevicesDict["switch"]['switch']['value'] # could also be light, switch, value.
		print("dartsLight deviceStatus: " + str(deviceStatus))


		if (deviceStatus == "off"):
			print("light was off, turning on.")
			switchCommand = "on"
		else:
			print("light was on, turning off.")
			switchCommand = "off"

		# API call to SmartThings POST device start
		data = json.dumps({"commands": [{"component": "main", "capability": "switch", "command": switchCommand}]})

		#print(data)
		smartThingsCommand = requests.post(url = (smartThingsURL + devicesEndpoint + dartsLight + componentsEndpoint), data = data, headers = {'Authorization': 'Bearer ' + smartThingsAuth + ''})
		smartThingsCommandDict = json.loads(smartThingsCommand.text)

		# troubleshooting if requests aren't good
		if (str(smartThingsCommand) == "<Response [200]>"):
			print("API Call Success!")
		else:
			print("smartThingsCommand response: " + str(smartThingsCommand))
			print("ST API POST Return: " + str(smartThingsCommandDict))


		# logic to switch darkSwitch on and off. This will trigger the modes switch at the hub via a routine
		print("\n##########\nWeather logic results below:")

		# check current status of darkSwitch
		smartThingsGetDevices = requests.get(url = (smartThingsURL + devicesEndpoint + darkSwitch + deviceStatusCheckEndpoint), headers={'Authorization': ('Bearer ' + smartThingsAuth)})
		smartThingsGetDevicesDict = json.loads(smartThingsGetDevices.text)
		deviceStatus = smartThingsGetDevicesDict["switch"]['switch']['value'] # could also be light, switch, value.
		stURL = (smartThingsURL + devicesEndpoint + darkSwitch + componentsEndpoint)
		print("darkSwitch deviceStatus: " + str(deviceStatus))

		if (weatherId == 800): # weather is clear
			print("ITS CLEAR OUTSIDE")
			switchCommand = "off"
		elif (weatherId in range(801,805)): # Weather is cloudy
			if (cloudinessInt <= 50): # threshold for being dark outside
				print("NOT CLOUDY AT ALL")
				switchCommand = "off"
			else:
				print("more cloudy")
				switchCommand = "on"
		elif (weatherId in range(700, 799)):
			print("Atmosphere condition: " + weatherMain)
			switchCommand = "on"
		else:
			print("no matching weatherId")
			switchCommand = "off"

		data = json.dumps({"commands": [{"component": "main", "capability": "switch", "command": switchCommand}]})
		#print(data)
		smartThingsCommand = requests.post(url = (smartThingsURL + devicesEndpoint + darkSwitch + componentsEndpoint), data = data, headers = {'Authorization': 'Bearer ' + smartThingsAuth + ''})

		# troubleshooting if requests aren't good
		if (str(smartThingsCommand) == "<Response [200]>"):
			print("API Call Success!")
		else:
			print("smartThingsCommand response: " + str(smartThingsCommand))
			print("ST API POST Return: " + str(smartThingsCommandDict))
		smartThingsCommandDict = json.loads(smartThingsCommand.text)



		print("##########\n")

		return Response(smartThingsGetDevicesDict, content_type='json', status=status.HTTP_200_OK)
	def post(self, request):
		print("REQUEST DATA: ")
		print(str(request.data))

		lifecycle = bleach.clean(request.data.get('lifecycle'))
		if lifecycle == 'PING':
			print("PING LIFECYCLE")
			#print(request.data.get('pingData'))
			#print("challenge: " + request.data.get('pingData')["challenge"])
			challenge = bleach.clean(request.data.get('pingData')["challenge"])
			print(challenge)

			# nested dictionary below to send appropriate nested json response
			response = {'pingData': {'challenge': challenge}}
			# garbage return "{\"pingData\": {\"challenge\": \"1a904d57-4fab-4b15-a11e-1c4bfe7cb502\"}}"
			# response = json.dumps({'pingData': {'challenge': challenge }})
			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'CONFIGURATION':
			print("CONFIGURATION LIFECYCLE")
			phase = request.data.get('configurationData')['phase']
			if phase == "INITIALIZE":
				print("Config Phase: " + phase)
				response = {"configurationData": {"initialize": {"name": "WeatherAPP", "description":"Weather App to switch modes", "id":"app", "permissions":[], "firstPageId": "1"}}}
			elif phase == "PAGE":
				print("Config Phase: " + phase)
				response = {
				  "configurationData": {
				    "page": {
				      "pageId": "1",
				      "name": "Auto Update mode from weather",
				      "nextPageId": "null",
				      "previousPageId": "null",
				      "complete": "true",
				      "sections": [
				        {
				          "name": "What location to check weather for",
				          "settings": [
				            {
								"id": "zipCode",
								"name": "What 5-digit US Zip Code?",
								"description": "Enter Zip Code",
								"type": "NUMBER",
								"required": "true"
							}
				          ]

				        },
						{
							"name":"Devices to monitor for presence",
							"settings": [
								{
									"id":"presenceDevices",
									"name":"Which Presence Device(s)?",
									"description":"Tap to set",
									"type":"DEVICE",
									"required": "true",
									"multiple": "true",
									"capabilities": ["switch"],
									"permissions": ["r", "x"]
								}
							]
						},
						{
							"name":"Lights to turn on",
							"settings": [
								{
									"id":"lightswitches",
									"name":"Which Lights?",
									"description":"Tap to set",
									"type":"DEVICE",
									"required": "true",
									"multiple": "true",
									"capabilities": ["switch"],
									"permissions": ["r", "x"]
								}
							]
						}
				      ]
				    }
				  }
				}
				# TODO fix presence devices to actually monitor presence Devices.
				print("whew thats a lot of config: " + str(response))

			return Response(response,  status=status.HTTP_200_OK)

		elif lifecycle == 'INSTALL':
			print("INSTALL LIFECYCLE")
			# do something here
			installedAppId = request.data.get('installData')['installedApp']['installedAppId']
			installAuthToken = request.data.get('installData')['authToken']
			installRefreshToken = request.data.get('installData')['refreshToken']
			print("Installed App token: " + str(installAuthToken))
			print("Installed Refresh token: " + str(installRefreshToken))
			print("Installed App ID: " + installedAppId)

			zipCode = request.data.get('installData')['installedApp']['config']['zipCode'][0]['stringConfig']['value']
			print("Zipcode: " + str(zipCode))

			for presenceDeviceId in request.data.get('installData')['installedApp']['config']['presenceDevices']:
				currentPresenceDeviceId = presenceDeviceId['deviceConfig']['deviceId']
				currentComponentId = presenceDeviceId['deviceConfig']['componentId']
				print("Current Device ID: " + currentPresenceDeviceId)
				print("Current Component ID: " + currentComponentId)

				# format requst data to create subscription
				# TODO fix this for actual presence devices
				data = json.dumps({"sourceType":"DEVICE","device": {
					"deviceId": currentPresenceDeviceId,
					"componentId": currentComponentId,
					"capability": "switch",
					"attribute": "switch",
					"stateChangeOnly": "true",
					"value":"on"
				}})

				smartThingsCommand = requests.post(url = (smartThingsURL + installedAppsEndpoint + installedAppId + subscriptionEndpoint), data = data, headers={'Authorization': ('Bearer ' + installAuthToken)})
				print("ST subscription request: " + str(smartThingsCommand))
				print("ST subscription request text: " + smartThingsCommand.content)

			response = {'installData': {}}
			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'UPDATE':
			"""
			When the user updates the configuration of the app this code will run.
			"""
			print("UPDATE LIFECYCLE")
			installedAppId = request.data.get('updateData')['installedApp']['installedAppId']
			installAuthToken = request.data.get('updateData')['authToken']
			installRefreshToken = request.data.get('updateData')['refreshToken']
			print("Installed App token: " + str(installAuthToken))
			print("Installed Refresh token: " + str(installRefreshToken))
			print("Installed App ID: " + installedAppId)

			zipCode = request.data.get('updateData')['installedApp']['config']['zipCode'][0]['stringConfig']['value']
			print("Zipcode: " + str(zipCode))
			# delete previous subscription so you can post this new one.
			smartThingsCommand = requests.delete(url = (smartThingsURL + installedAppsEndpoint + installedAppId + subscriptionEndpoint), headers={'Authorization': ('Bearer ' + installAuthToken)})
			print("SmartThings delete existing subs response: " + smartThingsCommand.content + "\n")

			for presenceDeviceId in request.data.get('updateData')['installedApp']['config']['presenceDevices']:
				currentPresenceDeviceId = presenceDeviceId['deviceConfig']['deviceId']
				currentComponentId = presenceDeviceId['deviceConfig']['componentId']
				print("Current Device ID: " + currentPresenceDeviceId)
				print("Current Component ID: " + currentComponentId)



				# format requst data to create subscription
				# TODO fix this for actual presence devices
				data = json.dumps({"sourceType":"DEVICE","device": {
					"deviceId": currentPresenceDeviceId,
					"componentId": currentComponentId,
					"capability": "switch",
					"attribute": "switch",
					"stateChangeOnly": "true",
					"value":"on"
				}})

				smartThingsCommand = requests.post(url = (smartThingsURL + installedAppsEndpoint + installedAppId + subscriptionEndpoint), data = data, headers={'Authorization': ('Bearer ' + installAuthToken)})
				print("ST subscription request: " + str(smartThingsCommand))
				print("ST subscription request text: " + smartThingsCommand.content)

			response = {'updateData': {}}
			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'UNINSTALL':
			print("UNINSTALL LIFECYCLE")
			response = {'uninstallData': {}}
			return Response({'updateData': {}}, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'EVENT':
			print("EVENT LIFECYCLE")
			#info from smartThings
			zipCode = request.data.get('eventData')['installedApp']['config']['zipCode'][0]['stringConfig']['value']

			print("Zipcode: " + str(zipCode))
			presenceDeviceId = request.data.get('eventData')['installedApp']['config']['presenceDevices'][0]['deviceConfig']['deviceId']
			print("presenceDeviceId: " + str(presenceDeviceId))
			lightswitches = request.data.get('eventData')['installedApp']['config']['lightswitches'][0]['deviceConfig']['deviceId']

			# weather API here
			params = {"zip": zipCode, "APPID": weatherApiKey}

			currentWeather = requests.get(url = weatherURL, params = params)

			currentWeatherDict = json.loads(currentWeather.text) # converts JSON into dictionary
			location = currentWeatherDict['name']
			weatherMain = currentWeatherDict['weather'][0]['main']
			weatherId = currentWeatherDict['weather'][0]['id']
			weatherDescription = currentWeatherDict['weather'][0]['description']
			cloudinessInt = currentWeatherDict['clouds']['all']
			sunrise = currentWeatherDict['sys']['sunrise']
			sunset = currentWeatherDict['sys']['sunset']
			# summary for console output
			weatherSummary = ("##########\nWeather Summary:\nLocation: " + location + "\nWeather Type: " + weatherMain + "\nWeather ID: " + str(weatherId) + "\nWeather Description: " + weatherDescription + "\nCloudiness: " + str(cloudinessInt) + "%\n##########")
			sunTimes = ("Sun Times in Epoc UTC:\nSunrise: " + str(sunrise) + "\nSunset: " + str(sunset) + "\n##########\n" )
			print(weatherSummary)
			print(sunTimes)

			# SmartThings execution here
			if (weatherId == 800): # weather is clear
				print("ITS CLEAR OUTSIDE")
				switchCommand = "off"
			elif (weatherId in range(801,805)): # Weather is cloudy
				if (cloudinessInt <= 50): # threshold for being dark outside
					print("NOT CLOUDY AT ALL")
					switchCommand = "off"
				else:
					print("more cloudy")
					switchCommand = "on"
			elif (weatherId in range(200, 799)):
				print("Atmosphere condition: " + weatherMain)
				switchCommand = "on"
			else:
				print("no matching weatherId")
				switchCommand = "off"

			switchCommand = "on" # test value to illustrate event lifecycle.
			data = json.dumps({"commands": [{"component": "main", "capability": "switch", "command": switchCommand}]})
			#print(data)
			if (switchCommand == "on"):
				for lightswitch in request.data.get('eventData')['installedApp']['config']['lightswitches']:
					currentLight = lightswitch['deviceConfig']['deviceId']
					smartThingsCommand = requests.post(url = (smartThingsURL + devicesEndpoint + currentLight + componentsEndpoint), data = data, headers = {'Authorization': 'Bearer ' + smartThingsAuth + ''})

				# troubleshooting if requests aren't good
				if (str(smartThingsCommand) == "<Response [200]>"):
					print("API Call Success!")
				else:
					print("smartThingsCommand response: " + str(smartThingsCommand))
					print("ST API POST Return: " + str(smartThingsCommandDict))
			else:
				print("No action taken, its still light outside")

			#print("Zipcode: " + str(zipCode))
			# do handleEvent here like set mode (virtual switch) let the app take care of the rest.
			# do something here

			response = {'eventData': {}}
			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'OAUTH_CALLBACK':
			print("OAUTH_CALLBACK LIFECYCLE")
			response = {'oAuthCallbackData':'{}'}
			return Response(response, content_type='json', status=status.HTTP_200_OK)
		else:
			print("Invalid POST")
			return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)

class Register(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # Login
		username = request.POST.get('username')
		password = request.POST.get('password')
		email = request.POST.get('email')
		if username is not None and password is not None and email is not None:
	        # lastname = request.POST.get('lastname')
	        # firstname = request.POST.get('firstname')
	        # org = request.POST.get('org')
	        # college = request.POST.get('college')
	        # dept = request.POST.get('dept')
	        # other_details = request.POST.get('otherdetails')
	        # areas_of_interest = request.POST.get('areasofinterest')
	        # areas_of_interest = api.Areaofinterest.objects.get_or_create(name=areas_of_interest)

			print request.POST.get('username')
			if User.objects.filter(username=username).exists():
			    return Response({'username': 'Username is taken.', 'status': 'error'})
			elif User.objects.filter(email=email).exists():
			    return Response({'email': 'Email is taken.', 'status': 'error'})
			# especially before you pass them in here
			newuser = User.objects.create_user(email=email, username=username, password=password)

			newprofile = api.Profile(user=newuser)

			newprofile.save()
			# Send email msg
			# send_templated_mail(
			#     template_name='welcome',
			#     from_email='from@example.com',
			#     recipient_list=[email],
			#     context={
			#         'username':username,
			#         'email':email,
			#     },
			#     # Optional:
			#     # cc=['cc@example.com'],
			#     # bcc=['bcc@example.com'],
			# )
			return Response({'status': 'success', 'userid': newuser.id, 'profile': newprofile.id})
		else:
			return Response({'status': 'error'})


class Session(APIView):
	"""
	Returns a JSON structure: {'isauthenticated':<T|F>,'userid': <int:None>,'username': <string|None>,'profileid': <int|None>}
	"""
	permission_classes = (AllowAny,)
	def form_response(self, isauthenticated, userid, username, profileid, error=""):
		data = {
			'isauthenticated': 	isauthenticated,
			'userid': 			userid,
			'username': 		username,
			'profileid':		profileid,
		}
		if error:
			data['message'] = error

		return Response(data)

	def get(self, request, *args, **kwargs):
		# Get the current user
		user = request.user
		if user.is_authenticated():
			profile = get_object_or_404(api.Profile,user__username=user.username)
			return self.form_response(True, user.id, user.username, profile.id)
		return self.form_response(False, None, None, None)

	def post(self, request, *args, **kwargs):
		print(request.data)
		# Login
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				profile = get_object_or_404(api.Profile,user__username=user.username)
				return self.form_response(True, user.id, user.username, profile.id)
			return self.form_response(False, None, None, None, "Account is suspended")
		return self.form_response(False, None, None, None, "Invalid username or password")

	def delete(self, request, *args, **kwargs):
		# Logout
		logout(request)
		return Response(status=status.HTTP_204_NO_CONTENT)
