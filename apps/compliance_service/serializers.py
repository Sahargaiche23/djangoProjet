from rest_framework import serializers
from .models import ComplianceRule, ComplianceAudit, ComplianceGap, ComplianceReport

class ComplianceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRule
        fields = ['id', 'name', 'description', 'framework', 'rule_text', 'severity', 'created_at']

class ComplianceAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceAudit
        fields = ['id', 'title', 'framework', 'start_date', 'end_date', 'status', 
                  'conducted_by', 'findings', 'compliance_score', 'created_at']

class ComplianceGapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceGap
        fields = ['id', 'audit', 'rule', 'gap_description', 'severity', 'remediation_steps', 
                  'status', 'assigned_to', 'due_date', 'created_at']

class ComplianceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceReport
        fields = ['id', 'audit', 'report_type', 'content', 'generated_at', 'generated_by']
