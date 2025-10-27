from django.contrib import admin
from .models import UserProfile, LoginAttempt, Session

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'last_login_ip', 'last_login_country', 'two_factor_enabled', 'failed_login_attempts']
    list_filter = ['two_factor_enabled', 'created_at']
    search_fields = ['user__username', 'last_login_ip']

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'country', 'success', 'risk_score', 'timestamp']
    list_filter = ['success', 'risk_action', 'timestamp']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['id', 'token']
