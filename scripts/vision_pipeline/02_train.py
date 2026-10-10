from ultralytics import YOLO
import os

# Strong Technical Reason Note:
# Running 5 separate AI models on a Raspberry Pi will exhaust its RAM and cause the camera to drop to <1 FPS.
# If these tasks operate on the same camera feed, combining them into ONE multi-class YOLO model is highly recommended for edge devices.
# However, as requested, these are kept separate.

def train_detection(dataset_yaml, model_export_name):
    print(f"\n--- TRAINING DETECTION MODEL: {model_export_name} ---")
    if not os.path.exists(dataset_yaml):
        print(f"Skipping {model_export_name} - dataset yaml {dataset_yaml} not found.")
        return
        
    # We use YOLOv8 Nano (yolov8n.pt) because it is the most lightweight SOTA model for Raspberry Pi.
    model = YOLO("yolov8n.pt") 
    
    # Train the model (epochs=50 is good for beginners/testing)
    model.train(data=dataset_yaml, epochs=50, imgsz=640, project="../../models/vision", name=model_export_name)

def train_classification(dataset_folder, model_export_name):
    print(f"\n--- TRAINING CLASSIFICATION MODEL: {model_export_name} ---")
    if not os.path.exists(dataset_folder):
        print(f"Skipping {model_export_name} - dataset {dataset_folder} not found.")
        return
        
    # We use YOLOv8 Nano Classification model (yolov8n-cls.pt)
    model = YOLO("yolov8n-cls.pt")
    
    model.train(data=dataset_folder, epochs=50, imgsz=224, project="../../models/vision", name=model_export_name)

if __name__ == "__main__":
    print("--- 2. TRAINING PIPELINE ---")
    # Uncomment these once you place the datasets in data/vision_datasets/
    
    # train_detection("../../data/vision_datasets/vehicle_detection/data.yaml", "vehicle_model")
    # train_detection("../../data/vision_datasets/accident_detection/data.yaml", "accident_model")
    # train_classification("../../data/vision_datasets/fire_smoke_classification/", "fire_smoke_model")
    
    print("Run this script after populating the datasets!")
