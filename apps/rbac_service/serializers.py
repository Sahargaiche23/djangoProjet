from rest_framework import serializers
from .models import Role, Permission, UserRole, PermissionRecommendation

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'description', 'resource', 'action']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'assigned_at', 'expires_at']

class PermissionRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionRecommendation
        fields = ['id', 'user', 'permission', 'recommendation_type', 'confidence_score', 'reasoning', 'status']
