from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Role, Permission, UserRole, PermissionRecommendation
from .serializers import RoleSerializer, PermissionSerializer, UserRoleSerializer
from .ai_models import PolicyOptimizer
from apps.core.models import AuditLog
from apps.logging_service.models import AccessLog

class RoleViewSet(viewsets.ModelViewSet):
    """Role management endpoints"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        AuditLog.objects.create(
            user=self.request.user,
            action='create_role',
            resource_type='role',
            resource_id=str(serializer.validated_data['name']),
            status='success',
        )
        serializer.save()

class PermissionViewSet(viewsets.ModelViewSet):
    """Permission management endpoints"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

class UserRoleViewSet(viewsets.ModelViewSet):
    """User role assignment endpoints"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def assign_role(self, request):
        """Assign role to user"""
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        
        try:
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)
        except (User.DoesNotExist, Role.DoesNotExist):
            return Response({'error': 'User or role not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user_role, created = UserRole.objects.get_or_create(user=user, role=role)
        
        AuditLog.objects.create(
            user=request.user,
            action='assign_role',
            resource_type='user_role',
            resource_id=f"{user.id}_{role.id}",
            changes={'role': role.name},
            status='success',
        )
        
        return Response(UserRoleSerializer(user_role).data)
    
    @action(detail=False, methods=['post'])
    def revoke_role(self, request):
        """Revoke role from user"""
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')
        
        try:
            UserRole.objects.get(user_id=user_id, role_id=role_id).delete()
        except UserRole.DoesNotExist:
            return Response({'error': 'User role not found'}, status=status.HTTP_404_NOT_FOUND)
        
        AuditLog.objects.create(
            user=request.user,
            action='revoke_role',
            resource_type='user_role',
            resource_id=f"{user_id}_{role_id}",
            status='success',
        )
        
        return Response({'message': 'Role revoked'})

class PolicyOptimizerViewSet(viewsets.ViewSet):
    """Policy optimization endpoints"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.optimizer = PolicyOptimizer()
    
    @action(detail=False, methods=['post'])
    def analyze_user_permissions(self, request):
        """Analyze user permissions and generate recommendations"""
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get user permissions
        user_roles = UserRole.objects.filter(user=user)
        permissions = Permission.objects.filter(
            rolepermission__role__in=[ur.role for ur in user_roles]
        ).distinct()
        
        # Get access logs
        access_logs = AccessLog.objects.filter(user=user)
        
        # Get recommendations
        recommendations = self.optimizer.recommend_permissions(user, permissions, access_logs)
        
        # Create recommendation records
        for perm in recommendations['grant_recommendations']:
            PermissionRecommendation.objects.create(
                user=user,
                permission=perm,
                recommendation_type='grant',
                confidence_score=recommendations['confidence_scores']['grant'],
                reasoning='User needs this permission based on access patterns',
            )
        
        for perm_data in recommendations['revoke_recommendations']:
            PermissionRecommendation.objects.create(
                user=user,
                permission=perm_data['permission'],
                recommendation_type='revoke',
                confidence_score=0.85,
                reasoning=perm_data['reason'],
            )
        
        return Response({
            'user_id': user_id,
            'recommendations': {
                'grant_count': len(recommendations['grant_recommendations']),
                'revoke_count': len(recommendations['revoke_recommendations']),
                'review_count': len(recommendations['review_recommendations']),
            },
            'reasoning': recommendations['reasoning'],
        })
    
    @action(detail=False, methods=['get'])
    def get_recommendations(self, request):
        """Get pending recommendations for current user"""
        recommendations = PermissionRecommendation.objects.filter(status='pending')
        
        data = []
        for rec in recommendations:
            data.append({
                'id': rec.id,
                'user': rec.user.username,
                'permission': rec.permission.name,
                'type': rec.recommendation_type,
                'confidence': rec.confidence_score,
                'reasoning': rec.reasoning,
            })
        
        return Response(data)
