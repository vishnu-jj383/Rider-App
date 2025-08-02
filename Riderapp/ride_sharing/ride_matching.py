# ride_sharing/ride_matching.py
from django.contrib.auth.models import User
from .models import Ride, UserProfile

def match_ride_with_driver(ride):
    available_drivers = User.objects.filter(
        is_active=True, 
        profile__role='DRIVER'
    ).exclude(id=ride.rider.id)
    return available_drivers.first() if available_drivers.exists() else None