import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os

FEATURES_FILE = "extracted_features.csv"
MODEL_EXPORT_PATH = "../../models/audio/audio_classifier_rf.pkl"
LABEL_ENCODER_PATH = "../../models/audio/audio_labels.pkl"

def train_and_export():
    print(f"--- 2 & 6. TRAINING AND EXPORT SCRIPT ---")
    
    if not os.path.exists(FEATURES_FILE):
        print(f"ERROR: {FEATURES_FILE} not found. Run 01_dataset_prep.py first!")
        return
        
    print("Loading features...")
    df = pd.DataFrame(pd.read_csv(FEATURES_FILE))
    
    # X contains the 40 MFCC features, y contains the text labels (e.g., 'siren')
    X = df.drop('label', axis=1).values
    y = df['label'].values
    
    # Convert text labels into numbers so the ML model can understand them
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Split data: 80% for training, 20% for testing/validation
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    print(f"Training data: {len(X_train)} samples")
    print(f"Validation data: {len(X_test)} samples")
    
    # We use a Random Forest because it is lightweight, runs easily on a laptop, 
    # and is perfect for tabular MFCC features.
    print("\nTraining Random Forest model (this should be very fast)...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Quick validation check on the training script
    acc = model.score(X_test, y_test)
    print(f"Initial Validation Accuracy: {acc * 100:.2f}%")
    
    # Export (Script 6 requirement)
    print(f"\nExporting trained model to {MODEL_EXPORT_PATH}...")
    joblib.dump(model, MODEL_EXPORT_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    
    # Save the test set for the separate evaluation script
    np.save("X_test.npy", X_test)
    np.save("y_test.npy", y_test)
    
    print("Done! Model is saved and ready for evaluation and inference.")

if __name__ == "__main__":
    train_and_export()
