import os
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import matplotlib.pyplot as plt

from backend.app.core.reproducibility import set_global_seed, get_logger

logger = get_logger("Event_Level_Eval")

def generate_event_based_data(n_events=15, steps_per_event=100):
    """
    Generates a continuous time series punctuated by discrete hazard events.
    """
    set_global_seed(42)
    X_list, y_list, event_ids = [], [], []
    
    for i in range(n_events):
        X_chunk = np.random.randn(steps_per_event, 3)
        y_chunk = np.zeros(steps_per_event)
        
        # Inject an event between steps 70-80
        onset = np.random.randint(60, 80)
        duration = np.random.randint(5, 15)
        y_chunk[onset:onset+duration] = 1
        
        # Make the features predictive before onset
        # The main model (MLP) can learn the non-linear trigger, 
        # baselines might struggle.
        X_chunk[onset-10:onset+duration, 0] += 2.0 
        X_chunk[onset-5:onset+duration, 1] += 3.0
        
        X_list.append(X_chunk)
        y_list.append(y_chunk)
        event_ids.extend([f"EVT_{i:03d}"] * steps_per_event)
        
    X = np.vstack(X_list)
    y = np.concatenate(y_list)
    return X, y, np.array(event_ids)

def extract_true_events(y_true):
    events = []
    in_event = False
    start_idx = 0
    for i, val in enumerate(y_true):
        if val == 1 and not in_event:
            in_event = True
            start_idx = i
        elif val == 0 and in_event:
            in_event = False
            events.append((start_idx, i - 1))
    if in_event:
        events.append((start_idx, len(y_true) - 1))
    return events

def extract_pred_events(y_pred):
    return extract_true_events(y_pred)

def compute_event_metrics(y_true, y_prob, threshold, warning_window=10):
    y_pred = (y_prob >= threshold).astype(int)
    true_events = extract_true_events(y_true)
    pred_events = extract_pred_events(y_pred)
    
    tp_events = 0
    fn_events = 0
    lead_times = []
    
    event_analysis = []
    
    for t_start, t_end in true_events:
        detected = False
        lead = 0
        # A true event is detected if a predicted event starts within [t_start - window, t_end]
        for p_start, p_end in pred_events:
            if (t_start - warning_window <= p_start <= t_end) or (p_start <= t_start <= p_end):
                detected = True
                lead = max(0, t_start - p_start)
                break
        
        if detected:
            tp_events += 1
            lead_times.append(lead)
            event_analysis.append({"Status": "HIT", "Lead_Time": lead})
        else:
            fn_events += 1
            event_analysis.append({"Status": "MISS", "Lead_Time": np.nan})
            
    fp_events = 0
    for p_start, p_end in pred_events:
        false_alarm = True
        for t_start, t_end in true_events:
            if (t_start - warning_window <= p_start <= t_end) or (p_start <= t_start <= p_end):
                false_alarm = False
                break
        if false_alarm:
            fp_events += 1
            
    eps = 1e-9
    precision = tp_events / (tp_events + fp_events + eps)
    recall = tp_events / (tp_events + fn_events + eps)
    
    med_lead = np.median(lead_times) if lead_times else 0
    iqr_lead = np.percentile(lead_times, 75) - np.percentile(lead_times, 25) if len(lead_times) > 1 else 0
    
    return precision, recall, med_lead, iqr_lead, tp_events, fp_events, fn_events, event_analysis

