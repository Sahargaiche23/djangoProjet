from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole, PermissionRecommendation

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource', 'action', 'created_at']
    list_filter = ['resource', 'action']
    search_fields = ['name', 'description']

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
    list_filter = ['role', 'created_at']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'expires_at']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__username']

@admin.register(PermissionRecommendation)
class PermissionRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'recommendation_type', 'confidence_score', 'status', 'created_at']
    list_filter = ['recommendation_type', 'status', 'created_at']
    search_fields = ['user__username', 'permission__name']
