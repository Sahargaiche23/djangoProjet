from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AccessLogViewSet, LogAnomalyViewSet, LogTimelineViewSet

router = DefaultRouter()
router.register(r'access-logs', AccessLogViewSet, basename='access-log')
router.register(r'anomalies', LogAnomalyViewSet, basename='anomaly')
router.register(r'timelines', LogTimelineViewSet, basename='timeline')

urlpatterns = router.urls
