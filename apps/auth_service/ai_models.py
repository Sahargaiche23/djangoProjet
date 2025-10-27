import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
import pickle
import os

class AuthRiskScorer:
    """
    Auth Risk Scorer - ML model for login risk assessment
    Features: user_id, timestamp_local, ip_geo_country, ip_risk_score, 
              device_fingerprint, failed_attempts_last_24h, last_login_geo_distance, 
              account_age, behavior_embedding
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = 'ml_models/auth_risk_scorer.pkl'
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
        
        # Train default model with synthetic data
        self._train_default_model()
    
    def _train_default_model(self):
        """Train model with synthetic data"""
        np.random.seed(42)
        n_samples = 1000
        
        X = np.random.randn(n_samples, 9)
        y = np.random.randint(0, 3, n_samples)  # 0: allow, 1: step_up_2fa, 2: block
        
        self.model = lgb.LGBMClassifier(
            num_leaves=31,
            max_depth=5,
            learning_rate=0.05,
            n_estimators=100,
            random_state=42
        )
        self.model.fit(X, y)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def extract_features(self, login_data):
        """Extract features from login attempt"""
        features = {
            'hour_of_day': login_data.get('timestamp', datetime.now()).hour,
            'day_of_week': login_data.get('timestamp', datetime.now()).weekday(),
            'is_weekend': login_data.get('timestamp', datetime.now()).weekday() >= 5,
            'ip_risk_score': login_data.get('ip_risk_score', 0.0),
            'failed_attempts_24h': login_data.get('failed_attempts_24h', 0),
            'account_age_days': login_data.get('account_age_days', 365),
            'geo_distance_km': login_data.get('geo_distance_km', 0.0),
            'device_seen_before': login_data.get('device_seen_before', 1),
            'behavior_score': login_data.get('behavior_score', 0.5),
        }
        return features
    
    def predict_risk(self, login_data):
        """
        Predict risk score and recommended action
        Returns: {
            'risk_score': float (0-1),
            'action': 'allow' | 'step_up_2fa' | 'block',
            'confidence': float,
            'reasoning': str
        }
        """
        features = self.extract_features(login_data)
        feature_vector = np.array([list(features.values())])
        
        # Predict
        prediction = self.model.predict(feature_vector)[0]
        probabilities = self.model.predict_proba(feature_vector)[0]
        
        action_map = {0: 'allow', 1: 'step_up_2fa', 2: 'block'}
        action = action_map[prediction]
        confidence = float(probabilities[prediction])
        
        # Calculate risk score (0-1)
        risk_score = 1.0 - probabilities[0]  # Inverse of allow probability
        
        reasoning = self._generate_reasoning(features, action, risk_score)
        
        return {
            'risk_score': float(risk_score),
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning,
            'features': features
        }
    
    def _generate_reasoning(self, features, action, risk_score):
        """Generate human-readable reasoning"""
        reasons = []
        
        if features['failed_attempts_24h'] > 3:
            reasons.append(f"Multiple failed attempts ({features['failed_attempts_24h']})")
        
        if features['hour_of_day'] >= 22 or features['hour_of_day'] <= 6:
            reasons.append("Unusual login time")
        
        if features['geo_distance_km'] > 1000:
            reasons.append(f"Significant geographic distance ({features['geo_distance_km']:.0f}km)")
        
        if not features['device_seen_before']:
            reasons.append("New device detected")
        
        if features['ip_risk_score'] > 0.7:
            reasons.append("High-risk IP address")
        
        if not reasons:
            reasons.append("Normal login pattern")
        
        return "; ".join(reasons)
