from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import requests
from .models import UserProfile, LoginAttempt, Session
from .serializers import UserProfileSerializer, LoginAttemptSerializer
from .ai_models import AuthRiskScorer
from apps.core.models import AuditLog, Alert
from apps.incident_service.models import Incident

class AuthViewSet(viewsets.ViewSet):
    """Authentication service endpoints"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.risk_scorer = AuthRiskScorer()
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login endpoint with risk assessment"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Missing credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        # Check if account is locked
        if profile.account_locked_until and profile.account_locked_until > timezone.now():
            return Response({'error': 'Account locked'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get client IP and geolocation
        client_ip = self._get_client_ip(request)
        geo_data = self._get_geolocation(client_ip)
        
        # Check device fingerprint
        device_fingerprint = request.data.get('device_fingerprint', '')
        device_seen_before = device_fingerprint == profile.device_fingerprint if profile.device_fingerprint else False
        
        # Calculate geo distance
        geo_distance = self._calculate_geo_distance(
            profile.last_login_country,
            geo_data.get('country', '')
        ) if profile.last_login_country else 0
        
        # Count failed attempts in last 24h
        failed_24h = LoginAttempt.objects.filter(
            user=user,
            success=False,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Calculate account age
        account_age_days = (timezone.now() - user.date_joined).days
        
        # Prepare risk assessment data
        risk_data = {
            'timestamp': timezone.now(),
            'ip_risk_score': geo_data.get('risk_score', 0.0),
            'failed_attempts_24h': failed_24h,
            'account_age_days': account_age_days,
            'geo_distance_km': geo_distance,
            'device_seen_before': device_seen_before,
            'behavior_score': 0.5,
        }
        
        # Get risk assessment
        risk_assessment = self.risk_scorer.predict_risk(risk_data)
        
        # Verify password
        if not user.check_password(password):
            profile.failed_login_attempts += 1
            if profile.failed_login_attempts >= 5:
                profile.account_locked_until = timezone.now() + timedelta(hours=1)
            profile.save()
            
            # Log failed attempt
            LoginAttempt.objects.create(
                user=user,
                ip_address=client_ip,
                country=geo_data.get('country', ''),
                device_fingerprint=device_fingerprint,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=False,
                risk_score=risk_assessment['risk_score'],
            )
            
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check risk action
        if risk_assessment['action'] == 'block':
            # Create alert
            Alert.objects.create(
                title='Suspicious Login Attempt Blocked',
                description=f"Login attempt from {client_ip} ({geo_data.get('country', 'Unknown')}) blocked due to high risk",
                severity='high',
                source_module='auth_service',
                metadata={
                    'user_id': user.id,
                    'ip_address': client_ip,
                    'risk_score': risk_assessment['risk_score'],
                    'reasoning': risk_assessment['reasoning'],
                }
            )
            
            # Create incident
            Incident.objects.create(
                title='Blocked Login Attempt',
                description=risk_assessment['reasoning'],
                severity='high',
                status='open',
                assigned_to=None,
            )
            
            return Response({
                'error': 'Login blocked due to security concerns',
                'action': 'contact_support'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reset failed attempts
        profile.failed_login_attempts = 0
        profile.last_login_ip = client_ip
        profile.last_login_country = geo_data.get('country', '')
        profile.last_login_timestamp = timezone.now()
        profile.device_fingerprint = device_fingerprint
        profile.save()
        
        # Create session
        session = Session.objects.create(
            user=user,
            token=self._generate_token(),
            ip_address=client_ip,
            device_fingerprint=device_fingerprint,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Log successful login
        LoginAttempt.objects.create(
            user=user,
            ip_address=client_ip,
            country=geo_data.get('country', ''),
            device_fingerprint=device_fingerprint,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True,
            risk_score=risk_assessment['risk_score'],
            risk_action=risk_assessment['action'],
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='login',
            resource_type='user',
            resource_id=str(user.id),
            ip_address=client_ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
        )
        
        return Response({
            'token': session.token,
            'user_id': user.id,
            'username': user.username,
            'risk_assessment': risk_assessment,
            'requires_2fa': risk_assessment['action'] == 'step_up_2fa',
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout endpoint"""
        token = request.auth
        Session.objects.filter(token=str(token)).update(is_active=False)
        
        AuditLog.objects.create(
            user=request.user,
            action='logout',
            resource_type='user',
            resource_id=str(request.user.id),
            ip_address=self._get_client_ip(request),
            status='success',
        )
        
        return Response({'message': 'Logged out successfully'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get user profile"""
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _get_geolocation(ip_address):
        """Get geolocation data for IP (mock implementation)"""
        try:
            response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=2)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', ''),
                    'latitude': data.get('latitude', 0),
                    'longitude': data.get('longitude', 0),
                    'risk_score': 0.1,  # Mock risk score
                }
        except Exception:
            pass
        
        return {'country': 'Unknown', 'latitude': 0, 'longitude': 0, 'risk_score': 0.0}
    
    @staticmethod
    def _calculate_geo_distance(country1, country2):
        """Calculate approximate distance between countries (mock)"""
        if not country1 or not country2 or country1 == country2:
            return 0
        return 5000  # Mock distance
    
    @staticmethod
    def _generate_token():
        """Generate secure token"""
        import secrets
        return secrets.token_urlsafe(32)
