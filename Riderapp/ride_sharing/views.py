from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .models import Ride
from .serializers import UserSerializer, RideSerializer,RideLocationSerializer
from .ride_matching import match_ride_with_driver

import requests
from django.conf import settings
class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
# class UserRegisterView(APIView):
#     def post(self, request):
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RideCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if not request.user.profile.role == 'RIDER':
                return Response({"error": "Only users with the 'Rider' role can create rides"}, 
                               status=status.HTTP_403_FORBIDDEN)
            serializer = RideSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(rider=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

class RideListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rides = Ride.objects.all()
      
        serializer = RideSerializer(rides, many=True)
        return Response(serializer.data)

class RideDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            serializer = RideSerializer(ride)
            return Response(serializer.data)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)

class RideStatusUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            status_value = request.data.get('status')
            if status_value not in dict(Ride.STATUS_CHOICES).keys():
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            ride.status = status_value
            ride.save()
            serializer = RideSerializer(ride)
            return Response(serializer.data)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)

class RideLocationUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            current_location = request.data.get('current_location')
            if not current_location:
                return Response({"error": "Current location required"}, 
                               status=status.HTTP_400_BAD_REQUEST)
            ride.current_location = current_location
            ride.save()
            serializer = RideSerializer(ride)
            return Response(serializer.data)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)
class RideLocationUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_city_from_coordinates(self, longitude, latitude):
        """Perform reverse geocoding using Geoapify API."""
        try:
            url = f"https://api.geoapify.com/v1/geocode/reverse?lat={latitude}&lon={longitude}&apiKey={settings.GEOAPIFY_API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Extract city from the first result
            features = data.get('features', [])
            if features:
                city = features[0].get('properties', {}).get('city', '')
                return city if city else 'Unknown'
            return 'Unknown'
        except requests.RequestException as e:
            print(f"Reverse geocoding error: {e}")
            return 'Unknown'

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            
            if ride.driver != request.user and ride.rider != request.user:
                return Response({"error": "Unauthorized to update this ride"}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            serializer = RideLocationSerializer(data=request.data)
            if serializer.is_valid():
                current_location = serializer.validated_data['current_location']
                # Update ride's current location
                ride.current_location = current_location
                # Get city name from coordinates
                lng, lat = current_location['coordinates']
                ride.city = self.get_city_from_coordinates(lng, lat)
                ride.save()
                
                # Return serialized ride data
                ride_serializer = RideSerializer(ride)
                return Response(ride_serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)

class RideAcceptView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
            if ride.status != 'REQUESTED':
                return Response({"error": "Ride cannot be accepted"}, 
                               status=status.HTTP_400_BAD_REQUEST)
            if ride.rider == request.user:
                return Response({"error": "Rider cannot accept their own ride"}, 
                               status=status.HTTP_400_BAD_REQUEST)
            if not request.user.profile.role == 'DRIVER':
                return Response({"error": "Only users with the 'Driver' role can accept rides"}, 
                               status=status.HTTP_403_FORBIDDEN)
            ride.driver = request.user
            ride.status = 'ACCEPTED'
            ride.save()
            serializer = RideSerializer(ride)
            return Response(serializer.data)
        except Ride.DoesNotExist:
            return Response({"error": "Ride not found"}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

class RideMatchDriverView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ride = Ride.objects.filter(status='REQUESTED', rider=request.user).last()
        if not ride:
            return Response({"error": "No pending ride requests"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        driver = match_ride_with_driver(ride)
        if driver:
            ride.driver = driver
            ride.status = 'ACCEPTED'
            ride.save()
            serializer = RideSerializer(ride)
            return Response(serializer.data)
        return Response({"error": "No drivers available"}, 
                       status=status.HTTP_404_NOT_FOUND)