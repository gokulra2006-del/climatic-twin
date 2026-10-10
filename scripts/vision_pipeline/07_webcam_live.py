import cv2
from ultralytics import YOLO
import time
import os

def live_webcam_inference(model_path):
    print(f"\n--- 7. LIVE WEBCAM INFERENCE ---")
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}. Please train or export first.")
        return

    # Load the model (use the exported .ncnn or .tflite model if on Raspberry Pi)
    model = YOLO(model_path)
    
    # Open the default webcam (0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        start_time = time.time()
        
        # Run YOLO inference
        # stream=True is a generator and heavily speeds up continuous feeds
        results = model(frame, stream=True, verbose=False) 
        
        for r in results:
            # Draw the bounding boxes and labels on the frame
            annotated_frame = r.plot()
            
            # Calculate Latency and FPS
            latency_ms = (time.time() - start_time) * 1000
            fps = 1000 / latency_ms if latency_ms > 0 else 0
            
            # Add FPS counter to the top left of the video feed
            cv2.putText(annotated_frame, f"FPS: {fps:.1f} | Latency: {latency_ms:.1f}ms", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Show the video feed
            cv2.imshow("Vision AI Live Feed", annotated_frame)
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Point this to your NCNN or TFLite exported model for Raspberry Pi tests!
    # live_webcam_inference("../../models/vision/vehicle_model/weights/best.pt")
    pass
