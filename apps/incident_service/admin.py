from django.contrib import admin
from .models import Incident, IncidentPlaybook, IncidentTimeline, IncidentTemplate

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'status', 'priority_score', 'assigned_to', 'created_at']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

@admin.register(IncidentPlaybook)
class IncidentPlaybookAdmin(admin.ModelAdmin):
    list_display = ['incident', 'title', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']

@admin.register(IncidentTimeline)
class IncidentTimelineAdmin(admin.ModelAdmin):
    list_display = ['incident', 'event_type', 'performed_by', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

@admin.register(IncidentTemplate)
class IncidentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'created_at']
    list_filter = ['severity', 'created_at']
    search_fields = ['name', 'description']
