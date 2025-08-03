from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import resolve
from django.contrib.auth.models import User
from ride_sharing.models import UserProfile, Ride
from unittest.mock import patch

class UserRegistrationTests(APITestCase):
    def setUp(self):
        # Assuming setUp creates rider1, driver1, and a ride
        self.rider = User.objects.create_user(username='rider1', password='test123', email='rider1@example.com')
        UserProfile.objects.create(user=self.rider, role='RIDER')
        self.driver = User.objects.create_user(username='driver1', password='test123', email='driver1@example.com')
        UserProfile.objects.create(user=self.driver, role='DRIVER')
        self.ride = Ride.objects.create(rider=self.rider, pickup_location='123 Main St', dropoff_location='456 Oak Ave')

    def get_token(self, username, password):
        response = self.client.post('/api/token/', {'username': username, 'password': password}, format='json')
        return response.data.get('access') if response.status_code == 200 else None

    def test_user_registration_with_role(self):
        print(resolve('/api/users/register/'))  # Debug URL
        response = self.client.post('/api/users/register/', {  # Adjust to /api/ if needed
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'test123',
            'profile': {'role': 'RIDER'}
        }, format='json')
        print("Response content:", response.content)  # Debug 404
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_profile = UserProfile.objects.get(user__username='testuser')
        self.assertEqual(user_profile.role, 'RIDER')
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')

    