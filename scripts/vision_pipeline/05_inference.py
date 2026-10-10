from ultralytics import YOLO
import time
import os
import sys

def infer_image(model_path, image_path):
    print(f"\n--- 5. INFERENCE: {image_path} ---")
    if not os.path.exists(model_path) or not os.path.exists(image_path):
        print("Model or Image not found.")
        return

    model = YOLO(model_path)
    
    start_time = time.time()
    results = model(image_path)
    end_time = time.time()
    
    latency_ms = (end_time - start_time) * 1000
    fps = 1000 / latency_ms if latency_ms > 0 else 0
    
    print("\n--- INFERENCE RESULTS ---")
    print(f"Latency: {latency_ms:.2f} ms")
    print(f"Estimated FPS: {fps:.2f} frames per second")
    
    # Save the output image with bounding boxes/labels drawn
    for r in results:
        r.save(filename=f"inference_result.jpg")
    print("Result saved as inference_result.jpg")

if __name__ == "__main__":
    # infer_image("../../models/vision/vehicle_model/weights/best.pt", "test_image.jpg")
    pass
