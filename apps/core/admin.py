from django.contrib import admin
from .models import AuditLog, Alert, SystemMetric

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'resource_type', 'status', 'timestamp']
    list_filter = ['action', 'status', 'timestamp']
    search_fields = ['user__username', 'resource_id', 'action']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'source_module', 'created_at', 'acknowledged_at']
    list_filter = ['severity', 'source_module', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_name', 'metric_value', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
