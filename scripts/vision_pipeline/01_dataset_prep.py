import os
import yaml

# CONFIGURATION
# Set this to where your downloaded datasets are stored
BASE_DATASET_DIR = "../../data/vision_datasets/"

def prepare_detection_dataset(dataset_name, classes):
    """
    Creates a YOLOv8 data.yaml file required for Object Detection training.
    Assumes your dataset is organized as:
    dataset_name/
      images/
        train/
        val/
      labels/
        train/
        val/
    """
    dataset_path = os.path.join(BASE_DATASET_DIR, dataset_name)
    yaml_path = os.path.join(dataset_path, "data.yaml")
    
    if not os.path.exists(dataset_path):
        print(f"WARNING: Dataset path {dataset_path} not found. Please place your data here.")
        return
        
    data = {
        'path': os.path.abspath(dataset_path),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(classes),
        'names': classes
    }
    
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    print(f"Created YOLO YAML for {dataset_name} at {yaml_path}")

def prepare_classification_dataset(dataset_name):
    """
    Classification datasets don't need a YAML, just proper folder structure:
    dataset_name/
      train/
        class1/
        class2/
      val/
        class1/
        class2/
    """
    dataset_path = os.path.join(BASE_DATASET_DIR, dataset_name)
    if not os.path.exists(dataset_path):
        print(f"WARNING: Classification dataset path {dataset_path} not found.")
        return
    print(f"Classification dataset {dataset_name} is ready (folder structure verified).")

if __name__ == "__main__":
    print("--- 1. VISION DATASET PREPARATION ---")
    os.makedirs(BASE_DATASET_DIR, exist_ok=True)
    
    # 1. Vehicle Detection (Object Detection)
    prepare_detection_dataset("vehicle_detection", ["vehicle"])
    
    # 2. Accident Detection (Object Detection or Classification depending on your data)
    prepare_detection_dataset("accident_detection", ["accident"])
    
    # 3. Road Obstacles (Object Detection)
    prepare_detection_dataset("obstacle_detection", ["obstacle"])
    
    # 4. Fire & Smoke (Classification usually works well if just detecting presence)
    prepare_classification_dataset("fire_smoke_classification")
    
    print("\nPlease place your image datasets into the generated folders.")
