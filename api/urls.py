# @Author: Matthew Hale <matthale>
# @Date:   2018-02-28T00:25:25-06:00
# @Email:  mlhale@unomaha.edu
# @Filename: urls.py
# @Last modified by:   matthale
# @Last modified time: 2018-03-02T02:50:46-06:00
# @Copyright: Copyright (C) 2018 Matthew L. Hale



from django.conf.urls import include, url

#Django Rest Framework
from rest_framework import routers

from api import controllers
from django.views.decorators.csrf import csrf_exempt

#REST API routes
router = routers.DefaultRouter(trailing_slash=False)


urlpatterns = [
    url(r'^session', csrf_exempt(controllers.Session.as_view())),
    url(r'^register', csrf_exempt(controllers.Register.as_view())),
    url(r'^lifecycle', csrf_exempt(controllers.Lifecycles.as_view())),
    url(r'^', include(router.urls)),
]
