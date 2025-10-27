import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.auth_service.models import UserProfile, LoginAttempt

@pytest.mark.django_db
class TestAuthService:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
            'device_fingerprint': 'test_device_123'
        })
        
        assert response.status_code == 200
        assert 'token' in response.data
        assert response.data['username'] == 'testuser'
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
            'device_fingerprint': 'test_device_123'
        })
        
        assert response.status_code == 401
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser'
        })
        
        assert response.status_code == 400
    
    def test_user_profile_creation(self):
        """Test user profile creation"""
        profile = UserProfile.objects.get(user=self.user)
        assert profile.user == self.user
        assert profile.failed_login_attempts == 0
        assert profile.two_factor_enabled == False
    
    def test_login_attempt_logging(self):
        """Test login attempt is logged"""
        self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123',
            'device_fingerprint': 'test_device_123'
        })
        
        attempt = LoginAttempt.objects.filter(user=self.user, success=True).first()
        assert attempt is not None
        assert attempt.success == True
