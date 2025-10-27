#!/bin/bash

echo "=== Security Platform Initialization ==="

# Wait for database
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created: admin / admin123")
else:
    print("Superuser already exists")
END

# Create initial roles
echo "Creating initial roles..."
python manage.py shell << END
from apps.rbac_service.models import Role, Permission, RolePermission

roles_data = [
    {'name': 'Admin', 'description': 'Administrator with full access'},
    {'name': 'Security Officer', 'description': 'Security operations and monitoring'},
    {'name': 'Compliance Officer', 'description': 'Compliance and audit management'},
    {'name': 'User', 'description': 'Regular user'},
]

for role_data in roles_data:
    role, created = Role.objects.get_or_create(
        name=role_data['name'],
        defaults={'description': role_data['description']}
    )
    if created:
        print(f"Created role: {role.name}")
    else:
        print(f"Role already exists: {role.name}")

# Create permissions
permissions_data = [
    {'name': 'view_logs', 'resource': 'logs', 'action': 'view'},
    {'name': 'create_incident', 'resource': 'incidents', 'action': 'create'},
    {'name': 'manage_users', 'resource': 'users', 'action': 'manage'},
    {'name': 'run_audit', 'resource': 'compliance', 'action': 'audit'},
]

for perm_data in permissions_data:
    perm, created = Permission.objects.get_or_create(
        name=perm_data['name'],
        defaults={'resource': perm_data['resource'], 'action': perm_data['action']}
    )
    if created:
        print(f"Created permission: {perm.name}")

# Assign permissions to Admin role
admin_role = Role.objects.get(name='Admin')
for perm in Permission.objects.all():
    RolePermission.objects.get_or_create(role=admin_role, permission=perm)
print("Assigned all permissions to Admin role")
END

# Create compliance rules
echo "Creating compliance rules..."
python manage.py shell << END
from apps.compliance_service.models import ComplianceRule

rules_data = [
    {'name': 'Data Encryption', 'framework': 'gdpr', 'severity': 'critical'},
    {'name': 'Access Control', 'framework': 'gdpr', 'severity': 'critical'},
    {'name': 'Audit Logging', 'framework': 'gdpr', 'severity': 'high'},
    {'name': 'Encryption', 'framework': 'hipaa', 'severity': 'critical'},
    {'name': 'MFA', 'framework': 'pci_dss', 'severity': 'high'},
]

for rule_data in rules_data:
    rule, created = ComplianceRule.objects.get_or_create(
        name=rule_data['name'],
        framework=rule_data['framework'],
        defaults={'severity': rule_data['severity'], 'rule_text': f"Rule: {rule_data['name']}"}
    )
    if created:
        print(f"Created rule: {rule.name} ({rule.framework})")
END

# Create audit schedules
echo "Creating audit schedules..."
python manage.py shell << END
from apps.compliance_service.models import AuditSchedule
from django.utils import timezone
from datetime import timedelta

frameworks = ['gdpr', 'hipaa', 'pci_dss', 'iso27001']
for framework in frameworks:
    schedule, created = AuditSchedule.objects.get_or_create(
        framework=framework,
        frequency='quarterly',
        defaults={'next_audit_date': timezone.now() + timedelta(days=90)}
    )
    if created:
        print(f"Created audit schedule: {framework}")
END

echo "=== Initialization Complete ==="
echo "Admin credentials: admin / admin123"
echo "Access the platform at: http://localhost:8000"
echo "Admin panel at: http://localhost:8000/admin"
