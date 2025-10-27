from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import AccessLog, LogAnomaly, LogTimeline
from .serializers import AccessLogSerializer, LogAnomalySerializer, LogTimelineSerializer
from .ai_models import LogAnomalyDetector
from apps.core.models import Alert

class AccessLogViewSet(viewsets.ModelViewSet):
    """Access log management endpoints"""
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['user', 'event_type', 'resource_type', 'status']
    search_fields = ['user__username', 'resource_id', 'error_message']
    ordering_fields = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def recent_logs(self, request):
        """Get recent access logs"""
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        logs = AccessLog.objects.filter(timestamp__gte=since).order_by('-timestamp')[:100]
        serializer = AccessLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_log(self, request):
        """Create a new access log"""
        serializer = AccessLogSerializer(data=request.data)
        if serializer.is_valid():
            log = serializer.save()
            
            # Run anomaly detection
            detector = LogAnomalyDetector()
            anomaly_result = detector.detect_anomaly(log)
            
            if anomaly_result['is_anomaly']:
                LogAnomaly.objects.create(
                    access_log=log,
                    anomaly_type=','.join(anomaly_result['anomaly_types']),
                    severity='high' if anomaly_result['confidence'] > 0.8 else 'medium',
                    confidence_score=anomaly_result['confidence'],
                    description=anomaly_result['reasoning'],
                )
                
                # Create alert
                Alert.objects.create(
                    title='Log Anomaly Detected',
                    description=anomaly_result['reasoning'],
                    severity='high' if anomaly_result['confidence'] > 0.8 else 'medium',
                    source_module='logging_service',
                    metadata={
                        'log_id': str(log.id),
                        'anomaly_types': anomaly_result['anomaly_types'],
                        'confidence': anomaly_result['confidence'],
                    }
                )
            
            return Response(AccessLogSerializer(log).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogAnomalyViewSet(viewsets.ModelViewSet):
    """Log anomaly management endpoints"""
    queryset = LogAnomaly.objects.all()
    serializer_class = LogAnomalySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['severity', 'anomaly_type', 'investigated']
    ordering_fields = ['-detected_at']
    
    @action(detail=True, methods=['post'])
    def mark_investigated(self, request, pk=None):
        """Mark anomaly as investigated"""
        anomaly = self.get_object()
        anomaly.investigated = True
        anomaly.investigation_notes = request.data.get('notes', '')
        anomaly.save()
        
        return Response(LogAnomalySerializer(anomaly).data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get anomaly summary"""
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        anomalies = LogAnomaly.objects.filter(detected_at__gte=since)
        
        summary = {
            'total': anomalies.count(),
            'by_severity': {
                'critical': anomalies.filter(severity='critical').count(),
                'high': anomalies.filter(severity='high').count(),
                'medium': anomalies.filter(severity='medium').count(),
                'low': anomalies.filter(severity='low').count(),
            },
            'investigated': anomalies.filter(investigated=True).count(),
            'uninvestigated': anomalies.filter(investigated=False).count(),
        }
        
        return Response(summary)

class LogTimelineViewSet(viewsets.ModelViewSet):
    """Log timeline management endpoints"""
    queryset = LogTimeline.objects.all()
    serializer_class = LogTimelineSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_timeline(self, request):
        """Create a timeline from related logs"""
        log_ids = request.data.get('log_ids', [])
        title = request.data.get('title', 'Timeline')
        description = request.data.get('description', '')
        
        timeline = LogTimeline.objects.create(
            title=title,
            description=description,
            created_by=request.user,
        )
        
        logs = AccessLog.objects.filter(id__in=log_ids)
        timeline.logs.set(logs)
        
        return Response(LogTimelineSerializer(timeline).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs in timeline"""
        timeline = self.get_object()
        logs = timeline.logs.all().order_by('-timestamp')
        serializer = AccessLogSerializer(logs, many=True)
        return Response(serializer.data)
