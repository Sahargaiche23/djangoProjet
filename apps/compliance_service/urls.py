from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ComplianceRuleViewSet, ComplianceAuditViewSet, ComplianceGapViewSet,
    ComplianceReportViewSet, AuditScheduleViewSet
)

router = DefaultRouter()
router.register(r'rules', ComplianceRuleViewSet, basename='rule')
router.register(r'audits', ComplianceAuditViewSet, basename='audit')
router.register(r'gaps', ComplianceGapViewSet, basename='gap')
router.register(r'reports', ComplianceReportViewSet, basename='report')
router.register(r'schedules', AuditScheduleViewSet, basename='schedule')

urlpatterns = router.urls
