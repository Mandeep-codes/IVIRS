#!/usr/bin/env python3
"""
Advanced Machine Learning Based Fake Report Detection
Implements Random Forest, Neural Network, and ensemble methods
"""

import numpy as np
import pandas as pd
import json
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

class FakeReportDetector:
    """
    Multi-model ensemble for fake report detection
    """
    
    def __init__(self):
        # Models
        self.random_forest = None
        self.gradient_boost = None
        self.neural_network = None
        self.scaler = StandardScaler()
        
        # Ensemble weights (learned from validation)
        self.ensemble_weights = {'rf': 0.4, 'gb': 0.35, 'nn': 0.25}
        
    def extract_features(self, report_data):
        """
        Extract features from report for ML classification
        
        Features:
        1. Reporter trust score (historical)
        2. Number of witnesses
        3. Distance from reporter to incident location
        4. Time since last report from this vehicle
        5. Proximity to other vehicles
        6. Speed at time of report
        7. Distance to nearest RSU
        8. Report frequency of this vehicle
        9. Consistency with nearby vehicle reports
        10. Time of day (rush hour, etc.)
        """
        features = []
        
        reporter_trust = report_data.get('reporter_trust_score', 0.5)
        witnesses = report_data.get('witnesses', [])
        witness_count = len(witnesses) if isinstance(witnesses, list) else int(witnesses) if witnesses else 0
        location_distance = report_data.get('location_distance', 0)
        time_since_last = report_data.get('time_since_last_report', 1000)
        nearby_vehicles = report_data.get('nearby_vehicle_count', 0)
        reporter_speed = report_data.get('reporter_speed', 0)
        rsu_distance = report_data.get('rsu_distance', 0)
        report_frequency = report_data.get('report_frequency', 0)
        consistency_score = report_data.get('consistency_score', 0.5)
        time_of_day = report_data.get('time_of_day', 0)
        
        # Derived features
        witness_ratio = witness_count / max(1, nearby_vehicles)
        location_credibility = 1.0 / (1.0 + location_distance / 100)
        report_pattern_score = 1.0 / (1.0 + report_frequency)
        
        features = [
            reporter_trust,
            witness_count,
            location_distance,
            time_since_last,
            nearby_vehicles,
            reporter_speed,
            rsu_distance,
            report_frequency,
            consistency_score,
            time_of_day,
            witness_ratio,
            location_credibility,
            report_pattern_score
        ]
        
        return np.array(features).reshape(1, -1)
    
    def generate_training_data(self, num_samples=10000):
        """
        Generate synthetic training data for fake detection
        """
        np.random.seed(42)
        
        # Real reports (60%)
        num_real = int(num_samples * 0.6)
        real_reports = []
        
        for _ in range(num_real):
            report = {
                'reporter_trust_score': np.random.beta(8, 2),  # High trust
                'witnesses': np.random.randint(0, 5),
                'location_distance': np.random.exponential(50),  # Close to reporter
                'time_since_last_report': np.random.exponential(300),
                'nearby_vehicle_count': np.random.poisson(8),
                'reporter_speed': np.random.normal(25, 5),
                'rsu_distance': np.random.uniform(0, 400),
                'report_frequency': np.random.poisson(0.5),
                'consistency_score': np.random.beta(7, 3),
                'time_of_day': np.random.uniform(0, 24),
                'is_fake': 0
            }
            real_reports.append(report)
        
        # Fake reports (40%)
        num_fake = num_samples - num_real
        fake_reports = []
        
        for _ in range(num_fake):
            report = {
                'reporter_trust_score': np.random.beta(2, 8),  # Low trust
                'witnesses': 0 if np.random.random() < 0.7 else np.random.randint(0, 2),
                'location_distance': np.random.exponential(300),  # Far from reporter
                'time_since_last_report': np.random.exponential(50),  # Frequent reports
                'nearby_vehicle_count': np.random.poisson(3),  # Fewer vehicles
                'reporter_speed': np.random.normal(20, 10),
                'rsu_distance': np.random.uniform(100, 500),
                'report_frequency': np.random.poisson(3),  # High frequency
                'consistency_score': np.random.beta(2, 8),  # Low consistency
                'time_of_day': np.random.uniform(0, 24),
                'is_fake': 1
            }
            fake_reports.append(report)
        
        # Combine and shuffle
        all_reports = real_reports + fake_reports
        np.random.shuffle(all_reports)
        
        return pd.DataFrame(all_reports)
    
    def train_models(self, data=None, save_models=True):
        """
        Train all ML models
        """
        if data is None:
            print("[ML] Generating synthetic training data...")
            data = self.generate_training_data(10000)
        
        # Extract features
        X = []
        for _, row in data.iterrows():
            features = self.extract_features(row.to_dict())[0]
            X.append(features)
        
        X = np.array(X)
        y = data['is_fake'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("[ML] Training Random Forest...")
        self.random_forest = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.random_forest.fit(X_train_scaled, y_train)
        rf_score = self.random_forest.score(X_test_scaled, y_test)
        print(f"[ML] Random Forest Test Accuracy: {rf_score:.4f}")
        
        print("[ML] Training Gradient Boosting...")
        self.gradient_boost = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.gradient_boost.fit(X_train_scaled, y_train)
        gb_score = self.gradient_boost.score(X_test_scaled, y_test)
        print(f"[ML] Gradient Boosting Test Accuracy: {gb_score:.4f}")
        
        print("[ML] Training Neural Network...")
        self.neural_network = MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size=32,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42
        )
        self.neural_network.fit(X_train_scaled, y_train)
        nn_score = self.neural_network.score(X_test_scaled, y_test)
        print(f"[ML] Neural Network Test Accuracy: {nn_score:.4f}")
        
        # Ensemble prediction
        rf_pred = self.random_forest.predict_proba(X_test_scaled)[:, 1]
        gb_pred = self.gradient_boost.predict_proba(X_test_scaled)[:, 1]
        nn_pred = self.neural_network.predict_proba(X_test_scaled)[:, 1]
        
        ensemble_pred = (
            self.ensemble_weights['rf'] * rf_pred +
            self.ensemble_weights['gb'] * gb_pred +
            self.ensemble_weights['nn'] * nn_pred
        )
        ensemble_pred_binary = (ensemble_pred > 0.5).astype(int)
        ensemble_accuracy = np.mean(ensemble_pred_binary == y_test)
        
        print(f"[ML] Ensemble Test Accuracy: {ensemble_accuracy:.4f}")
        
        # Detailed metrics
        print("\n" + "="*60)
        print("CLASSIFICATION REPORT (Ensemble)")
        print("="*60)
        print(classification_report(y_test, ensemble_pred_binary, 
                                   target_names=['Real', 'Fake']))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, ensemble_pred_binary)
        print("\nConfusion Matrix:")
        print(cm)
        
        # ROC-AUC
        roc_auc = roc_auc_score(y_test, ensemble_pred)
        print(f"\nROC-AUC Score: {roc_auc:.4f}")
        
        # Feature Importance (from Random Forest)
        feature_names = [
            'Reporter Trust', 'Witness Count', 'Location Distance',
            'Time Since Last', 'Nearby Vehicles', 'Reporter Speed',
            'RSU Distance', 'Report Frequency', 'Consistency Score',
            'Time of Day', 'Witness Ratio', 'Location Credibility',
            'Report Pattern'
        ]
        
        importances = self.random_forest.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\nFeature Importances:")
        for i, idx in enumerate(indices[:10]):
            print(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
        
        # Save models
        if save_models:
            self.save_models()
        
        # Generate visualizations
        self.generate_visualizations(X_test_scaled, y_test, feature_names)
        
        return {
            'rf_accuracy': rf_score,
            'gb_accuracy': gb_score,
            'nn_accuracy': nn_score,
            'ensemble_accuracy': ensemble_accuracy,
            'roc_auc': roc_auc
        }
    
    def predict(self, report_data):
        """
        Predict if a report is fake using ensemble
        Returns: probability of being fake (0-1)
        """
        features = self.extract_features(report_data)
        features_scaled = self.scaler.transform(features)
        
        rf_pred = self.random_forest.predict_proba(features_scaled)[0, 1]
        gb_pred = self.gradient_boost.predict_proba(features_scaled)[0, 1]
        nn_pred = self.neural_network.predict_proba(features_scaled)[0, 1]
        
        ensemble_pred = (
            self.ensemble_weights['rf'] * rf_pred +
            self.ensemble_weights['gb'] * gb_pred +
            self.ensemble_weights['nn'] * nn_pred
        )
        
        return ensemble_pred
    
    def save_models(self, filepath='ml-detection/models/'):
        """Save trained models"""
        import os
        os.makedirs(filepath, exist_ok=True)
        
        with open(f'{filepath}random_forest.pkl', 'wb') as f:
            pickle.dump(self.random_forest, f)
        
        with open(f'{filepath}gradient_boost.pkl', 'wb') as f:
            pickle.dump(self.gradient_boost, f)
        
        with open(f'{filepath}neural_network.pkl', 'wb') as f:
            pickle.dump(self.neural_network, f)
        
        with open(f'{filepath}scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"[ML] Models saved to {filepath}")
    
    def load_models(self, filepath='ml-detection/models/'):
        """Load trained models"""
        with open(f'{filepath}random_forest.pkl', 'rb') as f:
            self.random_forest = pickle.load(f)
        
        with open(f'{filepath}gradient_boost.pkl', 'rb') as f:
            self.gradient_boost = pickle.load(f)
        
        with open(f'{filepath}neural_network.pkl', 'rb') as f:
            self.neural_network = pickle.load(f)
        
        with open(f'{filepath}scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)
        
        print(f"[ML] Models loaded from {filepath}")
    
    def generate_visualizations(self, X_test, y_test, feature_names):
        """Generate visualization plots"""
        import os
        os.makedirs('analysis/visualizations', exist_ok=True)
        
        # Feature importance plot
        plt.figure(figsize=(10, 8))
        importances = self.random_forest.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.title('Feature Importances for Fake Report Detection')
        plt.barh(range(len(indices)), importances[indices], color='skyblue')
        plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
        plt.xlabel('Importance')
        plt.tight_layout()
        plt.savefig('analysis/visualizations/feature_importance.png', dpi=300)
        plt.close()
        
        print("[ML] Visualizations saved to analysis/visualizations/")

def main():
    """Main training script"""
    print("="*60)
    print("IVIRS Machine Learning Training")
    print("="*60)
    
    detector = FakeReportDetector()
    metrics = detector.train_models()
    
    print("\n" + "="*60)
    print("TRAINING COMPLETED")
    print("="*60)
    print(f"Final Ensemble Accuracy: {metrics['ensemble_accuracy']:.2%}")
    print(f"ROC-AUC Score: {metrics['roc_auc']:.4f}")
    print("="*60)

if __name__ == "__main__":
    main()
