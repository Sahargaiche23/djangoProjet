import numpy as np
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle
import os

class TriageAssistant:
    """
    Triage Assistant - ML model for incident prioritization and playbook suggestion
    Predicts priority level and suggests appropriate response playbooks
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.model_path = 'ml_models/triage_assistant.pkl'
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or train a new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                return
            except Exception:
                pass
        
        self._train_default_model()
    
    def _train_default_model(self):
        """Train model with synthetic data"""
        np.random.seed(42)
        n_samples = 500
        
        X = np.random.randn(n_samples, 10)
        y = np.random.randint(0, 4, n_samples)  # 4 priority levels
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )
        self.model.fit(X, y)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def extract_incident_features(self, incident_data):
        """Extract features from incident"""
        features = {
            'num_affected_assets': len(incident_data.get('affected_assets', [])),
            'severity_numeric': self._encode_severity(incident_data.get('severity', 'low')),
            'has_data_breach': 1 if 'data' in incident_data.get('description', '').lower() else 0,
            'has_service_impact': 1 if 'service' in incident_data.get('description', '').lower() else 0,
            'has_security_threat': 1 if 'threat' in incident_data.get('description', '').lower() else 0,
            'description_length': len(incident_data.get('description', '')),
            'num_keywords': self._count_keywords(incident_data.get('description', '')),
            'is_automated_alert': 1 if incident_data.get('source') == 'automated' else 0,
            'time_to_detect': incident_data.get('time_to_detect', 0),
            'affected_users': incident_data.get('affected_users', 0),
        }
        return features
    
    def triage_incident(self, incident_data):
        """
        Triage incident and generate recommendations
        Returns: {
            'priority_score': float (0-1),
            'priority_level': str,
            'suggested_playbooks': [str],
            'recommended_actions': [str],
            'reasoning': str,
            'estimated_resolution_time': int (minutes)
        }
        """
        features = self.extract_incident_features(incident_data)
        feature_vector = np.array([list(features.values())])
        
        # Predict priority
        prediction = self.model.predict(feature_vector)[0]
        probabilities = self.model.predict_proba(feature_vector)[0]
        
        priority_map = {0: 'low', 1: 'medium', 2: 'high', 3: 'critical'}
        priority_level = priority_map[prediction]
        priority_score = float(probabilities[prediction])
        
        # Suggest playbooks
        suggested_playbooks = self._suggest_playbooks(incident_data, priority_level)
        
        # Recommend actions
        recommended_actions = self._recommend_actions(incident_data, priority_level)
        
        # Estimate resolution time
        estimated_time = self._estimate_resolution_time(priority_level, features)
        
        reasoning = self._generate_reasoning(incident_data, priority_level, features)
        
        return {
            'priority_score': priority_score,
            'priority_level': priority_level,
            'suggested_playbooks': suggested_playbooks,
            'recommended_actions': recommended_actions,
            'reasoning': reasoning,
            'estimated_resolution_time': estimated_time,
        }
    
    def _suggest_playbooks(self, incident_data, priority_level):
        """Suggest appropriate playbooks"""
        playbooks = []
        description = incident_data.get('description', '').lower()
        
        if 'login' in description or 'auth' in description:
            playbooks.append('authentication_incident')
        
        if 'data' in description or 'breach' in description:
            playbooks.append('data_breach_response')
        
        if 'malware' in description or 'virus' in description:
            playbooks.append('malware_containment')
        
        if 'ddos' in description or 'attack' in description:
            playbooks.append('ddos_mitigation')
        
        if 'service' in description or 'outage' in description:
            playbooks.append('service_restoration')
        
        if priority_level == 'critical':
            playbooks.insert(0, 'critical_incident_response')
        
        return playbooks[:3]  # Return top 3
    
    def _recommend_actions(self, incident_data, priority_level):
        """Recommend immediate actions"""
        actions = []
        
        if priority_level in ['critical', 'high']:
            actions.append('Notify incident commander')
            actions.append('Activate war room')
        
        if 'data' in incident_data.get('description', '').lower():
            actions.append('Isolate affected systems')
            actions.append('Preserve evidence')
        
        if 'auth' in incident_data.get('description', '').lower():
            actions.append('Force password reset for affected users')
            actions.append('Review access logs')
        
        if priority_level == 'critical':
            actions.append('Escalate to executive team')
            actions.append('Prepare public statement')
        
        return actions
    
    def _estimate_resolution_time(self, priority_level, features):
        """Estimate resolution time in minutes"""
        base_times = {
            'critical': 30,
            'high': 120,
            'medium': 480,
            'low': 1440,
        }
        
        base_time = base_times.get(priority_level, 480)
        
        # Adjust based on complexity
        complexity_factor = features['num_affected_assets'] * 10 + features['num_keywords'] * 5
        
        return int(base_time + complexity_factor)
    
    def _generate_reasoning(self, incident_data, priority_level, features):
        """Generate human-readable reasoning"""
        reasons = []
        
        if features['num_affected_assets'] > 5:
            reasons.append(f"Multiple assets affected ({features['num_affected_assets']})")
        
        if features['has_data_breach']:
            reasons.append("Potential data breach detected")
        
        if features['has_security_threat']:
            reasons.append("Security threat indicators present")
        
        if features['affected_users'] > 100:
            reasons.append(f"Large number of users affected ({features['affected_users']})")
        
        if not reasons:
            reasons.append(f"Incident classified as {priority_level} priority")
        
        return "; ".join(reasons)
    
    @staticmethod
    def _encode_severity(severity):
        """Encode severity to numeric"""
        severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return severity_map.get(severity, 1)
    
    @staticmethod
    def _count_keywords(text):
        """Count security-related keywords"""
        keywords = ['breach', 'attack', 'malware', 'threat', 'vulnerability', 'exploit', 'compromise']
        count = sum(1 for keyword in keywords if keyword in text.lower())
        return count
