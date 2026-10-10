import os
import sys
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
import logging

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Baseline_Suite")

# --- 1. BASELINE MODEL INTERFACES ---
class BaseModelBaseline:
    def fit(self, X, y): raise NotImplementedError
    def predict(self, X): raise NotImplementedError
    def predict_proba(self, X): raise NotImplementedError
    def predict_interval(self, X, alpha=0.1):
        p = self.predict_proba(X)
        return np.clip(p - 0.2, 0, 1), np.clip(p + 0.2, 0, 1)

class PersistenceModel(BaseModelBaseline):
    def fit(self, X, y): pass
    def predict(self, X): return X[:, 0]  # Assumes index 0 is lagged target
    def predict_proba(self, X): return X[:, 0]

class PhysicsHydrologicalBaseline(BaseModelBaseline):
    def __init__(self, rain_idx, res_idx, rain_thresh=80.0, res_thresh=30.0):
        self.rain_idx = rain_idx
        self.res_idx = res_idx
        self.rain_thresh = rain_thresh
        self.res_thresh = res_thresh
    def fit(self, X, y): pass
    def predict_proba(self, X):
        prob = (X[:, self.rain_idx] / (self.rain_thresh * 1.5)) * 0.6 + (X[:, self.res_idx] / 100.0) * 0.4
        return np.clip(prob, 0, 1)
    def predict(self, X):
        return (self.predict_proba(X) >= 0.5).astype(int)

class LogRegBaseline(BaseModelBaseline):
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    def fit(self, X, y): self.model.fit(X, y)
    def predict(self, X): return self.model.predict(X)
    def predict_proba(self, X): return self.model.predict_proba(X)[:, 1]

class RFBaseline(BaseModelBaseline):
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42)
    def fit(self, X, y): self.model.fit(X, y)
    def predict(self, X): return self.model.predict(X)
    def predict_proba(self, X): return self.model.predict_proba(X)[:, 1]

class XGBBaseline(BaseModelBaseline):
    def __init__(self):
        if XGB_AVAILABLE:
            self.model = xgb.XGBClassifier(n_estimators=100, max_depth=6, scale_pos_weight=5, random_state=42, use_label_encoder=False, eval_metric='logloss')
        else:
            self.model = None
    def fit(self, X, y):
        if self.model: self.model.fit(X, y)
    def predict(self, X): return self.model.predict(X) if self.model else np.zeros(len(X))
    def predict_proba(self, X): return self.model.predict_proba(X)[:, 1] if self.model else np.zeros(len(X))

# --- Simple PyTorch Models ---
class LSTMPyTorch(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, 32, batch_first=True)
        self.fc = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        _, (h_n, _) = self.lstm(x.unsqueeze(1))
        return self.sigmoid(self.fc(h_n[-1]))

class LSTMBaseline(BaseModelBaseline):
    def __init__(self, epochs=20, lr=0.01):
        self.epochs = epochs
        self.lr = lr
        self.model = None
    def fit(self, X, y):
        set_global_seed(42)
        self.model = LSTMPyTorch(X.shape[1])
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.BCELoss()
        X_t = torch.FloatTensor(X)
        y_t = torch.FloatTensor(y).unsqueeze(1)
        for _ in range(self.epochs):
            optimizer.zero_grad()
            out = self.model(X_t)
            loss = criterion(out, y_t)
            loss.backward()
            optimizer.step()
    def predict_proba(self, X):
        with torch.no_grad():
            return self.model(torch.FloatTensor(X)).squeeze().numpy()
    def predict(self, X):
        return (self.predict_proba(X) > 0.5).astype(int)

class PlaceholderGNN(BaseModelBaseline):
    def fit(self, X, y): pass
    def predict_proba(self, X): return np.zeros(len(X))  # TARGET/TODO
    def predict(self, X): return np.zeros(len(X))

# --- 2. EVALUATION & METRICS ---
def calc_metrics(y_true, y_prob):
    y_pred = (y_prob >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0,1]).ravel()
    
    mae = mean_absolute_error(y_true, y_prob)
    rmse = np.sqrt(mean_squared_error(y_true, y_prob))
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    far = fp / (fp + tp) if (fp + tp) > 0 else 0.0
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    return {
        "MAE": mae, "RMSE": rmse, "POD (Recall)": pod, 
        "FAR": far, "Precision": prec, "F1": f1
    }

