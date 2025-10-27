from rest_framework import serializers
from .models import UserProfile, LoginAttempt

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'device_fingerprint', 'last_login_ip', 'last_login_country', 
                  'last_login_timestamp', 'failed_login_attempts', 'two_factor_enabled']

class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = ['id', 'user', 'ip_address', 'country', 'device_fingerprint', 
                  'success', 'risk_score', 'risk_action', 'timestamp']
