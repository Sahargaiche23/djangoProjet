import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os

class LogAnomalyDetector:
    """
    Log Anomaly Detector - ML model for detecting anomalies in logs
    Uses Isolation Forest for feature-based anomaly detection
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'ml_models/log_anomaly_detector.pkl'
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
        n_samples = 1000
        
        # Simulate normal log patterns
        X = np.random.randn(n_samples, 8)
        
        self.model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def extract_log_features(self, access_log):
        """Extract features from access log"""
        features = {
            'hour_of_day': access_log.timestamp.hour,
            'day_of_week': access_log.timestamp.weekday(),
            'latency_ms': access_log.latency_ms or 0,
            'is_error': 1 if access_log.status == 'failure' else 0,
            'error_code_numeric': self._encode_error_code(access_log.error_code),
            'resource_type_numeric': self._encode_resource_type(access_log.resource_type),
            'action_numeric': self._encode_action(access_log.action),
            'event_type_numeric': self._encode_event_type(access_log.event_type),
        }
        return features
    
    def detect_anomaly(self, access_log):
        """
        Detect if a log entry is anomalous
        Returns: {
            'is_anomaly': bool,
            'anomaly_score': float (-1 to 1, -1 is anomaly),
            'confidence': float (0-1),
            'anomaly_types': [str],
            'reasoning': str
        }
        """
        features = self.extract_log_features(access_log)
        feature_vector = np.array([list(features.values())])
        
        # Predict
        prediction = self.model.predict(feature_vector)[0]
        anomaly_score = self.model.score_samples(feature_vector)[0]
        
        is_anomaly = prediction == -1
        confidence = abs(anomaly_score) / 10  # Normalize to 0-1
        
        anomaly_types = self._classify_anomalies(access_log, features)
        reasoning = self._generate_reasoning(access_log, anomaly_types)
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': float(anomaly_score),
            'confidence': float(min(confidence, 1.0)),
            'anomaly_types': anomaly_types,
            'reasoning': reasoning,
        }
    
    def _classify_anomalies(self, access_log, features):
        """Classify types of anomalies detected"""
        anomalies = []
        
        # Unusual time
        if features['hour_of_day'] < 6 or features['hour_of_day'] > 22:
            anomalies.append('unusual_time')
        
        # High latency
        if features['latency_ms'] > 5000:
            anomalies.append('high_latency')
        
        # Error spike
        if features['is_error']:
            anomalies.append('error_detected')
        
        # Unusual resource access
        if access_log.resource_type not in ['database', 'file', 'api']:
            anomalies.append('unusual_resource')
        
        # Bulk operation
        if access_log.action == 'bulk_read' or access_log.action == 'bulk_write':
            anomalies.append('bulk_operation')
        
        return anomalies
    
    def _generate_reasoning(self, access_log, anomaly_types):
        """Generate human-readable reasoning"""
        if not anomaly_types:
            return "Log entry appears normal"
        
        reasons = []
        for atype in anomaly_types:
            if atype == 'unusual_time':
                reasons.append(f"Access at unusual time ({access_log.timestamp.hour}:00)")
            elif atype == 'high_latency':
                reasons.append(f"High latency ({access_log.latency_ms}ms)")
            elif atype == 'error_detected':
                reasons.append(f"Error: {access_log.error_message}")
            elif atype == 'unusual_resource':
                reasons.append(f"Unusual resource type: {access_log.resource_type}")
            elif atype == 'bulk_operation':
                reasons.append("Bulk operation detected")
        
        return "; ".join(reasons)
    
    @staticmethod
    def _encode_error_code(error_code):
        """Encode error code to numeric"""
        code_map = {
            '401': 1, '403': 2, '404': 3, '500': 4, '502': 5, '503': 6,
        }
        return code_map.get(error_code, 0)
    
    @staticmethod
    def _encode_resource_type(resource_type):
        """Encode resource type to numeric"""
        type_map = {
            'database': 1, 'file': 2, 'api': 3, 'cache': 4, 'queue': 5,
        }
        return type_map.get(resource_type, 0)
    
    @staticmethod
    def _encode_action(action):
        """Encode action to numeric"""
        action_map = {
            'read': 1, 'write': 2, 'delete': 3, 'update': 4, 'bulk_read': 5, 'bulk_write': 6,
        }
        return action_map.get(action, 0)
    
    @staticmethod
    def _encode_event_type(event_type):
        """Encode event type to numeric"""
        event_map = {
            'login': 1, 'logout': 2, 'access': 3, 'modification': 4, 'deletion': 5,
        }
        return event_map.get(event_type, 0)
