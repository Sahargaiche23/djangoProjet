from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import IncidentViewSet, IncidentPlaybookViewSet, IncidentTimelineViewSet

router = DefaultRouter()
router.register(r'', IncidentViewSet, basename='incident')
router.register(r'playbooks', IncidentPlaybookViewSet, basename='playbook')
router.register(r'timeline', IncidentTimelineViewSet, basename='timeline')

urlpatterns = router.urls
