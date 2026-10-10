import os
import librosa
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

# CONFIGURATION
# IMPORTANT: Change this to the folder where your audio files are stored!
# E.g., DATASET_PATH = "C:/Users/gokul/Downloads/my_sound_dataset"
DATASET_PATH = "../data/audio_dataset" 
FEATURES_OUTPUT = "extracted_features.csv"

def extract_features(file_path):
    """
    Extracts MFCC features from an audio file.
    MFCCs (Mel-Frequency Cepstral Coefficients) act like a "fingerprint" of the sound.
    """
    try:
        # Load audio file (resampled to 22050 Hz for consistency)
        audio, sample_rate = librosa.load(file_path, sr=22050, res_type='kaiser_fast')
        
        # Extract exactly 40 MFCCs
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        
        # Take the mean of each MFCC across the time axis to get a 1D array of 40 numbers
        mfcc_scaled = np.mean(mfccs.T, axis=0)
        return mfcc_scaled
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def prepare_dataset():
    print(f"--- 1. DATASET PREPARATION ---")
    print(f"Scanning for audio files in: {DATASET_PATH}")
    
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: The folder {DATASET_PATH} does not exist!")
        print("Please place your audio files in class folders (e.g., /siren, /horn, /crash)")
        return
        
    features = []
    labels = []
    
    # We assume the dataset has subfolders for each class, e.g.:
    # DATASET_PATH/
    #   siren/
    #     sound1.wav
    #   horn/
    #     sound2.wav
    classes = [d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))]
    print(f"Discovered {len(classes)} classes: {classes}")
    
    for class_name in classes:
        class_dir = os.path.join(DATASET_PATH, class_name)
        files = [f for f in os.listdir(class_dir) if f.endswith(('.wav', '.mp3', '.ogg'))]
        print(f"Found {len(files)} files in class '{class_name}'...")
        
        for file_name in files:
            file_path = os.path.join(class_dir, file_name)
            data = extract_features(file_path)
            if data is not None:
                features.append(data)
                labels.append(class_name)
                
    # Save to a CSV so we don't have to extract features every time we train
    df = pd.DataFrame(features)
    df['label'] = labels
    df.to_csv(FEATURES_OUTPUT, index=False)
    print(f"\nSuccess! Extracted features for {len(features)} audio files.")
    print(f"Saved to {FEATURES_OUTPUT}. You can now run the training script.")

if __name__ == "__main__":
    prepare_dataset()
