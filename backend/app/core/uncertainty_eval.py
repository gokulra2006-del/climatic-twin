import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.isotonic import IsotonicRegression
import logging

logger = logging.getLogger(__name__)

class UncertaintyEvaluator:
    """
    Scientific Purpose: Evaluates probabilistic forecasts, including CRPS, WIS, 
    Empirical Coverage, Sharpness, and Reliability. Supports extreme event isolation.
    """
    @staticmethod
    def coverage_and_sharpness(y_true, p10, p90):
        covered = ((y_true >= p10) & (y_true <= p90)).astype(float)
        coverage = np.mean(covered)
        sharpness = np.mean(p90 - p10)
        return coverage, sharpness

    @staticmethod
    def weighted_interval_score(y_true, p10, p50, p90, alpha=0.2):
        """
        WIS approximation for P10, P50, P90.
        WIS = (1/2)*|y - p50| + (alpha/2)*(p90 - p10) + max(p10 - y, 0) + max(y - p90, 0)
        """
        dispersion = (alpha / 2.0) * (p90 - p10)
        underprediction = np.maximum(p10 - y_true, 0)
        overprediction = np.maximum(y_true - p90, 0)
        absolute_error = 0.5 * np.abs(y_true - p50)
        
        wis = dispersion + underprediction + overprediction + absolute_error
        return np.mean(wis)

    @staticmethod
    def crps_gaussian_approx(y_true, p50, p_std):
        """
        Approximates CRPS assuming predictive distribution is Gaussian.
        CRPS(N(mu, sig^2), y) = sig * [ z(2 Phi(z) - 1) + 2 phi(z) - 1 / sqrt(pi) ]
        where z = (y - mu) / sig
        """
        from scipy.stats import norm
        p_std = np.clip(p_std, 1e-6, None)
        z = (y_true - p50) / p_std
        crps = p_std * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi))
        return np.mean(crps)
        
    @staticmethod
    def reliability_curve(y_true, p_prob, bins=10):
        """Computes empirical probability for binned forecast probabilities."""
        bin_edges = np.linspace(0, 1, bins + 1)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        empirical_probs = []
        for i in range(bins):
            mask = (p_prob >= bin_edges[i]) & (p_prob < bin_edges[i+1])
            if np.sum(mask) > 0:
                empirical_probs.append(np.mean(y_true[mask]))
            else:
                empirical_probs.append(np.nan)
        return bin_centers, np.array(empirical_probs)


class UncertaintyRecalibrator:
    """
    Implements Post-hoc Recalibration (Conformal and Isotonic).
    """
    def __init__(self):
        self.iso_reg = IsotonicRegression(out_of_bounds='clip')
        self.conformal_q = 0.0

    def fit_isotonic(self, val_p50, val_y):
        self.iso_reg.fit(val_p50, val_y)

    def predict_isotonic(self, test_p50):
        return self.iso_reg.predict(test_p50)

    def fit_conformal(self, val_p10, val_p90, val_y, alpha=0.2):
        """Split Conformal Prediction for Regression/Quantiles."""
        scores = np.maximum(val_p10 - val_y, val_y - val_p90)
        n = len(val_y)
        q_level = np.ceil((n + 1) * (1 - alpha)) / n
        q_level = np.clip(q_level, 0, 1)
        self.conformal_q = np.quantile(scores, q_level)

    def predict_conformal(self, test_p10, test_p90):
        return np.clip(test_p10 - self.conformal_q, 0, None), test_p90 + self.conformal_q

class EpistemicTracker:
    @staticmethod
    def mc_dropout_predict(model, X_tensor, adj_tensor=None, num_samples=30):
        """
        Enables Dropout at inference to estimate Epistemic uncertainty.
        Model must have dropout layers.
        """
        model.train() # Force dropout active
        predictions = []
        with torch.no_grad():
            for _ in range(num_samples):
                if adj_tensor is not None:
                    preds = model(X_tensor, adj_tensor)
                else:
                    preds = model(X_tensor)
                predictions.append(preds.unsqueeze(0))
        
        preds_stacked = torch.cat(predictions, dim=0) # (Samples, B, T, N, F)
        p_mean = preds_stacked.mean(dim=0)
        p_std = preds_stacked.std(dim=0) # Epistemic spread
        return p_mean, p_std
