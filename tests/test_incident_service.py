import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.incident_service.models import Incident, IncidentPlaybook

@pytest.mark.django_db
class TestIncidentService:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_incident(self):
        """Test incident creation"""
        response = self.client.post('/api/incidents/', {
            'title': 'Test Incident',
            'description': 'This is a test incident',
            'severity': 'high',
            'affected_assets': ['asset1', 'asset2']
        })
        
        assert response.status_code == 201
        assert response.data['title'] == 'Test Incident'
        assert response.data['severity'] == 'high'
    
    def test_incident_triage(self):
        """Test incident is triaged automatically"""
        incident = Incident.objects.create(
            title='Test Incident',
            description='Critical security breach detected',
            severity='critical',
            affected_assets=['database_server']
        )
        
        assert incident.priority_score > 0
        assert incident.metadata.get('triage_result') is not None
    
    def test_incident_playbook_creation(self):
        """Test playbooks are created for incident"""
        incident = Incident.objects.create(
            title='Test Incident',
            description='Authentication incident detected',
            severity='high',
            affected_assets=['auth_service']
        )
        
        playbooks = IncidentPlaybook.objects.filter(incident=incident)
        assert playbooks.count() > 0
    
    def test_assign_incident(self):
        """Test assigning incident to user"""
        incident = Incident.objects.create(
            title='Test Incident',
            description='Test',
            severity='high',
            affected_assets=[]
        )
        
        response = self.client.post(f'/api/incidents/{incident.id}/assign/', {
            'user_id': self.user.id
        })
        
        assert response.status_code == 200
        incident.refresh_from_db()
        assert incident.assigned_to == self.user