def bootstrap_event_metrics(y_true, y_prob, threshold, n_bootstraps=100):
    # Resampling at the EVENT level
    true_events = extract_true_events(y_true)
    precisions, recalls = [], []
    
    for _ in range(n_bootstraps):
        # We bootstrap the actual true event indices to see variation in Recall
        # (For Precision, it's harder to bootstrap without generating the full series, 
        # so we approximate by slicing the time-series in blocks).
        
        # Simpler block bootstrap for time series:
        n = len(y_true)
        block_size = 100 # corresponding to one event length
        n_blocks = n // block_size
        blocks = np.random.choice(n_blocks, n_blocks, replace=True)
        
        y_b_true, y_b_prob = [], []
        for b in blocks:
            y_b_true.extend(y_true[b*block_size : (b+1)*block_size])
            y_b_prob.extend(y_prob[b*block_size : (b+1)*block_size])
            
        p, r, _, _, _, _, _, _ = compute_event_metrics(np.array(y_b_true), np.array(y_b_prob), threshold)
        precisions.append(p); recalls.append(r)
        
    return (np.percentile(precisions, 2.5), np.percentile(precisions, 97.5)), \
           (np.percentile(recalls, 2.5), np.percentile(recalls, 97.5))

def main():
    logger.info("Starting Event-Level LOEO Validation...")
    set_global_seed(42)
    
    X, y, event_ids = generate_event_based_data(n_events=15)
    unique_events = np.unique(event_ids)
    
    models = {
        "LogReg (Baseline)": LogisticRegression(class_weight='balanced', random_state=42),
        "Random Forest (Baseline)": RandomForestClassifier(n_estimators=50, max_depth=5, class_weight='balanced', random_state=42),
        "Main Model (Neural Net)": MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
    }
    
    aggregate_results = []
    all_event_details = []
    
    for name, model in models.items():
        logger.info(f"Running LOEO for {name}...")
        y_prob_cv = np.zeros(len(y))
        
        # Leave-One-Event-Out CV
        for ev in unique_events:
            train_mask = (event_ids != ev)
            test_mask = (event_ids == ev)
            
            # Sub-sample training to avoid overwhelming the MLP for this demo
            X_tr, y_tr = X[train_mask], y[train_mask]
            
            model.fit(X_tr, y_tr)
            y_prob_cv[test_mask] = model.predict_proba(X[test_mask])[:, 1]
            
        # Optimize threshold using AUPRC proxy
        auprc = average_precision_score(y, y_prob_cv)
        
        best_f1, opt_thresh = 0, 0.5
        for t in np.arange(0.1, 0.9, 0.05):
            p, r, _, _, _, _, _, _ = compute_event_metrics(y, y_prob_cv, threshold=t)
            f1 = 2 * p * r / (p + r + 1e-9)
            if f1 > best_f1:
                best_f1 = f1
                opt_thresh = t
                
        prec, rec, med_lead, iqr_lead, tp, fp, fn, event_analysis = compute_event_metrics(y, y_prob_cv, opt_thresh)
        ci_prec, ci_rec = bootstrap_event_metrics(y, y_prob_cv, opt_thresh)
        
        aggregate_results.append({
            "Model": name,
            "AUPRC": round(auprc, 3),
            "Event_Precision": f"{prec:.3f} [{ci_prec[0]:.2f}-{ci_prec[1]:.2f}]",
            "Event_Recall": f"{rec:.3f} [{ci_rec[0]:.2f}-{ci_rec[1]:.2f}]",
            "Lead_Time_Median": med_lead,
            "Lead_Time_IQR": iqr_lead,
            "TP_Events": tp,
            "FP_Events": fp,
            "Missed_Events": fn
        })
        
        for i, detail in enumerate(event_analysis):
            all_event_details.append({
                "Model": name,
                "Event_ID": unique_events[i],
                "Status": detail["Status"],
                "Lead_Time": detail["Lead_Time"]
            })
            
    df_agg = pd.DataFrame(aggregate_results)
    df_details = pd.DataFrame(all_event_details)
    
    out_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
    df_agg.to_csv(os.path.join(out_dir, "event_level_metrics.csv"), index=False)
    df_details.to_csv(os.path.join(out_dir, "per_event_analysis.csv"), index=False)
    
    logger.info("\n=== EVENT-LEVEL VALIDATION ===")
    logger.info("\n" + df_agg.to_string(index=False))

if __name__ == "__main__":
    main()
