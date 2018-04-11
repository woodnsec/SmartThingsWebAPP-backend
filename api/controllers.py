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
import datetime, pytz

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

import json

import bleach


def home(request):
	"""
	Send requests to '/' to the ember.js clientside app
	"""

	return render(request, 'index.html')

def staff_or_401(request):
    if not request.user.is_staff:
        return Response({'success': False},status=status.HTTP_401_UNAUTHORIZED)

def super_user_or_401(request):
    if not request.user.is_superuser:
        return Response({'success': False},status=status.HTTP_401_UNAUTHORIZED)

def admin_or_401(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'success': False},status=status.HTTP_401_UNAUTHORIZED)

from api.pagination import *
import json, datetime, pytz
from django.core import serializers
from django.core.validators import validate_email, validate_image_file_extension
import requests

# bleach for input sanitizing input
import bleach
# re for regex
import re




"""
one post endpoint for lifecycles, must conform to ST reqs must have switch statement for lifecycles
"""

class Lifecycles(APIView):
	# interacting with SmartThings Lifecycles

	# weather api stuff definitions here
	zipcode = 68116
	weatherApiKey = "test-key"
	APPID = "APPID=" + weatherApiKey
	weatherURL = ("https://api.openweathermap.org/data/2.5/weather?" + str(zipcode) + "&" + APPID)

	permission_classes = (AllowAny,)
	parser_classes = (parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser)
	renderer_classes = (renderers.JSONRenderer,)

	def get(self, request):
		console.log("REQUEST DATA: \n")
		print(str(request.data))

		return Response({'success': True}, content_type='json', status=status.HTTP_200_OK)
	def post(self, request):
		print("REQUEST DATA: \n")
		print(str(request.data))

		lifecycle = bleach.clean(request.data.get('lifecycle'))
		if lifecycle == 'PING':
			print("PING LIFECYCLE")
			print(request.data.get('pingData'))
			print(request.data.get('pingData')["challenge"])
			challenge = bleach.clean(request.data.get('pingData')["challenge"])
			print(challenge)

			# nested dictionary below to send appropriate json response
			response = {'pingData': {'challenge': challenge}}

			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'CONFIGURATION':
			print("CONFIGURATION LIFECYCLE")

			return JsonResponse(challenge,  status=status.HTTP_200_OK)

		elif lifecycle == 'INSTALL':
			print("INSTALL LIFECYCLE")
			response = {'installData': {}}
			return Response(response, content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'UPDATE':
			print("UPDATE LIFECYCLE")

			return Response(content_type='json', status=status.HTTP_200_OK)
		elif lifecycle == 'UNINSTALL':
			print("UNINSTALL LIFECYCLE")

			return Response(content_type='json', status=status.HTTP_200_OK)

		elif lifecycle == 'EVENT':
			print("EVENT LIFECYCLE")
			# weather API here


			# do handleEvent here like set mode (virtual switch) let the app take care of the rest.


			return Response(content_type='json', status=status.HTTP_200_OK)
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
