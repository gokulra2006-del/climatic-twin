import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

# Config per user requirement
ENKF_CONFIG = {
    "STATE_VARS": ["POONDI", "CHOLAVARAM", "REDHILLS", "CHEMBARAMBAKKAM"],
    "ENSEMBLE_SIZE": 100,
    "COVARIANCE_INFLATION": 1.05,
    "LOCALIZATION_RADIUS": None, # Future spatial tapering 
    # Base observation variances (R diagonal)
    "R_VARS": [400.0, 150.0, 350.0, 450.0],
    "PROCESS_NOISE": [50.0, 20.0, 40.0, 60.0], # Q diagonal (system uncertainty)
    "STUCK_INFLATION_FACTOR": 1000.0  # Inflate R if sensor is flagged faulty
}

class ReservoirEnKF:
    def __init__(self, N=None, inflation=None):
        self.state_vars = ENKF_CONFIG["STATE_VARS"]
        self.n_state = len(self.state_vars)
        self.N = N if N else ENKF_CONFIG["ENSEMBLE_SIZE"]
        self.inflation = inflation if inflation else ENKF_CONFIG["COVARIANCE_INFLATION"]
        
        # Initialize ensemble (shape: N, n_state)
        # We start with some naive uniform guess (empty reservoirs)
        self.ensemble = np.zeros((self.N, self.n_state))
        
        self.Q = np.diag(ENKF_CONFIG["PROCESS_NOISE"]) ** 2
        self.R_base = np.diag(ENKF_CONFIG["R_VARS"]) ** 2

    def process_model(self):
        """
        f(x): Naive persistence process model with added system noise Q.
        In a real physical twin, this would be a hydrodynamic step.
        """
        for i in range(self.N):
            self.ensemble[i] += np.random.multivariate_normal(np.zeros(self.n_state), self.Q)
            # Physical bounds
            self.ensemble[i] = np.clip(self.ensemble[i], 0, None)

    def assimilate(self, observations: dict, faults: dict = None):
        """
        Assimilate an incoming observation dictionary.
        observations: e.g. {"POONDI": 2000, "REDHILLS": 1500} (missing others)
        faults: {"POONDI": "stuck"} (fault flags)
        """
        if not faults:
            faults = {}
            
        z_list = []
        H_rows = []
        R_diag = []
        
        for i, var in enumerate(self.state_vars):
            if var in observations:
                # Dynamically construct observation row
                val = observations[var]
                h_row = np.zeros(self.n_state)
                h_row[i] = 1.0
                
                # Check for fault
                var_fault = faults.get(var)
                r_val = self.R_base[i, i]
                if var_fault in ["stuck", "biased", "stale"]:
                    r_val *= ENKF_CONFIG["STUCK_INFLATION_FACTOR"]
                
                z_list.append(val)
                H_rows.append(h_row)
                R_diag.append(r_val)

        if len(z_list) == 0:
            return np.mean(self.ensemble, axis=0) # No valid obs, just return prediction

        z = np.array(z_list)
        H = np.array(H_rows)
        R = np.diag(R_diag)
        
        n_obs = len(z)

        # 1. Inflation
        x_mean = np.mean(self.ensemble, axis=0)
        self.ensemble = x_mean + self.inflation * (self.ensemble - x_mean)

        # 2. Perturb Observations
        Z = np.zeros((self.N, n_obs))
        for i in range(self.N):
            Z[i] = z + np.random.multivariate_normal(np.zeros(n_obs), R)

        # 3. Predict Observations
        HX = self.ensemble @ H.T # Shape: (N, n_obs)
        HX_mean = np.mean(HX, axis=0)

        # 4. Kalman Gain using sample covariance
        dX = self.ensemble - x_mean
        dHX = HX - HX_mean
        
        P_xy = (dX.T @ dHX) / (self.N - 1)
        P_yy = (dHX.T @ dHX) / (self.N - 1) + R
        
        try:
            K = P_xy @ np.linalg.inv(P_yy)
        except np.linalg.LinAlgError:
            logger.warning("Singular P_yy. Adding jitter.")
            K = P_xy @ np.linalg.inv(P_yy + np.eye(n_obs)*1e-6)

        # 5. Update
        for i in range(self.N):
            self.ensemble[i] = self.ensemble[i] + K @ (Z[i] - HX[i])
            # Enforce physical constraint (>= 0)
            self.ensemble[i] = np.clip(self.ensemble[i], 0, None)
            
        return np.mean(self.ensemble, axis=0)
