# ride_sharing/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('RIDER', 'Rider'),
        ('DRIVER', 'Driver'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Ride(models.Model):
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_rider')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_driver', null=True, blank=True)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # current_location = models.CharField(max_length=255, blank=True, null=True)
    current_location = models.JSONField(null=True, blank=True)  # Store GeoJSON Point
    city = models.CharField(max_length=100, null=True, blank=True)  # Store city name


    def clean(self):
        if self.rider == self.driver and self.driver is not None:
            raise ValidationError("Rider and driver cannot be the same user.")
        if self.driver and not self.driver.profile.role == 'DRIVER':
            raise ValidationError("Only users with the 'Driver' role can be assigned as drivers.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ride {self.id} - {self.rider.username} to {self.dropoff_location}"