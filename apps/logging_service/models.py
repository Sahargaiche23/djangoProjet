from django.db import models
from django.contrib.auth.models import User
import uuid

class AccessLog(models.Model):
    """Access and activity logs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    event_type = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    action = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failure', 'Failure'),
    ], default='success')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['resource_type', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]

class LogAnomaly(models.Model):
    """Detected log anomalies"""
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access_log = models.ForeignKey(AccessLog, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    confidence_score = models.FloatField()
    description = models.TextField()
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    investigated = models.BooleanField(default=False)
    investigation_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['severity', '-detected_at']),
            models.Index(fields=['anomaly_type', '-detected_at']),
        ]

class LogTimeline(models.Model):
    """Timeline view of related logs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logs = models.ManyToManyField(AccessLog, related_name='timelines')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
