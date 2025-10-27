from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    """Extended user profile with security metadata"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    device_fingerprint = models.CharField(max_length=255, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_country = models.CharField(max_length=100, blank=True)
    last_login_timestamp = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class LoginAttempt(models.Model):
    """Track all login attempts for anomaly detection"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    risk_score = models.FloatField(null=True, blank=True)
    risk_action = models.CharField(max_length=50, choices=[
        ('allow', 'Allow'),
        ('step_up_2fa', 'Step-up 2FA'),
        ('block', 'Block'),
    ], default='allow')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]

class Session(models.Model):
    """Secure session management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500, unique=True)
    ip_address = models.GenericIPAddressField()
    device_fingerprint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
