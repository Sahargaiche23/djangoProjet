from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import ComplianceRule, ComplianceAudit, ComplianceGap, ComplianceReport, AuditSchedule
from .serializers import ComplianceRuleSerializer, ComplianceAuditSerializer, ComplianceGapSerializer, ComplianceReportSerializer
from .ai_models import ComplianceAuditor
from apps.core.models import AuditLog

class ComplianceRuleViewSet(viewsets.ModelViewSet):
    """Compliance rule management"""
    queryset = ComplianceRule.objects.all()
    serializer_class = ComplianceRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['framework', 'severity']
    search_fields = ['name', 'description']

class ComplianceAuditViewSet(viewsets.ModelViewSet):
    """Compliance audit management"""
    queryset = ComplianceAudit.objects.all()
    serializer_class = ComplianceAuditSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['framework', 'status']
    ordering_fields = ['-created_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auditor = ComplianceAuditor()
    
    def perform_create(self, serializer):
        audit = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            action='create_compliance_audit',
            resource_type='compliance_audit',
            resource_id=str(audit.id),
            status='success',
        )
    
    @action(detail=True, methods=['post'])
    def run_audit(self, request, pk=None):
        """Run compliance audit"""
        audit = self.get_object()
        
        # Get system configuration (mock)
        system_config = {
            'tls_enabled': request.data.get('tls_enabled', True),
            'data_encryption_enabled': request.data.get('data_encryption_enabled', True),
            'rbac_enabled': request.data.get('rbac_enabled', True),
            'mfa_enabled': request.data.get('mfa_enabled', True),
            'mfa_for_admins': request.data.get('mfa_for_admins', True),
            'password_min_length': request.data.get('password_min_length', 12),
            'password_complexity_required': request.data.get('password_complexity_required', True),
            'password_expiration_days': request.data.get('password_expiration_days', 90),
        }
        
        # Get audit logs
        audit_logs = []
        from apps.core.models import AuditLog as CoreAuditLog
        recent_logs = CoreAuditLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).values('timestamp')
        audit_logs = list(recent_logs)
        
        # Run audit
        audit_result = self.auditor.audit_system(audit.framework, system_config, audit_logs)
        
        # Update audit
        audit.status = 'completed'
        audit.compliance_score = audit_result['compliance_score']
        audit.findings = audit_result
        audit.end_date = timezone.now()
        audit.save()
        
        # Create gaps
        for gap_data in audit_result['gaps']:
            rule = ComplianceRule.objects.filter(
                name=gap_data['rule'],
                framework=audit.framework
            ).first()
            
            if rule:
                ComplianceGap.objects.create(
                    audit=audit,
                    rule=rule,
                    gap_description=gap_data['description'],
                    severity=gap_data['severity'],
                    remediation_steps=gap_data['remediation'],
                )
        
        # Generate report
        report_content = self._generate_report(audit, audit_result)
        ComplianceReport.objects.create(
            audit=audit,
            report_type='detailed',
            content=report_content,
            generated_by=request.user,
        )
        
        return Response({
            'compliance_score': audit_result['compliance_score'],
            'gaps_count': len(audit_result['gaps']),
            'passed_checks': len(audit_result['passed_checks']),
            'failed_checks': len(audit_result['failed_checks']),
            'summary': audit_result['summary'],
        })
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Get audit report"""
        audit = self.get_object()
        report = audit.reports.first()
        
        if not report:
            return Response({'error': 'No report generated'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'audit_id': str(audit.id),
            'framework': audit.framework,
            'compliance_score': audit.compliance_score,
            'report': report.content,
            'generated_at': report.generated_at,
        })
    
    @staticmethod
    def _generate_report(audit, audit_result):
        """Generate compliance report"""
        report = f"""
COMPLIANCE AUDIT REPORT
Framework: {audit.framework}
Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
Compliance Score: {audit_result['compliance_score']:.1%}

SUMMARY
{audit_result['summary']}

PASSED CHECKS ({len(audit_result['passed_checks'])})
"""
        for check in audit_result['passed_checks'][:5]:
            report += f"\n✓ {check['rule']}"
        
        report += f"\n\nFAILED CHECKS ({len(audit_result['failed_checks'])})\n"
        for check in audit_result['failed_checks'][:5]:
            report += f"\n✗ {check['rule']}\n  Gap: {check['gap_description']}\n"
        
        report += f"\n\nRECOMMENDATIONS\n"
        for i, rec in enumerate(audit_result['recommendations'], 1):
            report += f"\n{i}. {rec}"
        
        return report

class ComplianceGapViewSet(viewsets.ModelViewSet):
    """Compliance gap management"""
    queryset = ComplianceGap.objects.all()
    serializer_class = ComplianceGapSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['audit', 'severity', 'status']
    ordering_fields = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign gap to user"""
        gap = self.get_object()
        user_id = request.data.get('user_id')
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        gap.assigned_to = user
        gap.status = 'in_progress'
        gap.save()
        
        return Response(ComplianceGapSerializer(gap).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark gap as resolved"""
        gap = self.get_object()
        gap.status = 'resolved'
        gap.save()
        
        return Response(ComplianceGapSerializer(gap).data)

class ComplianceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Compliance report (read-only)"""
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['audit', 'report_type']
    ordering_fields = ['-generated_at']
    
    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """Export report as PDF"""
        report = self.get_object()
        
        return Response({
            'message': 'PDF export functionality would be implemented here',
            'report_id': str(report.id),
        })

class AuditScheduleViewSet(viewsets.ModelViewSet):
    """Audit schedule management"""
    queryset = AuditSchedule.objects.all()
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming audits"""
        schedules = AuditSchedule.objects.filter(
            next_audit_date__gte=timezone.now()
        ).order_by('next_audit_date')[:10]
        
        data = []
        for schedule in schedules:
            data.append({
                'framework': schedule.framework,
                'frequency': schedule.frequency,
                'next_audit_date': schedule.next_audit_date,
                'last_audit_date': schedule.last_audit_date,
            })
        
        return Response(data)
