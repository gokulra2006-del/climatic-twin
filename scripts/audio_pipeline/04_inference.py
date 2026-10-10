import librosa
import numpy as np
import joblib
import time
import os
import sys

MODEL_PATH = "../../models/audio/audio_classifier_rf.pkl"
LABEL_ENCODER_PATH = "../../models/audio/audio_labels.pkl"

def predict_audio(file_path):
    print(f"--- 5. INFERENCE SCRIPT ---")
    
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found. Train it first!")
        return

    if not os.path.exists(file_path):
        print(f"ERROR: Audio file {file_path} not found!")
        return

    print("Loading model...")
    model = joblib.load(MODEL_PATH)
    le = joblib.load(LABEL_ENCODER_PATH)
    
    print(f"Processing audio file: {file_path}")
    
    # 1. Start timer for latency
    start_time = time.time()
    
    # 2. Audio Preprocessing
    audio, sample_rate = librosa.load(file_path, sr=22050, res_type='kaiser_fast')
    mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
    mfcc_scaled = np.mean(mfccs.T, axis=0)
    
    # Model expects a 2D array, so we reshape [40] to [1, 40]
    features_2d = np.array([mfcc_scaled])
    
    # 3. Inference
    prediction_encoded = model.predict(features_2d)[0]
    prediction_text = le.inverse_transform([prediction_encoded])[0]
    
    # Confidence (probability)
    probabilities = model.predict_proba(features_2d)[0]
    confidence = probabilities[prediction_encoded] * 100
    
    # 4. End timer
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    print("\n--- INFERENCE RESULTS ---")
    print(f"Predicted Event  : {prediction_text.upper()}")
    print(f"Confidence       : {confidence:.2f}%")
    print(f"Inference Latency: {latency_ms:.2f} ms")

if __name__ == "__main__":
    # You can pass a path as a command line argument, or use a default one
    test_file = sys.argv[1] if len(sys.argv) > 1 else "sample_siren.wav"
    predict_audio(test_file)
