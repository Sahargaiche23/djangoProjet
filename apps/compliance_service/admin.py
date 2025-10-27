from django.contrib import admin
from .models import ComplianceRule, ComplianceAudit, ComplianceGap, ComplianceReport, AuditSchedule

@admin.register(ComplianceRule)
class ComplianceRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'framework', 'severity', 'created_at']
    list_filter = ['framework', 'severity']
    search_fields = ['name', 'description']

@admin.register(ComplianceAudit)
class ComplianceAuditAdmin(admin.ModelAdmin):
    list_display = ['title', 'framework', 'status', 'compliance_score', 'start_date', 'end_date']
    list_filter = ['framework', 'status', 'start_date']
    search_fields = ['title']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'start_date'

@admin.register(ComplianceGap)
class ComplianceGapAdmin(admin.ModelAdmin):
    list_display = ['audit', 'rule', 'severity', 'status', 'assigned_to', 'due_date']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['gap_description']
    readonly_fields = ['id', 'created_at']

@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ['audit', 'report_type', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    readonly_fields = ['id', 'generated_at']
    date_hierarchy = 'generated_at'

@admin.register(AuditSchedule)
class AuditScheduleAdmin(admin.ModelAdmin):
    list_display = ['framework', 'frequency', 'next_audit_date', 'last_audit_date']
    list_filter = ['framework', 'frequency']
    readonly_fields = ['id', 'created_at']
