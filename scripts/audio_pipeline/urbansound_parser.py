import os
import pandas as pd
import shutil

# CONFIGURATION
# Where you extract the 5.6GB UrbanSound8K.tar.gz file
URBANSOUND_METADATA = "../../data/UrbanSound8K/metadata/UrbanSound8K.csv"
URBANSOUND_AUDIO_DIR = "../../data/UrbanSound8K/audio/"

# Where we want to output our sorted folders for the AI
OUTPUT_DIR = "../../data/audio_dataset/"

def extract_urbansound_classes():
    print("--- URBANSOUND8K DATASET EXTRACTOR ---")
    
    if not os.path.exists(URBANSOUND_METADATA):
        print(f"Waiting for download... Metadata CSV not found at {URBANSOUND_METADATA}")
        return

    # Load the metadata
    df = pd.read_csv(URBANSOUND_METADATA)
    
    # UrbanSound8K Class IDs:
    # 1 = car_horn
    # 5 = engine_idling (we will use this for normal traffic)
    # 8 = siren
    target_classes = {
        1: "horn",
        5: "traffic",
        8: "siren"
    }
    
    # Create output directories
    for class_name in target_classes.values():
        os.makedirs(os.path.join(OUTPUT_DIR, class_name), exist_ok=True)
        
    print("Extracting Sirens, Horns, and Traffic from the 5.6GB dataset...")
    
    count = 0
    for index, row in df.iterrows():
        classID = row["classID"]
        
        if classID in target_classes:
            folder = f"fold{row['fold']}"
            file_name = row["slice_file_name"]
            
            src_path = os.path.join(URBANSOUND_AUDIO_DIR, folder, file_name)
            dest_dir = os.path.join(OUTPUT_DIR, target_classes[classID])
            dest_path = os.path.join(dest_dir, file_name)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                count += 1
                
    print(f"Success! Extracted {count} high-quality audio files into {OUTPUT_DIR}")
    print("You can now run '01_dataset_prep.py'!")

if __name__ == "__main__":
    extract_urbansound_classes()
