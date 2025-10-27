from django.contrib import admin
from .models import AccessLog, LogAnomaly, LogTimeline

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'resource_type', 'action', 'status', 'timestamp']
    list_filter = ['event_type', 'resource_type', 'status', 'timestamp']
    search_fields = ['user__username', 'resource_id', 'error_message']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(LogAnomaly)
class LogAnomalyAdmin(admin.ModelAdmin):
    list_display = ['access_log', 'anomaly_type', 'severity', 'confidence_score', 'investigated', 'detected_at']
    list_filter = ['severity', 'anomaly_type', 'investigated', 'detected_at']
    readonly_fields = ['id', 'detected_at']
    date_hierarchy = 'detected_at'

@admin.register(LogTimeline)
class LogTimelineAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']
