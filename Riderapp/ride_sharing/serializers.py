# ride_sharing/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Ride
import json
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        # Check for empty or whitespace-only email
        if not value or value.strip() == '':
            raise serializers.ValidationError("Email cannot be empty")
        
        
        
        # Check if email is unique
        if User.objects.filter(email=value.strip()).exists():
            raise serializers.ValidationError("This email is already in use")
        
        return value.strip()
        

    def validate(self, data):
        # Ensure profile data is present
        if 'profile' not in data or not data['profile']:
            raise serializers.ValidationError({"profile": "Profile data is required"})
        return data
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, **profile_data)
        return user

class RideLocationSerializer(serializers.Serializer):
    current_location = serializers.JSONField()

    def validate_current_location(self, value):
        try:
            if isinstance(value, str):
                value = json.loads(value)
            
            if not isinstance(value, dict) or value.get('type') != 'Point':
                raise serializers.ValidationError("Location must be a valid GeoJSON Point")
            
            coordinates = value.get('coordinates', [])
            if len(coordinates) != 2:
                raise serializers.ValidationError("Coordinates must contain [longitude, latitude]")
            
            lng, lat = coordinates
            if not (-180 <= lng <= 180):
                raise serializers.ValidationError("Invalid longitude value")
            if not (-90 <= lat <= 90):
                raise serializers.ValidationError("Invalid latitude value")
            
            return value
        except (json.JSONDecodeError, TypeError):
            raise serializers.ValidationError("Invalid location format")


class RideSerializer(serializers.ModelSerializer):
    rider = serializers.StringRelatedField()
    driver = serializers.StringRelatedField()
    
    class Meta:
        model = Ride
        fields = ['id', 'rider', 'driver', 'pickup_location', 'dropoff_location', 
                 'status', 'created_at', 'updated_at', 'current_location','city']