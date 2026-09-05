from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import numpy as np

class CompletionProbabilityRanker:
    def __init__(self):
        self.pipeline = Pipeline([
            ('vectorizer', DictVectorizer(sparse=False)),
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
        ])
        self.is_trained = False
        self.feature_names = []

    def prepare_data(self, dataset):
        X = []
        y = []
        for row in dataset:
            # We assume target_completed is already in the row or we must extract it.
            # actually extract_features currently doesn't output target_completed!
            # The prompt says: Target completed = 1 when student completed, else 0.
            # Wait, extract_features outputs 'recent_completion_rate' etc. The outcome itself is NOT in extract_features output because it is strictly pre-event features!
            # So the dataset passed here must be a list of tuples: (feature_dict, target)
            pass

    def train(self, X_train, y_train):
        if len(set(y_train)) < 2:
            raise ValueError("Training data must contain both classes (0 and 1).")
            
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True
        
        # Get feature names from DictVectorizer
        self.feature_names = self.pipeline.named_steps['vectorizer'].get_feature_names_out()

    def predict_proba(self, X):
        if not self.is_trained:
            raise RuntimeError("Model is not trained.")
        return self.pipeline.predict_proba(X)[:, 1]
        
    def predict(self, X):
        if not self.is_trained:
            raise RuntimeError("Model is not trained.")
        return self.pipeline.predict(X)

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    
    unique_classes = len(set(y_test))
    
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0) if unique_classes > 1 else 0.0,
        "recall": recall_score(y_test, y_pred, zero_division=0) if unique_classes > 1 else 0.0,
        "f1": f1_score(y_test, y_pred, zero_division=0) if unique_classes > 1 else 0.0,
        "roc_auc": roc_auc_score(y_test, y_prob) if unique_classes > 1 else None,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "positive_samples": sum(y_test),
        "negative_samples": len(y_test) - sum(y_test),
        "majority_class_baseline": max(sum(y_test), len(y_test) - sum(y_test)) / len(y_test) if len(y_test) > 0 else 0.0
    }
    return metrics
