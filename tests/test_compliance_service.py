import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from apps.compliance_service.models import ComplianceRule, ComplianceAudit
from apps.compliance_service.ai_models import ComplianceAuditor

@pytest.mark.django_db
class TestComplianceService:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_create_compliance_rule(self):
        """Test creating compliance rule"""
        response = self.client.post('/api/compliance/rules/', {
            'name': 'Data Encryption',
            'framework': 'gdpr',
            'severity': 'critical',
            'description': 'Data must be encrypted',
            'rule_text': 'All data at rest must be encrypted'
        })
        
        assert response.status_code == 201
        assert response.data['name'] == 'Data Encryption'
    
    def test_create_compliance_audit(self):
        """Test creating compliance audit"""
        response = self.client.post('/api/compliance/audits/', {
            'title': 'GDPR Audit',
            'framework': 'gdpr',
            'start_date': '2024-01-01T00:00:00Z'
        })
        
        assert response.status_code == 201
        assert response.data['framework'] == 'gdpr'
    
    def test_compliance_auditor_analysis(self):
        """Test compliance auditor analysis"""
        auditor = ComplianceAuditor()
        
        system_config = {
            'tls_enabled': True,
            'data_encryption_enabled': True,
            'rbac_enabled': True,
            'mfa_enabled': True,
            'password_min_length': 12,
            'password_complexity_required': True,
            'password_expiration_days': 90,
        }
        
        audit_logs = [
            {'timestamp': '2024-01-01T00:00:00Z'},
            {'timestamp': '2024-01-01T01:00:00Z'},
        ]
        
        result = auditor.audit_system('gdpr', system_config, audit_logs)
        
        assert 'compliance_score' in result
        assert 'gaps' in result
        assert 'passed_checks' in result
        assert 'failed_checks' in result
    
    def test_compliance_checklist_generation(self):
        """Test compliance checklist generation"""
        auditor = ComplianceAuditor()
        checklist = auditor.generate_checklist('gdpr')
        
        assert len(checklist) > 0
        assert all('item' in item for item in checklist)
        assert all('severity' in item for item in checklist)
