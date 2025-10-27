from rest_framework import serializers
from .models import Incident, IncidentPlaybook, IncidentTimeline

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ['id', 'title', 'description', 'severity', 'status', 'assigned_to', 
                  'created_at', 'updated_at', 'resolved_at', 'priority_score', 
                  'affected_assets', 'metadata']

class IncidentPlaybookSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentPlaybook
        fields = ['id', 'incident', 'title', 'description', 'steps', 'status', 'created_at', 'completed_at']

class IncidentTimelineSerializer(serializers.ModelSerializer):
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    
    class Meta:
        model = IncidentTimeline
        fields = ['id', 'incident', 'event_type', 'description', 'performed_by', 
                  'performed_by_username', 'created_at', 'metadata']
