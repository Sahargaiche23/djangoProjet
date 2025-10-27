from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.views.generic import TemplateView

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('apps.auth_service.urls')),
    path('api/rbac/', include('apps.rbac_service.urls')),
    path('api/logging/', include('apps.logging_service.urls')),
    path('api/incidents/', include('apps.incident_service.urls')),
    path('api/compliance/', include('apps.compliance_service.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', TemplateView.as_view(template_name='index.html')),
]
