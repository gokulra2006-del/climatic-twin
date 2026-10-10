from ultralytics import YOLO
import os

def validate_model(model_path, is_classification=False):
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found. Please train first.")
        return

    print(f"\n--- 3 & 4. VALIDATION & EVALUATION: {model_path} ---")
    model = YOLO(model_path)
    
    # YOLO automatically calculates metrics on the validation set
    metrics = model.val()
    
    if not is_classification:
        print("\n--- DETECTION METRICS ---")
        # mAP@50 is mean Average Precision at 50% IoU
        # mAP@50-95 is the strict metric across multiple IoU thresholds
        print(f"Precision: {metrics.results_dict['metrics/precision(B)']:.4f}")
        print(f"Recall:    {metrics.results_dict['metrics/recall(B)']:.4f}")
        print(f"mAP@50:    {metrics.results_dict['metrics/mAP50(B)']:.4f}")
        print(f"mAP@50-95: {metrics.results_dict['metrics/mAP50-95(B)']:.4f}")
    else:
        print("\n--- CLASSIFICATION METRICS ---")
        print(f"Top-1 Accuracy: {metrics.results_dict['metrics/accuracy_top1']:.4f}")
        print(f"Top-5 Accuracy: {metrics.results_dict['metrics/accuracy_top5']:.4f}")
        # Note: Precision/Recall/F1/Confusion matrix are saved as images and CSVs 
        # inside the runs/val folder by Ultralytics automatically.
        print(f"Detailed Confusion Matrix saved to the validation output directory.")

if __name__ == "__main__":
    # Example paths (YOLO saves models in project/name/weights/best.pt)
    # validate_model("../../models/vision/vehicle_model/weights/best.pt", is_classification=False)
    # validate_model("../../models/vision/fire_smoke_model/weights/best.pt", is_classification=True)
    pass
