from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Ride, UserProfile
from .ride_matching import match_ride_with_driver

class RideSharingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(username='rider1', password='test123', email='rider1@example.com')
        self.driver = User.objects.create_user(username='driver1', password='test123', email='driver1@example.com')
        UserProfile.objects.create(user=self.rider, role='RIDER')
        UserProfile.objects.create(user=self.driver, role='DRIVER')
        
    def get_token(self, username, password):
        response = self.client.post('/api/token/', {
            'username': username,
            'password': password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

        def test_driver_cannot_create_ride(self):
        token = self.get_token('driver1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/rides/', {
            'pickup_location': '123 Main St',
            'dropoff_location': '456 Oak Ave'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "Only users with the 'Rider' role can create rides")
        self.assertEqual(Ride.objects.count(), 0)  # No ride should be created

    def test_user_registration_with_role(self):
        response = self.client.post('/users/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'test123',
            'profile': {'role': 'RIDER'}
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.get(user__username='testuser').role, 'RIDER')

    def test_user_login(self):
        token = self.get_token('rider1', 'test123')
        self.assertIsNotNone(token)

    def test_create_ride(self):
        token = self.get_token('rider1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/rides/', {
            'pickup_location': '123 Main St',
            'dropoff_location': '456 Oak Ave'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ride.objects.count(), 1)
        self.assertEqual(Ride.objects.first().rider, self.rider)

    def test_update_ride_status(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        token = self.get_token('rider1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.patch(f'/rides/{ride.id}/update_status/', {
            'status': 'CANCELLED'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride.refresh_from_db()
        self.assertEqual(ride.status, 'CANCELLED')

    def test_ride_matching(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        matched_driver = match_ride_with_driver(ride)
        self.assertIsNotNone(matched_driver)
        self.assertEqual(matched_driver.profile.role, 'DRIVER')
        self.assertNotEqual(matched_driver.id, self.rider.id)

    def test_rider_cannot_accept_own_ride(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        token = self.get_token('rider1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/rides/{ride.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Rider cannot accept their own ride')
        ride.refresh_from_db()
        self.assertEqual(ride.status, 'REQUESTED')
        self.assertIsNone(ride.driver)

    def test_non_driver_cannot_accept_ride(self):
        non_driver = User.objects.create_user(username='rider2', password='test123', email='rider2@example.com')
        UserProfile.objects.create(user=non_driver, role='RIDER')
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        token = self.get_token('rider2', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/rides/{ride.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "Only users with the 'Driver' role can accept rides")
        ride.refresh_from_db()
        self.assertEqual(ride.status, 'REQUESTED')
        self.assertIsNone(ride.driver)

    def test_driver_can_accept_ride(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        token = self.get_token('driver1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(f'/rides/{ride.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride.refresh_from_db()
        self.assertEqual(ride.status, 'ACCEPTED')
        self.assertEqual(ride.driver, self.driver)

    def test_update_location(self):
        ride = Ride.objects.create(
            rider=self.rider,
            pickup_location='123 Main St',
            dropoff_location='456 Oak Ave'
        )
        token = self.get_token('rider1', 'test123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.patch(f'/rides/{ride.id}/update_location/', {
            'current_location': '789 Pine St'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride.refresh_from_db()
        self.assertEqual(ride.current_location, '789 Pine St')