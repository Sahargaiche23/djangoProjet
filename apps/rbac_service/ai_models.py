import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pickle
import os

class PolicyOptimizer:
    """
    Policy Optimizer - ML model for permission recommendations
    Uses clustering and embeddings to suggest permission minimization
    """
    
    def __init__(self):
        self.kmeans = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=10)
        self.model_path = 'ml_models/policy_optimizer.pkl'
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or train a new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.kmeans = pickle.load(f)
                return
            except Exception:
                pass
        
        self._train_default_model()
    
    def _train_default_model(self):
        """Train model with synthetic data"""
        np.random.seed(42)
        n_samples = 500
        
        # Simulate user-permission access patterns
        X = np.random.randn(n_samples, 20)
        
        self.kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        self.kmeans.fit(X)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.kmeans, f)
    
    def extract_user_features(self, user_permissions, access_logs):
        """Extract user behavior features"""
        features = {
            'num_permissions': len(user_permissions),
            'permission_diversity': len(set(p.resource for p in user_permissions)),
            'avg_permission_age': self._calculate_avg_age(user_permissions),
            'access_frequency': len(access_logs),
            'resource_diversity': len(set(log.resource_type for log in access_logs)),
            'error_rate': self._calculate_error_rate(access_logs),
            'unusual_access_patterns': self._detect_unusual_patterns(access_logs),
        }
        return features
    
    def recommend_permissions(self, user, user_permissions, access_logs):
        """
        Generate permission recommendations
        Returns: {
            'grant_recommendations': [...],
            'revoke_recommendations': [...],
            'review_recommendations': [...],
            'reasoning': str
        }
        """
        features = self.extract_user_features(user_permissions, access_logs)
        
        # Identify unused permissions
        used_resources = set(log.resource_type for log in access_logs)
        unused_permissions = [p for p in user_permissions if p.resource not in used_resources]
        
        # Identify over-privileged permissions
        over_privileged = self._identify_over_privileged(user_permissions, access_logs)
        
        # Identify missing permissions
        missing_permissions = self._identify_missing_permissions(user, access_logs)
        
        recommendations = {
            'grant_recommendations': missing_permissions,
            'revoke_recommendations': unused_permissions,
            'review_recommendations': over_privileged,
            'reasoning': self._generate_reasoning(features, unused_permissions, over_privileged),
            'confidence_scores': {
                'grant': 0.75,
                'revoke': 0.85,
                'review': 0.70,
            }
        }
        
        return recommendations
    
    def _identify_over_privileged(self, user_permissions, access_logs):
        """Identify permissions that are rarely or never used"""
        permission_usage = {}
        for log in access_logs:
            permission_usage[log.resource_type] = permission_usage.get(log.resource_type, 0) + 1
        
        over_privileged = []
        for perm in user_permissions:
            usage_count = permission_usage.get(perm.resource, 0)
            if usage_count == 0:
                over_privileged.append({
                    'permission': perm,
                    'reason': 'Never used',
                    'confidence': 0.9
                })
            elif usage_count < 5:
                over_privileged.append({
                    'permission': perm,
                    'reason': f'Rarely used ({usage_count} times)',
                    'confidence': 0.6
                })
        
        return over_privileged
    
    def _identify_missing_permissions(self, user, access_logs):
        """Identify permissions that user needs but doesn't have"""
        # Simplified: look for denied access attempts
        missing = []
        
        # This would typically query for failed access attempts
        # For now, return empty list
        
        return missing
    
    def _calculate_avg_age(self, permissions):
        """Calculate average age of permissions"""
        if not permissions:
            return 0
        from django.utils import timezone
        from datetime import timedelta
        
        total_age = 0
        for perm in permissions:
            age = (timezone.now() - perm.created_at).days
            total_age += age
        
        return total_age / len(permissions)
    
    def _calculate_error_rate(self, access_logs):
        """Calculate error rate in access logs"""
        if not access_logs:
            return 0
        
        errors = sum(1 for log in access_logs if log.status == 'failure')
        return errors / len(access_logs)
    
    def _detect_unusual_patterns(self, access_logs):
        """Detect unusual access patterns"""
        if len(access_logs) < 10:
            return 0
        
        # Simplified: check for access outside business hours
        from django.utils import timezone
        unusual_count = 0
        
        for log in access_logs[-100:]:  # Check last 100 logs
            hour = log.timestamp.hour
            if hour < 6 or hour > 22:
                unusual_count += 1
        
        return unusual_count / min(100, len(access_logs))
    
    def _generate_reasoning(self, features, unused, over_privileged):
        """Generate human-readable reasoning"""
        reasons = []
        
        if unused:
            reasons.append(f"Found {len(unused)} unused permissions")
        
        if over_privileged:
            reasons.append(f"Identified {len(over_privileged)} over-privileged permissions")
        
        if features['error_rate'] > 0.1:
            reasons.append(f"High error rate ({features['error_rate']:.1%})")
        
        if features['unusual_access_patterns'] > 0.2:
            reasons.append("Unusual access patterns detected")
        
        if not reasons:
            reasons.append("Permissions appear appropriate for user role")
        
        return "; ".join(reasons)
