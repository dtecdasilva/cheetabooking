from django.db import models
from datetime import datetime
from django.contrib.auth.models import User


class Bus(models.Model):
    picture = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    agency = models.IntegerField()
    seats = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class Location(models.Model):
    region = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class Agency(models.Model):
    name = models.CharField(max_length=255, default='default')
    location = models.CharField(max_length=255)
    country_location = models.IntegerField()
    logo = models.TextField()
    description = models.TextField()
    user = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class Trip(models.Model):
    agency = models.IntegerField()
    location_from = models.IntegerField()
    location_to = models.IntegerField()
    leave_time = models.TimeField()
    arrival_time = models.TimeField()
    bus = models.IntegerField()
    amount = models.IntegerField(default=0)
    trip_date = models.DateTimeField(default=datetime.now, blank=True)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class Book(models.Model):
    name = models.CharField(max_length=255, default=0)
    number = models.IntegerField()
    trip = models.IntegerField()
    seat = models.IntegerField()
    idcn = models.CharField(max_length=255, default=0)
    email = models.CharField(max_length=255, default=0)
    code = models.CharField(max_length=10, default=0)
    status = models.CharField(max_length=255, default="pending")
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class Customer(models.Model):
    userid = models.IntegerField()
    idcn = models.CharField(max_length=255)

