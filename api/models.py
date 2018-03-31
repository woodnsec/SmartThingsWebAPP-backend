from __future__ import unicode_literals

from django.db import models
from django.core.validators import *

from django.contrib.auth.models import User, Group

from django.contrib import admin
import base64


class Event(models.Model):
    eventtype = models.CharField(max_length=1000, blank=False)
    timestamp = models.DateTimeField(max_length=1000, blank=False)
    userid = models.CharField(max_length=1000, blank=True)
    requestor = models.GenericIPAddressField(blank=False)

    def __str__(self):
        return str(self.eventtype)


class EventAdmin(admin.ModelAdmin):
    list_display = ('eventtype', 'timestamp')


class ApiKey(models.Model):
    owner = models.CharField(max_length=1000, blank=False)
    key = models.CharField(max_length=5000, blank=False)

    def __str__(self):
        return str(self.owner) + str(self.key)


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('owner', 'key')


class Breed(models.Model):
    TINY = 'Tiny'
    SMALL = 'Small'
    MEDIUM = 'Medium'
    LARGE = 'Large'
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    number_choices = (
        (ONE, 1),
        (TWO, 2),
        (THREE, 3),
        (FOUR, 4),
        (FIVE, 5),
    )
    size_choices = (
        (TINY, 'Tiny'),
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
    )

    breedname = models.CharField(max_length=1000, blank=False)
    size = models.CharField(max_length=6, choices=size_choices, default=MEDIUM,
                            blank=False)  # needs to be one of several choices
    friendliness = models.IntegerField(choices=number_choices, default=THREE, blank=False)  # needs to be 1-5
    trainability = models.IntegerField(choices=number_choices, default=THREE, blank=False)  # needs to be 1-5
    sheddingamount = models.IntegerField(choices=number_choices, default=THREE, blank=False)  # needs to be 1-5
    exerciseneeds = models.IntegerField(choices=number_choices, default=THREE, blank=False)  # needs to be 1-5


class BreedAdmin(admin.ModelAdmin):
    list_display = ('id', 'breedname')


class Dog(models.Model):
    name = models.CharField(max_length=1000, blank=False)
    age = models.IntegerField(blank=False)
    gender = models.CharField(max_length=1000, blank=False)
    color = models.CharField(max_length=1000, blank=False)
    favoriteFood = models.CharField(max_length=1000, blank=False)
    favoriteToy = models.CharField(max_length=1000, blank=False)
    # breed = models.CharField(max_length=1000, blank=False)#needs to be a forign key field
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE)


class DogAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
