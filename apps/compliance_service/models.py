from django.db import models
from django.contrib.auth.models import User
import uuid

class ComplianceRule(models.Model):
    """Compliance rules and requirements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    framework = models.CharField(max_length=100, choices=[
        ('gdpr', 'GDPR'),
        ('hipaa', 'HIPAA'),
        ('pci_dss', 'PCI DSS'),
        ('iso27001', 'ISO 27001'),
        ('soc2', 'SOC 2'),
    ])
    rule_text = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['framework', 'name']
        unique_together = ['framework', 'name']

class ComplianceAudit(models.Model):
    """Compliance audit records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    framework = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='scheduled')
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    findings = models.JSONField(default=list)
    compliance_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class ComplianceGap(models.Model):
    """Identified compliance gaps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(ComplianceAudit, on_delete=models.CASCADE, related_name='gaps')
    rule = models.ForeignKey(ComplianceRule, on_delete=models.CASCADE)
    gap_description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ])
    remediation_steps = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ], default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_gaps')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class ComplianceReport(models.Model):
    """Generated compliance reports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(ComplianceAudit, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=100, choices=[
        ('summary', 'Summary'),
        ('detailed', 'Detailed'),
        ('executive', 'Executive'),
    ])
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-generated_at']

class AuditSchedule(models.Model):
    """Audit scheduling"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.CharField(max_length=100)
    frequency = models.CharField(max_length=50, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ])
    next_audit_date = models.DateTimeField()
    last_audit_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['next_audit_date']
        unique_together = ['framework', 'frequency']
