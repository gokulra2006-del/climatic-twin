import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import os

MODEL_PATH = "../../models/audio/audio_classifier_rf.pkl"
LABEL_ENCODER_PATH = "../../models/audio/audio_labels.pkl"

def evaluate_model():
    print(f"--- 3 & 4. VALIDATION AND EVALUATION SCRIPT ---")
    
    if not os.path.exists("X_test.npy"):
        print("ERROR: Test data not found. Run 02_train_and_export.py first!")
        return
        
    print("Loading model and test data...")
    model = joblib.load(MODEL_PATH)
    le = joblib.load(LABEL_ENCODER_PATH)
    
    X_test = np.load("X_test.npy")
    y_test = np.load("y_test.npy")
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    acc = accuracy_score(y_test, y_pred)
    print(f"\n--- CORE METRICS ---")
    print(f"Overall Accuracy: {acc * 100:.2f}%\n")
    
    # precision, recall, f1-score per class
    print("--- DETAILED REPORT (Precision, Recall, F1-Score) ---")
    # target_names maps the number back to the text (e.g. '0' -> 'siren')
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    print("\n--- CONFUSION MATRIX ---")
    cm = confusion_matrix(y_test, y_pred)
    print("Columns = Predicted, Rows = Actual")
    print(cm)
    
    # Calculate False Positive Rate (FPR) for each class
    # FPR = FP / (FP + TN)
    print("\n--- FALSE POSITIVE RATES ---")
    for i, class_name in enumerate(le.classes_):
        FP = cm[:, i].sum() - cm[i, i]
        TN = cm.sum() - (cm[:, i].sum() + cm[i, :].sum() - cm[i, i])
        FPR = FP / (FP + TN) if (FP + TN) > 0 else 0
        print(f"Class '{class_name}': FPR = {FPR:.4f}")

if __name__ == "__main__":
    evaluate_model()
