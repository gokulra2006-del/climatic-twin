import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timezone, timedelta
from scipy import stats

class LiveFeatureAlignmentEngine:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            self.base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        else:
            self.base_dir = base_dir
            
        self.processed_dir = os.path.join(self.base_dir, "data", "processed")
        self.feature_cols = [
            'rainfall_daily', 'rainfall_3d_sum', 'rainfall_5d_sum', 'rainfall_7d_sum',
            'rainfall_rate_1h', 'rainfall_trend',
            'temp_mean', 'temp_max', 'temp_min', 'dew_point_mean', 'dew_point_depression',
            'wind_speed_mean', 'wind_speed_trend',
            'POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM',
            'total_reservoir_level', 'reservoir_fill_ratio', 'reservoir_storage_rate_1d'
        ]
        
        # Load historical feature distributions
        self.history_features = self._load_historical_features()
        self.distribution_stats = self._calculate_historical_distributions()

    def _load_historical_features(self):
        """Reconstruct the historical feature space for distribution comparisons."""
        # Load processed datasets
        df_imerg = pd.read_csv(os.path.join(self.processed_dir, 'rainfall', 'imerg_chennai_daily.csv'))
        df_reservoirs = pd.read_csv(os.path.join(self.processed_dir, 'water_level', 'cmwssb_reservoir_levels.csv'))
        df_noaa = pd.read_csv(os.path.join(self.processed_dir, 'weather', 'noaa_isd_chennai_hourly.csv'))
        
        # Prepare
        df_imerg['time'] = pd.to_datetime(df_imerg['time'])
        df_imerg.set_index('time', inplace=True)
        
        df_reservoirs['date_standard'] = pd.to_datetime(df_reservoirs['date_standard'])
        df_reservoirs = df_reservoirs.groupby('date_standard')[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].mean()
        
        df_noaa['DATE'] = pd.to_datetime(df_noaa['DATE'])
        df_noaa.set_index('DATE', inplace=True)
        df_noaa_daily = df_noaa.resample('1D').agg({
            'temperature_c': ['mean', 'max', 'min'],
            'dew_point_c': 'mean',
            'wind_speed_ms': 'mean'
        })
        df_noaa_daily.columns = ['temp_mean', 'temp_max', 'temp_min', 'dew_point_mean', 'wind_speed_mean']
        
        start_date = max(df_imerg.index.min(), df_noaa_daily.index.min(), df_reservoirs.index.min())
        end_date = min(df_imerg.index.max(), df_noaa_daily.index.max(), df_reservoirs.index.max())
        
        date_range = pd.date_range(start_date, end_date, freq='D')
        df_features = pd.DataFrame(index=date_range)
        
        # Build features
        df_features['rainfall_daily'] = df_imerg['precipitation_mm_hr'].reindex(date_range).fillna(0.0)
        df_features['rainfall_3d_sum'] = df_features['rainfall_daily'].rolling(3, min_periods=1).sum()
        df_features['rainfall_5d_sum'] = df_features['rainfall_daily'].rolling(5, min_periods=1).sum()
        df_features['rainfall_7d_sum'] = df_features['rainfall_daily'].rolling(7, min_periods=1).sum()
        
        df_features['rainfall_rate_1h'] = df_features['rainfall_daily'] / 24.0
        df_features['rainfall_trend'] = df_features['rainfall_daily'].diff().fillna(0.0)
        
        df_features = df_features.join(df_noaa_daily, how='left')
        df_features.ffill(inplace=True)
        df_features.bfill(inplace=True)
        df_features['dew_point_depression'] = (df_features['temp_mean'] - df_features['dew_point_mean']).clip(lower=0.0)
        df_features['wind_speed_trend'] = df_features['wind_speed_mean'].diff().fillna(0.0)
        
        df_features = df_features.join(df_reservoirs, how='left')
        df_features.ffill(inplace=True)
        df_features.bfill(inplace=True)
        df_features['total_reservoir_level'] = df_features[['POONDI', 'CHOLAVARAM', 'REDHILLS', 'CHEMBARAMBAKKAM']].sum(axis=1)
        MAX_CAPACITY = 11257.0
        df_features['reservoir_fill_ratio'] = (df_features['total_reservoir_level'] / MAX_CAPACITY).clip(0.0, 1.0)
        df_features['reservoir_storage_rate_1d'] = df_features['total_reservoir_level'].diff().fillna(0.0)

        df_features.ffill(inplace=True)
        df_features.bfill(inplace=True)
        return df_features[self.feature_cols]

    def _calculate_historical_distributions(self):
        stats_dict = {}
        for col in self.feature_cols:
            series = self.history_features[col].dropna()
            stats_dict[col] = {
                'mean': float(series.mean()),
                'median': float(series.median()),
                'min': float(series.min()),
                'max': float(series.max()),
                'std': float(series.std()),
                'p90': float(series.quantile(0.90)),
                'p95': float(series.quantile(0.95)),
                'p99': float(series.quantile(0.99))
            }
        return stats_dict

    def align_live_data(self, raw_telemetry: dict):
        """
        Takes raw live data and produces a strict 20-feature vector.
        """
        aligned = {}
        missing = []
        
        tail = self.history_features.iloc[-1].to_dict()
        
        try:
            # Rainfall
            aligned['rainfall_daily'] = float(raw_telemetry.get('precipitation', 0.0))
            aligned['rainfall_3d_sum'] = float(raw_telemetry.get('precipitation_3d', tail['rainfall_3d_sum']))
            aligned['rainfall_5d_sum'] = float(raw_telemetry.get('precipitation_5d', tail['rainfall_5d_sum']))
            aligned['rainfall_7d_sum'] = float(raw_telemetry.get('precipitation_7d', tail['rainfall_7d_sum']))
            aligned['rainfall_rate_1h'] = aligned['rainfall_daily'] / 24.0
            aligned['rainfall_trend'] = aligned['rainfall_daily'] - tail['rainfall_daily']
            
            # Weather
            aligned['temp_mean'] = float(raw_telemetry.get('temperature', tail['temp_mean']))
            aligned['temp_max'] = float(raw_telemetry.get('temperature_max', aligned['temp_mean'] + 2))
            aligned['temp_min'] = float(raw_telemetry.get('temperature_min', aligned['temp_mean'] - 2))
            aligned['dew_point_mean'] = float(raw_telemetry.get('dew_point', tail['dew_point_mean']))
            aligned['dew_point_depression'] = max(0.0, aligned['temp_mean'] - aligned['dew_point_mean'])
            aligned['wind_speed_mean'] = float(raw_telemetry.get('wind_speed', tail['wind_speed_mean']))
            aligned['wind_speed_trend'] = aligned['wind_speed_mean'] - tail['wind_speed_mean']
            
            # Reservoirs
            aligned['POONDI'] = float(raw_telemetry.get('poondi', tail['POONDI']))
            aligned['CHOLAVARAM'] = float(raw_telemetry.get('cholavaram', tail['CHOLAVARAM']))
            aligned['REDHILLS'] = float(raw_telemetry.get('redhills', tail['REDHILLS']))
            aligned['CHEMBARAMBAKKAM'] = float(raw_telemetry.get('chembarambakkam', tail['CHEMBARAMBAKKAM']))
            
            aligned['total_reservoir_level'] = aligned['POONDI'] + aligned['CHOLAVARAM'] + aligned['REDHILLS'] + aligned['CHEMBARAMBAKKAM']
            MAX_CAPACITY = 11257.0
            aligned['reservoir_fill_ratio'] = min(1.0, max(0.0, aligned['total_reservoir_level'] / MAX_CAPACITY))
            aligned['reservoir_storage_rate_1d'] = aligned['total_reservoir_level'] - tail['total_reservoir_level']
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid live data payload: {str(e)}")
            
        # Check against schema
        for col in self.feature_cols:
            if col not in aligned:
                missing.append(col)
                aligned[col] = tail[col] # degrade gracefully
                
        # Compare to distribution
        comparison = {}
        is_drifting = False
        drift_warnings = []
        
        for col in self.feature_cols:
            val = aligned[col]
            series = self.history_features[col].dropna()
            # Calculate percentile
            pctile = stats.percentileofscore(series, val, kind='rank')
            
            comp_obj = {
                'value': val,
                'historical_mean': self.distribution_stats[col]['mean'],
                'percentile': pctile
            }
            comparison[col] = comp_obj
            
            if pctile > 99.0 or pctile < 1.0:
                is_drifting = True
                drift_warnings.append(f"{col} at {pctile:.1f}th percentile")

        status = 'ALIGNED'
        if missing:
            status = 'DEGRADED PREDICTION'

        return {
            'status': status,
            'vector': [aligned[col] for col in self.feature_cols],
            'dict': aligned,
            'missing_features': missing,
            'comparison': comparison,
            'drift_detected': is_drifting,
            'drift_warnings': drift_warnings
        }
