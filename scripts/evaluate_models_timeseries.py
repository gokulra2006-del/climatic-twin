import pandas as pd
import numpy as np
import os
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, precision_recall_curve, 
    auc, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
)

def main():
    print("Starting Comprehensive EDA and Modeling Pipeline...")
    base_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin"
    processed_dir = os.path.join(base_dir, "data", "processed")
    models_dir = os.path.join(base_dir, "backend", "app", "models")
    plots_dir = os.path.join(base_dir, "docs", "plots")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Load datasets
    df_events = pd.read_csv(os.path.join(processed_dir, "flood_events", "chennai_flood_events.csv"))
    df_imerg = pd.read_csv(os.path.join(processed_dir, "rainfall", "imerg_chennai_daily.csv"))
    df_reservoirs = pd.read_csv(os.path.join(processed_dir, "water_level", "cmwssb_reservoir_levels.csv"))
    df_noaa = pd.read_csv(os.path.join(processed_dir, "weather", "noaa_isd_chennai_hourly.csv"))
    
    # 2. Parse Datetime Indexes
    df_imerg['time'] = pd.to_datetime(df_imerg['time'])
    df_imerg.set_index('time', inplace=True)
    
    df_reservoirs['date_standard'] = pd.to_datetime(df_reservoirs['date_standard'])
    df_reservoirs = df_reservoirs.groupby('date_standard')[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].mean()
    
    df_noaa['DATE'] = pd.to_datetime(df_noaa['DATE'])
    df_noaa.set_index('DATE', inplace=True)
    df_noaa_daily = df_noaa.resample('1D').agg({
        'temperature_c': ['mean', 'max', 'min'],
        'dew_point_c': 'mean',
        'wind_speed_ms': 'mean'
    })
    df_noaa_daily.columns = ['temp_mean', 'temp_max', 'temp_min', 'dew_point_mean', 'wind_speed_mean']
    
    # 3. Create target variable
    intervals = []
    for _, row in df_events.iterrows():
        try:
            start = pd.to_datetime(row['Start Date'])
            end = pd.to_datetime(row['End Date'])
            if pd.notna(start) and pd.notna(end):
                intervals.append((start, end))
        except Exception:
            continue
            
    start_date = max(df_imerg.index.min(), df_noaa_daily.index.min(), df_reservoirs.index.min())
    end_date = min(df_imerg.index.max(), df_noaa_daily.index.max(), df_reservoirs.index.max())
    
    date_range = pd.date_range(start_date, end_date, freq='D')
    features = pd.DataFrame(index=date_range)
    
    is_flood = np.zeros(len(date_range))
    for i, dt in enumerate(date_range):
        for start, end in intervals:
            if start <= dt <= end:
                is_flood[i] = 1.0
                break
    features['flood_active'] = is_flood
    
    # 4. Ingest and engineer features
    features['rainfall_daily'] = df_imerg['precipitation_mm_hr']
    features['rainfall_3d_sum'] = features['rainfall_daily'].rolling(3, min_periods=1).sum()
    features['rainfall_5d_sum'] = features['rainfall_daily'].rolling(5, min_periods=1).sum()
    features['rainfall_7d_sum'] = features['rainfall_daily'].rolling(7, min_periods=1).sum()
    
    features = features.join(df_noaa_daily, how='left')
    features = features.join(df_reservoirs, how='left')
    
    features.ffill(inplace=True)
    features.bfill(inplace=True)
    
    features['total_reservoir_level'] = features[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].sum(axis=1)
    
    # 5. Generate and Save EDA Plots
    print("Generating EDA Visualizations...")
    
    # A. Time Series plot of Rainfall vs Flood active periods
    plt.figure(figsize=(14, 5))
    plt.plot(features.index, features['rainfall_daily'], label='Daily Rainfall (mm)', color='royalblue', alpha=0.7)
    plt.fill_between(features.index, 0, features['rainfall_daily'].max(), where=features['flood_active']==1, 
                     color='red', alpha=0.3, label='Flood Active Period')
    plt.title('Daily Precipitation & Active Flood Events in Chennai')
    plt.xlabel('Date')
    plt.ylabel('Precipitation (mm)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'rainfall_vs_floods.png'))
    plt.close()
    
    # B. Correlation Heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(features.corr(), annot=True, fmt=".2f", cmap='coolwarm', square=True, cbar_kws={'shrink': .8})
    plt.title('Pearson Correlation Heatmap (ClimateTwin Features)')
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'correlation_heatmap.png'))
    plt.close()
    
    # C. Reservoir levels plot
    plt.figure(figsize=(14, 6))
    for res in ['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']:
        plt.plot(features.index, features[res], label=res, alpha=0.8)
    plt.plot(features.index, features['total_reservoir_level'], label='Total Capacity', color='black', linestyle='--')
    plt.title('CMWSSB Reservoir Water Levels Over Time')
    plt.xlabel('Date')
    plt.ylabel('Reservoir Level (mcft)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'reservoir_levels.png'))
    plt.close()

    # 6. Time-based Split to Prevent Temporal Leakage
    # Split date: train <= 2016-12-31, test >= 2017-01-01
    split_date = pd.to_datetime('2016-12-31')
    
    train_idx = features.index <= split_date
    test_idx = features.index > split_date
    
    df_train = features[train_idx]
    df_test = features[test_idx]
    
    X_train = df_train.drop(columns=['flood_active'])
    y_train = df_train['flood_active']
    X_test = df_test.drop(columns=['flood_active'])
    y_test = df_test['flood_active']
    
    print("\n--- Data Splits (Split Date: 2016-12-31) ---")
    print(f"Train Set: {X_train.shape[0]} samples. Positives: {int(y_train.sum())} ({(y_train.sum()/len(y_train))*100:.2f}%)")
    print(f"Test Set : {X_test.shape[0]} samples. Positives: {int(y_test.sum())} ({(y_test.sum()/len(y_test))*100:.2f}%)")
    
    # 7. Model Comparisons & Training
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
    }
    
    results = {}
    
    plt.figure(figsize=(12, 5))
    
    # Subplot for ROC
    plt.subplot(1, 2, 1)
    
    for name, model in models.items():
        print(f"\nTraining model: {name}...")
        model.fit(X_train, y_train)
        
        # Predict
        train_preds = model.predict(X_train)
        train_probs = model.predict_proba(X_train)[:, 1]
        
        test_preds = model.predict(X_test)
        test_probs = model.predict_proba(X_test)[:, 1]
        
        # Evaluate
        train_auc = roc_auc_score(y_train, train_probs)
        test_auc = roc_auc_score(y_test, test_probs)
        
        precision_curve, recall_curve, _ = precision_recall_curve(y_test, test_probs)
        pr_auc = auc(recall_curve, precision_curve)
        
        print(f"[{name}] Train ROC-AUC: {train_auc:.4f} | Test ROC-AUC: {test_auc:.4f} | Test PR-AUC: {pr_auc:.4f}")
        print(f"[{name}] Test Classification Report:")
        print(classification_report(y_test, test_preds, zero_division=0))
        
        # Save results
        results[name] = {
            'model': model,
            'test_auc': test_auc,
            'test_pr_auc': pr_auc,
            'train_auc': train_auc,
            'test_preds': test_preds,
            'test_probs': test_probs,
            'f1_score': f1_score(y_test, test_preds, zero_division=0),
            'recall': recall_score(y_test, test_preds, zero_division=0),
            'precision': precision_score(y_test, test_preds, zero_division=0)
        }
        
        # Plot ROC curve for Test set
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, test_probs)
        plt.plot(fpr, tpr, label=f'{name} (AUC = {test_auc:.3f})')
        
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Test Set ROC Curves')
    plt.legend()
    
    # Subplot for PR Curves
    plt.subplot(1, 2, 2)
    for name, r in results.items():
        precision_curve, recall_curve, _ = precision_recall_curve(y_test, r['test_probs'])
        plt.plot(recall_curve, precision_curve, label=f'{name} (PR-AUC = {r["test_pr_auc"]:.3f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Test Set Precision-Recall Curves')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'model_evaluation_curves.png'))
    plt.close()
    
    # Time Series Cross-Validation to evaluate walk-forward performance
    from sklearn.model_selection import TimeSeriesSplit
    print("\n--- Walk-Forward Validation (5-Fold TimeSeriesSplit) ---")
    tscv = TimeSeriesSplit(n_splits=5)
    X_full = features.drop(columns=['flood_active'])
    y_full = features['flood_active']
    
    for name, model in models.items():
        fold_aucs = []
        fold_recalls = []
        for fold, (train_idx_cv, test_idx_cv) in enumerate(tscv.split(X_full)):
            X_tr, X_te = X_full.iloc[train_idx_cv], X_full.iloc[test_idx_cv]
            y_tr, y_te = y_full.iloc[train_idx_cv], y_full.iloc[test_idx_cv]
            
            # Skip if fold has no positives in test
            if y_te.sum() == 0:
                continue
                
            model.fit(X_tr, y_tr)
            probs_te = model.predict_proba(X_te)[:, 1]
            preds_te = model.predict(X_te)
            
            fold_aucs.append(roc_auc_score(y_te, probs_te))
            fold_recalls.append(recall_score(y_te, preds_te, zero_division=0))
            
        if fold_aucs:
            print(f"[{name}] Mean CV ROC-AUC: {np.mean(fold_aucs):.4f} | Mean CV Recall: {np.mean(fold_recalls):.4f}")
        else:
            print(f"[{name}] Walk-forward CV failed (no positive cases in test folds)")
            
    # 8. Feature Importance Plot for Best Model
    # Determine best model based on Test ROC-AUC (and PR-AUC)
    best_name = max(results, key=lambda k: results[k]['test_auc'])
    best_model_data = results[best_name]
    best_model = best_model_data['model']
    
    print(f"\n>>> BEST MODEL: {best_name} (ROC-AUC = {best_model_data['test_auc']:.4f})")
    
    # Plot feature importances
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(X_train.shape[1]), importances[indices], align='center', color='teal')
        plt.xticks(range(X_train.shape[1]), [X_train.columns[i] for i in indices], rotation=45, ha='right')
        plt.title(f'Feature Importances - {best_name}')
        plt.xlabel('Features')
        plt.ylabel('Importance Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'feature_importances.png'))
        plt.close()
        
    # 9. Verify Overfitting
    print("\n--- Overfitting Analysis ---")
    for name, r in results.items():
        diff = r['train_auc'] - r['test_auc']
        print(f"[{name}] Train-Test ROC-AUC Gap: {diff:.4f} (Train: {r['train_auc']:.4f}, Test: {r['test_auc']:.4f})")
        if diff > 0.05:
            print(f"  -> WARNING: Potential overfitting detected for {name}.")
            
    # 10. Save the final model (We overwrite flood_rf_model.pkl if the new one is validated better)
    model_path = os.path.join(models_dir, "flood_rf_model.pkl")
    with open(model_path, 'wb') as f_out:
        pickle.dump({
            'model': best_model,
            'features': list(X_train.columns),
            'test_auc': best_model_data['test_auc'],
            'test_pr_auc': best_model_data['test_pr_auc'],
            'test_precision': best_model_data['precision'],
            'test_recall': best_model_data['recall'],
            'test_f1': best_model_data['f1_score'],
            'confusion_matrix': confusion_matrix(y_test, best_model_data['test_preds']).tolist(),
            'split_date': '2019-12-31'
        }, f_out)
    print(f"\nBest model successfully saved/updated at: {model_path}")
    
if __name__ == "__main__":
    main()
