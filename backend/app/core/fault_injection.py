import numpy as np
import logging
from scipy.stats import ks_2samp
from sklearn.linear_model import RidgeClassifier, LogisticRegression

logger = logging.getLogger(__name__)

class FaultInjector:
    """Scientific Purpose: Hardware and Network Fault Simulation Matrix."""
    
    @staticmethod
    def random_missing(X, rate=0.1):
        mask = np.random.rand(*X.shape) < rate
        X_out = X.copy()
        X_out[mask] = np.nan
        return X_out
        
    @staticmethod
    def burst_missing(X, prob=0.01, burst_len=10):
        X_out = X.copy()
        for i in range(X.shape[0]):
            if np.random.rand() < prob:
                end = min(i + burst_len, X.shape[0])
                X_out[i:end, :] = np.nan
        return X_out
        
    @staticmethod
    def stuck_at(X, prob=0.05, stuck_val=0.0):
        X_out = X.copy()
        mask = np.random.rand(X.shape[0]) < prob
        X_out[mask, :] = stuck_val
        return X_out
        
    @staticmethod
    def bias(X, offset=5.0):
        return X + offset
        
    @staticmethod
    def out_of_order_mqtt(X, prob=0.1, max_delay=3):
        X_out = X.copy()
        for i in range(X.shape[0]):
            if np.random.rand() < prob:
                swap_idx = min(i + np.random.randint(1, max_delay+1), X.shape[0]-1)
                X_out[i], X_out[swap_idx] = X_out[swap_idx], X_out[i]
        return X_out
        
    @staticmethod
    def comm_outage(X, outage_start=100, outage_end=150):
        X_out = X.copy()
        X_out[outage_start:outage_end, :] = np.nan
        return X_out
        
    @staticmethod
    def corrupted_values(X, noise_scale=10.0):
        return X + np.random.normal(0, noise_scale, X.shape)


class AdaptiveForecaster:
    """
    Scientific Purpose: Non-stationary drift handling. Actively monitors 
    Kolmogorov-Smirnov (KS) distance. Triggers model recalibration/retraining 
    when statistical covariance shift is detected across seasons.
    """
    def __init__(self, buffer_size=300, drift_threshold=0.15):
        self.model = LogisticRegression(max_iter=1000)
        self.buffer_X = []
        self.buffer_y = []
        self.reference_X = None
        self.buffer_size = buffer_size
        self.drift_threshold = drift_threshold
        self.retrain_counts = 0
        self.step_counter = 0
        
    def fit_initial(self, X, y):
        self.model.fit(X, y)
        self.reference_X = X.copy()
        self.buffer_X = list(X[-self.buffer_size:])
        self.buffer_y = list(y[-self.buffer_size:])
        
    def update_and_predict_proba(self, x_new, y_new):
        # Fill NaNs natively via persistence (carry-forward) for robust inference
        if np.isnan(x_new).any():
            x_new = np.nan_to_num(x_new, nan=self.buffer_X[-1] if self.buffer_X else 0)
            
        pred = self.model.predict_proba(x_new.reshape(1, -1))[0, 1]
        
        self.buffer_X.append(x_new)
        self.buffer_y.append(y_new)
        self.step_counter += 1
        
        if len(self.buffer_X) > self.buffer_size:
            self.buffer_X.pop(0)
            self.buffer_y.pop(0)
            
            # Drift Check every 50 steps
            if self.step_counter % 50 == 0:
                stat, p_val = ks_2samp(self.reference_X[:, 0], np.array(self.buffer_X)[:, 0])
                if stat > self.drift_threshold:
                    logger.debug(f"Drift Detected! KS={stat:.2f}. Retraining...")
                    b_X, b_y = np.array(self.buffer_X), np.array(self.buffer_y)
                    # Need at least two classes to retrain LogReg safely
                    if len(np.unique(b_y)) > 1:
                        self.model.fit(b_X, b_y)
                        self.reference_X = b_X.copy()
                        self.retrain_counts += 1
                    
        return pred
