from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import Incident, IncidentPlaybook, IncidentTimeline, IncidentTemplate
from .serializers import IncidentSerializer, IncidentPlaybookSerializer, IncidentTimelineSerializer
from .ai_models import TriageAssistant
from apps.core.models import AuditLog

class IncidentViewSet(viewsets.ModelViewSet):
    """Incident management endpoints"""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['severity', 'status', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['-created_at', '-priority_score']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.triage = TriageAssistant()
    
    def perform_create(self, serializer):
        incident = serializer.save()
        
        # Run triage
        triage_data = {
            'severity': incident.severity,
            'description': incident.description,
            'affected_assets': incident.affected_assets,
            'source': 'manual',
        }
        
        triage_result = self.triage.triage_incident(triage_data)
        
        incident.priority_score = triage_result['priority_score']
        incident.metadata = {
            'triage_result': triage_result,
            'suggested_playbooks': triage_result['suggested_playbooks'],
        }
        incident.save()
        
        # Create playbooks
        for playbook_name in triage_result['suggested_playbooks']:
            IncidentPlaybook.objects.create(
                incident=incident,
                title=playbook_name,
                description=f"Automated playbook for {playbook_name}",
                steps=self._get_playbook_steps(playbook_name),
            )
        
        # Create timeline entry
        IncidentTimeline.objects.create(
            incident=incident,
            event_type='created',
            description='Incident created and triaged',
            performed_by=self.request.user,
        )
        
        AuditLog.objects.create(
            user=self.request.user,
            action='create_incident',
            resource_type='incident',
            resource_id=str(incident.id),
            status='success',
        )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign incident to user"""
        incident = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        incident.assigned_to = user
        incident.save()
        
        IncidentTimeline.objects.create(
            incident=incident,
            event_type='assigned',
            description=f'Assigned to {user.username}',
            performed_by=request.user,
        )
        
        return Response(IncidentSerializer(incident).data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update incident status"""
        incident = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Incident.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = incident.status
        incident.status = new_status
        
        if new_status == 'resolved':
            incident.resolved_at = timezone.now()
        
        incident.save()
        
        IncidentTimeline.objects.create(
            incident=incident,
            event_type='status_changed',
            description=f'Status changed from {old_status} to {new_status}',
            performed_by=request.user,
        )
        
        return Response(IncidentSerializer(incident).data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get incident summary"""
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        incidents = Incident.objects.filter(created_at__gte=since)
        
        summary = {
            'total': incidents.count(),
            'by_severity': {
                'critical': incidents.filter(severity='critical').count(),
                'high': incidents.filter(severity='high').count(),
                'medium': incidents.filter(severity='medium').count(),
                'low': incidents.filter(severity='low').count(),
            },
            'by_status': {
                'open': incidents.filter(status='open').count(),
                'investigating': incidents.filter(status='investigating').count(),
                'resolved': incidents.filter(status='resolved').count(),
                'closed': incidents.filter(status='closed').count(),
            },
            'avg_priority_score': incidents.aggregate(models.Avg('priority_score'))['priority_score__avg'] or 0,
        }
        
        return Response(summary)
    
    @staticmethod
    def _get_playbook_steps(playbook_name):
        """Get steps for playbook"""
        playbooks = {
            'authentication_incident': [
                {'step': 1, 'action': 'Review failed login attempts', 'owner': 'security'},
                {'step': 2, 'action': 'Force password reset', 'owner': 'admin'},
                {'step': 3, 'action': 'Enable MFA', 'owner': 'admin'},
                {'step': 4, 'action': 'Monitor for further attempts', 'owner': 'security'},
            ],
            'data_breach_response': [
                {'step': 1, 'action': 'Isolate affected systems', 'owner': 'infrastructure'},
                {'step': 2, 'action': 'Preserve evidence', 'owner': 'security'},
                {'step': 3, 'action': 'Notify affected parties', 'owner': 'legal'},
                {'step': 4, 'action': 'Begin forensic investigation', 'owner': 'security'},
            ],
            'malware_containment': [
                {'step': 1, 'action': 'Disconnect infected systems', 'owner': 'infrastructure'},
                {'step': 2, 'action': 'Scan all systems', 'owner': 'security'},
                {'step': 3, 'action': 'Update antivirus signatures', 'owner': 'infrastructure'},
                {'step': 4, 'action': 'Restore from clean backups', 'owner': 'infrastructure'},
            ],
            'critical_incident_response': [
                {'step': 1, 'action': 'Activate war room', 'owner': 'management'},
                {'step': 2, 'action': 'Notify stakeholders', 'owner': 'management'},
                {'step': 3, 'action': 'Begin incident investigation', 'owner': 'security'},
                {'step': 4, 'action': 'Implement containment measures', 'owner': 'infrastructure'},
            ],
        }
        
        return playbooks.get(playbook_name, [])

class IncidentPlaybookViewSet(viewsets.ModelViewSet):
    """Incident playbook management"""
    queryset = IncidentPlaybook.objects.all()
    serializer_class = IncidentPlaybookSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def execute_step(self, request, pk=None):
        """Execute a playbook step"""
        playbook = self.get_object()
        step_number = request.data.get('step_number')
        
        if playbook.status == 'pending':
            playbook.status = 'in_progress'
            playbook.save()
        
        IncidentTimeline.objects.create(
            incident=playbook.incident,
            event_type='playbook_step_executed',
            description=f'Executed step {step_number} of playbook: {playbook.title}',
            performed_by=request.user,
        )
        
        return Response(IncidentPlaybookSerializer(playbook).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark playbook as completed"""
        playbook = self.get_object()
        playbook.status = 'completed'
        playbook.completed_at = timezone.now()
        playbook.save()
        
        return Response(IncidentPlaybookSerializer(playbook).data)

class IncidentTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """Incident timeline (read-only)"""
    queryset = IncidentTimeline.objects.all()
    serializer_class = IncidentTimelineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['incident']
    ordering_fields = ['-created_at']
