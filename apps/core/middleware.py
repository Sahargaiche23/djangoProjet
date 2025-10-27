from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
import json

class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to capture all requests for audit logging"""
    
    def process_request(self, request):
        request.audit_data = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'audit_data') and request.user.is_authenticated:
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action=f"{request.method} {request.path}",
                    resource_type='http_request',
                    resource_id=request.path,
                    ip_address=request.audit_data['ip_address'],
                    user_agent=request.audit_data['user_agent'],
                    status='success' if response.status_code < 400 else 'failure',
                )
            except Exception:
                pass
        return response
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
