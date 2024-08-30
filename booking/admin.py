from django.contrib import admin
from .models import Bus, Location, Trip, Agency, Book, Customer


class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'picture', 'number', 'type', 'agency', 'seats', 'created_at')


admin.site.register(Bus, BusAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'region', 'location', 'image', 'description', 'created_at')


admin.site.register(Location, LocationAdmin)


class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'location_from', 'location_to', 'leave_time', 'arrival_time', 'bus', 'amount', 'trip_date', 'created_at')


admin.site.register(Trip, TripAdmin)


class AgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'country_location', 'logo', 'description', 'user', 'created_at')


admin.site.register(Agency, AgencyAdmin)


class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'trip', 'seat', 'number', 'idcn', 'code', 'email', 'status', 'created_at')


admin.site.register(Book, BookAdmin)


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'userid', 'idcn')


admin.site.register(Customer, CustomerAdmin)