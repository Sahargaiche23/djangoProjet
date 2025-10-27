import re
from datetime import datetime, timedelta

class ComplianceAuditor:
    """
    Compliance Auditor - Rules engine for compliance verification
    Checks configurations, logs, and policies against compliance rules
    """
    
    def __init__(self):
        self.rules_cache = {}
    
    def audit_system(self, framework, system_config, audit_logs):
        """
        Audit system against compliance framework
        Returns: {
            'compliance_score': float (0-1),
            'gaps': [gap_dict],
            'passed_checks': [check_dict],
            'failed_checks': [check_dict],
            'recommendations': [str],
            'summary': str
        }
        """
        framework_rules = self._get_framework_rules(framework)
        
        passed_checks = []
        failed_checks = []
        gaps = []
        
        for rule in framework_rules:
            check_result = self._check_rule(rule, system_config, audit_logs)
            
            if check_result['passed']:
                passed_checks.append(check_result)
            else:
                failed_checks.append(check_result)
                gaps.append({
                    'rule': rule['name'],
                    'description': check_result['gap_description'],
                    'severity': rule['severity'],
                    'remediation': check_result['remediation'],
                })
        
        total_checks = len(passed_checks) + len(failed_checks)
        compliance_score = len(passed_checks) / total_checks if total_checks > 0 else 0
        
        recommendations = self._generate_recommendations(gaps, system_config)
        summary = self._generate_summary(framework, compliance_score, len(gaps))
        
        return {
            'compliance_score': compliance_score,
            'gaps': gaps,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'recommendations': recommendations,
            'summary': summary,
        }
    
    def _check_rule(self, rule, system_config, audit_logs):
        """Check if system complies with a specific rule"""
        rule_name = rule['name']
        
        # Route to specific check based on rule
        if 'encryption' in rule_name.lower():
            return self._check_encryption(rule, system_config)
        elif 'access' in rule_name.lower():
            return self._check_access_control(rule, system_config)
        elif 'audit' in rule_name.lower():
            return self._check_audit_logging(rule, audit_logs)
        elif 'password' in rule_name.lower():
            return self._check_password_policy(rule, system_config)
        elif 'mfa' in rule_name.lower():
            return self._check_mfa(rule, system_config)
        else:
            return self._check_generic_rule(rule, system_config)
    
    def _check_encryption(self, rule, system_config):
        """Check encryption requirements"""
        has_tls = system_config.get('tls_enabled', False)
        has_data_encryption = system_config.get('data_encryption_enabled', False)
        
        passed = has_tls and has_data_encryption
        
        return {
            'rule': rule['name'],
            'passed': passed,
            'gap_description': 'TLS and data encryption not enabled' if not passed else '',
            'remediation': ['Enable TLS', 'Enable data encryption'] if not passed else [],
        }
    
    def _check_access_control(self, rule, system_config):
        """Check access control requirements"""
        has_rbac = system_config.get('rbac_enabled', False)
        has_mfa = system_config.get('mfa_enabled', False)
        
        passed = has_rbac and has_mfa
        
        return {
            'rule': rule['name'],
            'passed': passed,
            'gap_description': 'RBAC or MFA not properly configured' if not passed else '',
            'remediation': ['Implement RBAC', 'Enable MFA'] if not passed else [],
        }
    
    def _check_audit_logging(self, rule, audit_logs):
        """Check audit logging requirements"""
        if not audit_logs:
            return {
                'rule': rule['name'],
                'passed': False,
                'gap_description': 'No audit logs found',
                'remediation': ['Enable audit logging', 'Ensure logs are being collected'],
            }
        
        # Check if logs are recent
        latest_log = max(log.get('timestamp', datetime.now()) for log in audit_logs)
        hours_since_log = (datetime.now() - latest_log).total_seconds() / 3600
        
        passed = hours_since_log < 24
        
        return {
            'rule': rule['name'],
            'passed': passed,
            'gap_description': f'Audit logs not recent (last log {hours_since_log:.1f} hours ago)' if not passed else '',
            'remediation': ['Check logging system', 'Verify log collection'] if not passed else [],
        }
    
    def _check_password_policy(self, rule, system_config):
        """Check password policy requirements"""
        min_length = system_config.get('password_min_length', 0)
        requires_complexity = system_config.get('password_complexity_required', False)
        expiration_days = system_config.get('password_expiration_days', 0)
        
        passed = min_length >= 12 and requires_complexity and expiration_days > 0
        
        return {
            'rule': rule['name'],
            'passed': passed,
            'gap_description': 'Password policy not meeting requirements' if not passed else '',
            'remediation': [
                'Set minimum password length to 12',
                'Require password complexity',
                'Set password expiration to 90 days'
            ] if not passed else [],
        }
    
    def _check_mfa(self, rule, system_config):
        """Check MFA requirements"""
        mfa_enabled = system_config.get('mfa_enabled', False)
        mfa_for_admins = system_config.get('mfa_for_admins', False)
        
        passed = mfa_enabled and mfa_for_admins
        
        return {
            'rule': rule['name'],
            'passed': passed,
            'gap_description': 'MFA not properly configured' if not passed else '',
            'remediation': ['Enable MFA globally', 'Require MFA for admin accounts'] if not passed else [],
        }
    
    def _check_generic_rule(self, rule, system_config):
        """Generic rule check"""
        return {
            'rule': rule['name'],
            'passed': True,
            'gap_description': '',
            'remediation': [],
        }
    
    def _get_framework_rules(self, framework):
        """Get rules for a specific framework"""
        rules = {
            'gdpr': [
                {'name': 'Data Encryption', 'severity': 'critical'},
                {'name': 'Access Control', 'severity': 'critical'},
                {'name': 'Audit Logging', 'severity': 'high'},
                {'name': 'Data Retention Policy', 'severity': 'high'},
                {'name': 'User Consent Management', 'severity': 'high'},
            ],
            'hipaa': [
                {'name': 'Encryption', 'severity': 'critical'},
                {'name': 'Access Control', 'severity': 'critical'},
                {'name': 'Audit Logging', 'severity': 'critical'},
                {'name': 'Password Policy', 'severity': 'high'},
                {'name': 'MFA', 'severity': 'high'},
            ],
            'pci_dss': [
                {'name': 'Encryption', 'severity': 'critical'},
                {'name': 'Access Control', 'severity': 'critical'},
                {'name': 'Audit Logging', 'severity': 'critical'},
                {'name': 'Password Policy', 'severity': 'high'},
                {'name': 'MFA', 'severity': 'high'},
            ],
            'iso27001': [
                {'name': 'Access Control', 'severity': 'high'},
                {'name': 'Encryption', 'severity': 'high'},
                {'name': 'Audit Logging', 'severity': 'high'},
                {'name': 'Incident Management', 'severity': 'high'},
                {'name': 'Business Continuity', 'severity': 'medium'},
            ],
        }
        
        return rules.get(framework, [])
    
    def _generate_recommendations(self, gaps, system_config):
        """Generate remediation recommendations"""
        recommendations = []
        
        critical_gaps = [g for g in gaps if g['severity'] == 'critical']
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical compliance gaps immediately")
        
        for gap in gaps[:3]:  # Top 3 gaps
            recommendations.extend(gap['remediation'])
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_summary(self, framework, compliance_score, gap_count):
        """Generate compliance summary"""
        score_pct = int(compliance_score * 100)
        
        if compliance_score >= 0.9:
            status = "Compliant"
        elif compliance_score >= 0.7:
            status = "Mostly Compliant"
        else:
            status = "Non-Compliant"
        
        return f"{framework} Compliance: {score_pct}% ({status}) - {gap_count} gaps identified"
    
    def generate_checklist(self, framework):
        """Generate compliance checklist"""
        rules = self._get_framework_rules(framework)
        
        checklist = []
        for rule in rules:
            checklist.append({
                'item': rule['name'],
                'severity': rule['severity'],
                'checked': False,
                'notes': '',
            })
        
        return checklist
