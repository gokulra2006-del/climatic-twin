from ultralytics import YOLO
import os

def export_for_raspberry_pi(model_path):
    """
    Exports a trained YOLOv8 model to NCNN or TFLite formats.
    These formats are highly optimized for edge devices like Raspberry Pi.
    """
    print(f"\n--- 6. MODEL EXPORT ---")
    if not os.path.exists(model_path):
        print("Model not found. Train first.")
        return
        
    model = YOLO(model_path)
    
    # Export to NCNN (extremely fast on Raspberry Pi ARM CPUs)
    print("Exporting to NCNN format...")
    model.export(format="ncnn")
    
    # Export to TFLite (TensorFlow Lite - standard for edge devices)
    print("Exporting to TFLite format...")
    model.export(format="tflite")
    
    print("Export complete! Move the generated folder/files to your Raspberry Pi.")

if __name__ == "__main__":
    # export_for_raspberry_pi("../../models/vision/vehicle_model/weights/best.pt")
    pass
