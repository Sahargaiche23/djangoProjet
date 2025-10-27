from rest_framework import serializers
from .models import AccessLog, LogAnomaly, LogTimeline

class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields = ['id', 'user', 'event_type', 'resource_type', 'resource_id', 'action', 
                  'status', 'ip_address', 'latency_ms', 'error_code', 'error_message', 
                  'metadata', 'timestamp']

class LogAnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAnomaly
        fields = ['id', 'access_log', 'anomaly_type', 'severity', 'confidence_score', 
                  'description', 'detected_at', 'investigated', 'investigation_notes']

class LogTimelineSerializer(serializers.ModelSerializer):
    logs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LogTimeline
        fields = ['id', 'title', 'description', 'logs_count', 'created_at', 'created_by']
    
    def get_logs_count(self, obj):
        return obj.logs.count()
