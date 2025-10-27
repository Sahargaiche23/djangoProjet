from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Alert, AuditLog
from apps.logging_service.models import AccessLog, LogAnomaly
from apps.logging_service.ai_models import LogAnomalyDetector
from apps.incident_service.models import Incident
import logging

logger = logging.getLogger(__name__)

@shared_task
def detect_log_anomalies():
    """Detect anomalies in recent logs"""
    detector = LogAnomalyDetector()
    
    # Get recent logs without anomalies
    recent_logs = AccessLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1),
        anomalies__isnull=True
    )[:100]
    
    anomaly_count = 0
    for log in recent_logs:
        result = detector.detect_anomaly(log)
        
        if result['is_anomaly']:
            LogAnomaly.objects.create(
                access_log=log,
                anomaly_type=','.join(result['anomaly_types']),
                severity='high' if result['confidence'] > 0.8 else 'medium',
                confidence_score=result['confidence'],
                description=result['reasoning'],
            )
            
            Alert.objects.create(
                title='Log Anomaly Detected',
                description=result['reasoning'],
                severity='high' if result['confidence'] > 0.8 else 'medium',
                source_module='logging_service',
                metadata={
                    'log_id': str(log.id),
                    'anomaly_types': result['anomaly_types'],
                }
            )
            
            anomaly_count += 1
    
    logger.info(f"Detected {anomaly_count} anomalies")
    return anomaly_count

@shared_task
def cleanup_old_logs():
    """Clean up old audit logs (older than 90 days)"""
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
    logger.info(f"Deleted {deleted_count} old audit logs")
    return deleted_count

@shared_task
def generate_daily_security_report():
    """Generate daily security report"""
    from apps.core.models import Alert
    
    today = timezone.now().date()
    alerts = Alert.objects.filter(created_at__date=today)
    
    report = {
        'date': str(today),
        'total_alerts': alerts.count(),
        'by_severity': {
            'critical': alerts.filter(severity='critical').count(),
            'high': alerts.filter(severity='high').count(),
            'medium': alerts.filter(severity='medium').count(),
            'low': alerts.filter(severity='low').count(),
        },
        'acknowledged': alerts.filter(acknowledged_at__isnull=False).count(),
    }
    
    logger.info(f"Daily report: {report}")
    return report

@shared_task
def check_incident_slas():
    """Check incident SLA compliance"""
    from apps.incident_service.models import Incident
    
    critical_incidents = Incident.objects.filter(
        severity='critical',
        status__in=['open', 'investigating']
    )
    
    sla_breaches = 0
    for incident in critical_incidents:
        hours_open = (timezone.now() - incident.created_at).total_seconds() / 3600
        if hours_open > 4:  # 4-hour SLA for critical
            Alert.objects.create(
                title='Critical Incident SLA Breach',
                description=f"Incident {incident.id} open for {hours_open:.1f} hours",
                severity='critical',
                source_module='incident_service',
            )
            sla_breaches += 1
    
    logger.warning(f"SLA breaches: {sla_breaches}")
    return sla_breaches

@shared_task
def unlock_accounts():
    """Unlock accounts after lockout period"""
    from apps.auth_service.models import UserProfile
    
    unlocked = UserProfile.objects.filter(
        account_locked_until__lte=timezone.now()
    ).update(account_locked_until=None)
    
    logger.info(f"Unlocked {unlocked} accounts")
    return unlocked

@shared_task
def sync_compliance_schedules():
    """Sync compliance audit schedules"""
    from apps.compliance_service.models import AuditSchedule, ComplianceAudit
    
    schedules = AuditSchedule.objects.filter(
        next_audit_date__lte=timezone.now()
    )
    
    created_count = 0
    for schedule in schedules:
        # Create audit
        audit = ComplianceAudit.objects.create(
            title=f"{schedule.framework} Audit",
            framework=schedule.framework,
            start_date=timezone.now(),
            status='scheduled',
        )
        
        # Update schedule
        schedule.last_audit_date = timezone.now()
        
        # Calculate next audit date
        from dateutil.relativedelta import relativedelta
        frequency_map = {
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'semi_annual': relativedelta(months=6),
            'annual': relativedelta(years=1),
        }
        
        delta = frequency_map.get(schedule.frequency, relativedelta(months=1))
        schedule.next_audit_date = timezone.now() + delta
        schedule.save()
        
        created_count += 1
    
    logger.info(f"Created {created_count} compliance audits")
    return created_count
