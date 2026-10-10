import os
import random
import time
import numpy as np

# Try importing ML libraries, gracefully handle if not installed yet
try:
    import librosa
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

class Microphone:
    def __init__(self, mode="SIMULATION"):
        self.mode = os.getenv("SENSOR_MODE", mode).upper()
        
        # Paths to your trained Audio AI model
        self.model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'audio', 'audio_classifier_rf.pkl'))
        self.label_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'audio', 'audio_labels.pkl'))
        
        self.ai_model = None
        self.ai_labels = None
        
        print(f"Initializing Microphone in {self.mode} mode.")
        self._load_ai_model()

    def _load_ai_model(self):
        """Attempts to load the trained AI model if it exists."""
        if ML_AVAILABLE and os.path.exists(self.model_path) and os.path.exists(self.label_path):
            try:
                self.ai_model = joblib.load(self.model_path)
                self.ai_labels = joblib.load(self.label_path)
                print("[SUCCESS] Live Audio AI Model successfully loaded into Microphone module!")
            except Exception as e:
                print(f"[WARNING] Could not load Audio AI model: {e}")
        else:
            print("[WARNING] Trained Audio AI model not found. Microphone will use smart simulation until you finish training.")

    def record_audio(self, duration_sec: int = 2) -> str:
        if self.mode == "SIMULATION":
            return "simulated_audio_clip.wav"
        else:
            raise NotImplementedError("Real hardware Microphone logic not implemented yet.")
            
    def analyze_audio(self, test_audio_file: str = None) -> dict:
        """
        Records an audio clip and automatically calls the Audio AI module to classify it.
        If the real AI model is trained and available, it runs real inference!
        """
        filepath = test_audio_file if test_audio_file else self.record_audio()
        
        # --- REAL AI INFERENCE ---
        if self.ai_model and self.ai_labels and test_audio_file and os.path.exists(test_audio_file):
            print(f"🎤 Running LIVE AI INFERENCE on {test_audio_file}...")
            try:
                audio, sample_rate = librosa.load(test_audio_file, sr=22050, res_type='kaiser_fast')
                mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
                mfcc_scaled = np.mean(mfccs.T, axis=0)
                
                features_2d = np.array([mfcc_scaled])
                prediction_encoded = self.ai_model.predict(features_2d)[0]
                detected_event = self.ai_labels.inverse_transform([prediction_encoded])[0]
                
                probabilities = self.ai_model.predict_proba(features_2d)[0]
                confidence = probabilities[prediction_encoded] * 100
                
                return {
                    "file": filepath,
                    "detected_event": detected_event.upper(),
                    "confidence": round(confidence, 2)
                }
            except Exception as e:
                print(f"Error during live inference: {e}. Falling back to simulation.")

        # --- SIMULATED INFERENCE (Fallback while downloading/training) ---
        classes = ["NORMAL_TRAFFIC", "SIREN", "HORN", "CRASH"]
        simulated_class = random.choices(classes, weights=[0.7, 0.1, 0.1, 0.1])[0]
        confidence = round(random.uniform(70.0, 99.9), 2)
        
        return {
            "file": filepath,
            "detected_event": simulated_class,
            "confidence": confidence
        }

if __name__ == "__main__":
    sensor = Microphone("SIMULATION")
    result = sensor.analyze_audio()
    print(f"Audio AI Result: {result}")
