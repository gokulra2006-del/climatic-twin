import numpy as np
import logging
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

class ProbabilisticCompoundRiskEngine:
    """
    Scientific Purpose: Converts abstract compound risk indices into true probabilities of impact P(Y=1).
    Estimates base weights (w_i) and interaction terms (gamma_ij) using regularized 
    Logistic Regression (Bayesian/L2 prior). Naturally supports negative/protective interactions.
    Handles rare compound events via class weighting (balanced).
    """
    def __init__(self, use_interactions=True, penalty='l2', C=1.0):
        self.use_interactions = use_interactions
        self.model = LogisticRegression(class_weight='balanced', penalty=penalty, C=C, solver='liblinear')
        self.feature_names = []

    def _build_features(self, X_base):
        if not self.use_interactions:
            return X_base
        
        N, d = X_base.shape
        X_interact = []
        for i in range(d):
            for j in range(i+1, d):
                X_interact.append(X_base[:, i] * X_base[:, j])
                
        if len(X_interact) > 0:
            return np.hstack([X_base, np.column_stack(X_interact)])
        return X_base

    def fit(self, X_base, y, base_names):
        self.feature_names = list(base_names)
        if self.use_interactions:
            for i in range(len(base_names)):
                for j in range(i+1, len(base_names)):
                    self.feature_names.append(f"{base_names[i]}_x_{base_names[j]}")
                    
        X_full = self._build_features(X_base)
        self.model.fit(X_full, y)

    def predict_proba(self, X_base):
        X_full = self._build_features(X_base)
        return self.model.predict_proba(X_full)[:, 1]

    def get_coefficients(self):
        return dict(zip(self.feature_names, self.model.coef_[0]))