def bootstrap_ci(y_true, y_prob, n_bootstraps=1000):
    np.random.seed(42)
    bootstrapped_metrics = {"MAE": [], "RMSE": [], "POD (Recall)": [], "FAR": [], "F1": []}
    indices = np.arange(len(y_true))
    for _ in range(n_bootstraps):
        idx = np.random.choice(indices, size=len(indices), replace=True)
        # Ensure both classes exist in bootstrap sample to avoid metric crash
        if len(np.unique(y_true[idx])) < 2: continue
        m = calc_metrics(y_true[idx], y_prob[idx])
        for k, v in m.items():
            if k in bootstrapped_metrics:
                bootstrapped_metrics[k].append(v)
                
    ci = {}
    for k, v in bootstrapped_metrics.items():
        if v:
            ci[k] = (np.percentile(v, 2.5), np.percentile(v, 97.5))
        else:
            ci[k] = (0, 0)
    return ci

def main():
    set_global_seed(42)
    logger.info("Starting Multi-Model Baseline Suite...")

    # Load chronological splits
    data_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\data\processed\catalogue_v1"
    try:
        train_df = pd.read_csv(os.path.join(data_dir, "train_split.csv"))
        test_df = pd.read_csv(os.path.join(data_dir, "test_split.csv"))
    except Exception as e:
        logger.error("Splits not found. Please run build_event_catalogue.py first.")
        return

    # Prepare features
    train_df['lag_flood'] = train_df['event_flood'].shift(1).fillna(0)
    test_df['lag_flood'] = test_df['event_flood'].shift(1).fillna(0)
    
    features = ['lag_flood', 'rainfall_daily', 'rainfall_72h', 'total_res_pct', 'temp_max', 'grid_load_mw_SYNTHETIC']
    target = 'event_flood'
    
    train_df = train_df.dropna(subset=features + [target])
    test_df = test_df.dropna(subset=features + [target])
    
    X_train, y_train = train_df[features].values, train_df[target].values
    X_test, y_test = test_df[features].values, test_df[target].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    
    # We don't scale lagged binary for persistence, so persistence uses raw X_test
    # Physics uses raw X_test
    rain_idx = features.index('rainfall_72h')
    res_idx = features.index('total_res_pct')

    models = {
        "Persistence": (PersistenceModel(), False),
        "Physics (Thresh)": (PhysicsHydrologicalBaseline(rain_idx, res_idx), False),
        "Logistic Reg": (LogRegBaseline(), True),
        "Random Forest": (RFBaseline(), True),
        "XGBoost": (XGBBaseline(), True),
        "LSTM": (LSTMBaseline(), True),
        "TCN": (PlaceholderGNN(), True), # TARGET/TODO
        "GNN (Spatial)": (PlaceholderGNN(), True) # TARGET/TODO
    }

    results = []
    base_probs = None
    
    for name, (model, use_scaled) in models.items():
        logger.info(f"Training and Evaluating {name}...")
        X_tr = X_train_s if use_scaled else X_train
        X_te = X_test_s if use_scaled else X_test
        
        model.fit(X_tr, y_train)
        y_prob = model.predict_proba(X_te)
        
        if name == "Persistence":
            base_probs = y_prob
            
        m = calc_metrics(y_test, y_prob)
        ci = bootstrap_ci(y_test, y_prob, n_bootstraps=200) # 200 for speed
        
        # Paired Wilcoxon against Persistence
        if name != "Persistence" and base_probs is not None and not np.all(y_prob == 0):
            err_model = np.abs(y_test - y_prob)
            err_base = np.abs(y_test - base_probs)
            try:
                stat, p_val = stats.wilcoxon(err_model, err_base)
            except:
                p_val = 1.0
        else:
            p_val = np.nan
            
        res_row = {
            "Model": name,
            "F1": f"{m['F1']:.3f} [{ci['F1'][0]:.3f}-{ci['F1'][1]:.3f}]",
            "POD": f"{m['POD (Recall)']:.3f} [{ci['POD (Recall)'][0]:.3f}-{ci['POD (Recall)'][1]:.3f}]",
            "FAR": f"{m['FAR']:.3f} [{ci['FAR'][0]:.3f}-{ci['FAR'][1]:.3f}]",
            "MAE": f"{m['MAE']:.3f}",
            "RMSE": f"{m['RMSE']:.3f}",
            "Wilcoxon p-val": f"{p_val:.4f}" if not np.isnan(p_val) else "-",
            "Lead Time": "24h" if name not in ["TCN", "GNN (Spatial)"] else "TARGET",
            "Notes": "TODO/Target" if "Placeholder" in str(type(model)) else "Measured"
        }
        results.append(res_row)

    df_res = pd.DataFrame(results)
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\docs"
    os.makedirs(out_dir, exist_ok=True)
    
    df_res.to_csv(os.path.join(out_dir, "baseline_results.csv"), index=False)
    
    with open(os.path.join(out_dir, "baseline_results.tex"), "w") as f:
        f.write(df_res.to_latex(index=False, caption="Baseline Model Evaluation on Strict Chronological Test Set"))
        
    logger.info("\n" + df_res.to_string())
    logger.info(f"Saved results to {out_dir}")

if __name__ == "__main__":
    main()
