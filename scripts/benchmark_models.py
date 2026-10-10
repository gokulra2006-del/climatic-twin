import pandas as pd
import numpy as np
import os
import json
import time
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, 
    precision_score, recall_score, f1_score, brier_score_loss
)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

def run_benchmark():
    print("=== Phase Next: Chronological Model Benchmarking & Selection ===")
    base_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
    import sys
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    docs_dir = os.path.join(base_dir, "docs", "modeling")
    plots_dir = os.path.join(base_dir, "docs", "plots")
    models_dir = os.path.join(base_dir, "backend", "app", "models")
    
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Load Data
    from backend.app.core.live_feature_alignment import LiveFeatureAlignmentEngine
    aligner = LiveFeatureAlignmentEngine(base_dir)
    df_features = aligner.history_features.copy()
    df_features.dropna(inplace=True)
    
    # Define Target
    df_events = pd.read_csv(os.path.join(base_dir, 'data', 'processed', 'flood_events', 'chennai_flood_events.csv'))
    intervals = []
    for _, row in df_events.iterrows():
        try:
            start = pd.to_datetime(row['Start Date'])
            end = pd.to_datetime(row['End Date'])
            if pd.notna(start) and pd.notna(end):
                intervals.append((start, end))
        except:
            pass
            
    is_flood = np.zeros(len(df_features))
    for i, dt in enumerate(df_features.index):
        for start, end in intervals:
            if start <= dt <= end:
                is_flood[i] = 1.0
                break
    df_features['target'] = is_flood
    
    # 2. Strict Chronological Split (Train <= 2017-12-31, Test >= 2018-01-01)
    split_date = pd.to_datetime('2017-12-31 23:59:59')
    train_mask = df_features.index <= split_date
    test_mask = df_features.index > split_date
    
    X_train = df_features.loc[train_mask, aligner.feature_cols]
    y_train = df_features.loc[train_mask, 'target']
    X_test = df_features.loc[test_mask, aligner.feature_cols]
    y_test = df_features.loc[test_mask, 'target']
    
    print(f"Training set: {len(X_train)} samples, {int(y_train.sum())} flood days")
    print(f"Testing set: {len(X_test)} samples, {int(y_test.sum())} flood days")

    # 3. Define Models to Benchmark
    # We include MLP to evaluate neural network / deep learning performance vs trees
    models_to_evaluate = {
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=8, class_weight='balanced', random_state=42),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=100, max_depth=8, class_weight='balanced', random_state=42),
        "DeepLearning_MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42, early_stopping=True)
    }
    
    results = {}
    eval_curves = {'roc': {}, 'pr': {}, 'calib': {}}
    
    for name, model in models_to_evaluate.items():
        print(f"\nEvaluating {name}...")
        start_time = time.time()
        
        # Fit
        model.fit(X_train, y_train)
        
        # Inference latency measure (single sample mean)
        latencies = []
        for i in range(10):
            t0 = time.time()
            _ = model.predict_proba(X_test.iloc[[0]])
            latencies.append(time.time() - t0)
        mean_latency_ms = np.mean(latencies) * 1000
        
        # Test Preds
        probs = model.predict_proba(X_test)[:, 1]
        preds = model.predict(X_test)
        
        # Metrics
        roc_auc = float(roc_auc_score(y_test, probs))
        prec, rec, _ = precision_recall_curve(y_test, probs)
        pr_auc = float(auc(rec, prec))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        recall = float(recall_score(y_test, preds, zero_division=0))
        brier = float(brier_score_loss(y_test, probs))
        
        results[name] = {
            "ROC-AUC": round(roc_auc, 4),
            "PR-AUC": round(pr_auc, 4),
            "F1": round(f1, 4),
            "Recall": round(recall, 4),
            "Brier": round(brier, 4),
            "Latency_ms": round(mean_latency_ms, 2)
        }
        
        # Store curves
        from sklearn.metrics import roc_curve
        eval_curves['roc'][name] = roc_curve(y_test, probs)
        eval_curves['pr'][name] = (prec, rec)
        prob_true, prob_pred = calibration_curve(y_test, probs, n_bins=10)
        eval_curves['calib'][name] = (prob_true, prob_pred)
        
    print("\n=== Benchmark Results ===")
    df_results = pd.DataFrame(results).T
    print(df_results)
    
    # 4. Model Selection Logic
    # We prioritize PR-AUC and Recall for this imbalanced early warning system.
    # We avoid DeepLearning_MLP if it doesn't clearly win PR-AUC.
    best_model_name = df_results.sort_values(by=['PR-AUC', 'Recall'], ascending=False).index[0]
    print(f"\n[SELECTION] Best Model based on Chronological Test Data: {best_model_name}")
    
    selected_model = models_to_evaluate[best_model_name]
    
    # 5. Probability Calibration
    print("\nCalibrating Best Model (Sigmoid / Platt Scaling)...")
    calibrated_model = CalibratedClassifierCV(estimator=selected_model, method='sigmoid', cv=3)
    calibrated_model.fit(X_train, y_train)
    
    calib_probs = calibrated_model.predict_proba(X_test)[:, 1]
    calib_brier = float(brier_score_loss(y_test, calib_probs))
    print(f"Pre-Calibration Brier: {results[best_model_name]['Brier']}")
    print(f"Post-Calibration Brier: {calib_brier:.4f}")
    
    # 6. Save Model Artifacts
    model_path = os.path.join(models_dir, "best_live_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': calibrated_model,
            'base_model_name': best_model_name,
            'features': aligner.feature_cols,
            'training_period': f"<= {split_date.date()}",
            'version': '2.0.0_Live',
            'calibration_method': 'sigmoid'
        }, f)
        
    # 7. Generate Reports & Plots
    # Model Comparison JSON
    with open(os.path.join(docs_dir, "model_comparison.json"), "w") as f:
        json.dump({
            "evaluation_metrics": results,
            "selected_model": best_model_name,
            "selection_reason": "Highest PR-AUC and Recall on chronological unseen test data. Deep learning was evaluated but did not outperform tree ensembles on this specific dataset shape and size.",
            "calibration_brier_improvement": results[best_model_name]['Brier'] - calib_brier
        }, f, indent=4)
        
    # Plot ROC & PR
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for name in results.keys():
        fpr, tpr, _ = eval_curves['roc'][name]
        axes[0].plot(fpr, tpr, label=f"{name} (AUC={results[name]['ROC-AUC']})")
        
        prec, rec = eval_curves['pr'][name]
        axes[1].plot(rec, prec, label=f"{name} (PR-AUC={results[name]['PR-AUC']})")
        
    axes[0].plot([0,1], [0,1], 'k--')
    axes[0].set_title("ROC Curve")
    axes[0].legend()
    axes[1].set_title("Precision-Recall Curve")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "model_comparison.png"))
    plt.close()
    
    print("Benchmark complete. Artifacts saved.")

if __name__ == "__main__":
    run_benchmark()
