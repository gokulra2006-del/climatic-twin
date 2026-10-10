import pandas as pd
import numpy as np
import os
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler

class HistoricalAnalogEngine:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        else:
            self.base_dir = base_dir
            
        self.processed_dir = os.path.join(self.base_dir, "data", "processed")
        
        try:
            from app.core.live_feature_alignment import LiveFeatureAlignmentEngine
        except ImportError:
            from backend.app.core.live_feature_alignment import LiveFeatureAlignmentEngine
        self.aligner = LiveFeatureAlignmentEngine(self.base_dir)
        self.history_features = self.aligner.history_features.copy()
        
        # Drop NaNs
        self.history_features.dropna(inplace=True)
        
        # Load flood labels to return outcome status for analogs
        self.df_events = pd.read_csv(os.path.join(self.processed_dir, 'flood_events', 'chennai_flood_events.csv'))
        # Fit standard scaler for distance computation on feature columns only
        self.feature_cols = self.aligner.feature_cols
        self.scaler = StandardScaler()
        self.scaler.fit(self.history_features[self.feature_cols])
        self.history_scaled = self.scaler.transform(self.history_features[self.feature_cols])
        self._map_historical_labels()

    def _map_historical_labels(self):
        intervals = []
        for _, row in self.df_events.iterrows():
            try:
                start = pd.to_datetime(row['Start Date'])
                end = pd.to_datetime(row['End Date'])
                if pd.notna(start) and pd.notna(end):
                    intervals.append((start, end))
            except Exception:
                continue
                
        is_flood = np.zeros(len(self.history_features))
        for i, dt in enumerate(self.history_features.index):
            for start, end in intervals:
                if start <= dt <= end:
                    is_flood[i] = 1.0
                    break
        self.history_features['flood_active'] = is_flood

    def find_analogs(self, live_vector: list, top_k: int = 3):
        """
        Find the most similar historical dates using Standardized Euclidean Distance.
        """
        # Scale the live vector
        live_scaled = self.scaler.transform([live_vector])
        
        # Compute distances
        distances = cdist(live_scaled, self.history_scaled, metric='euclidean')[0]
        
        # Find closest k indices
        closest_indices = np.argsort(distances)[:top_k]
        
        analogs = []
        # Calculate a similarity score (100% being identical)
        max_dist = np.max(distances) if len(distances) > 0 else 1.0
        
        for idx in closest_indices:
            dt = self.history_features.index[idx]
            dist = distances[idx]
            # Heuristic similarity percentage
            similarity = max(0.0, 100.0 * (1.0 - (dist / max_dist)))
            
            analogs.append({
                'date': dt.strftime('%Y-%m-%d'),
                'similarity_pct': round(similarity, 1),
                'flood_status': bool(self.history_features.iloc[idx]['flood_active']),
                'key_metrics': {
                    'rainfall_7d_sum': round(self.history_features.iloc[idx]['rainfall_7d_sum'], 1),
                    'total_reservoir_level': round(self.history_features.iloc[idx]['total_reservoir_level'], 1)
                }
            })
            
        return analogs
