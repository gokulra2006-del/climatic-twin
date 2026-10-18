import React, { useState, useEffect } from 'react';
import { 
  Shield, Activity, Clock, Radio, Database, Terminal, CheckCircle2, 
  AlertTriangle, Server, Network, Layers, Zap, Info, X, CloudRain,
  ThermometerSun, Wind, Droplets, Map, TrendingUp, TrendingDown, Minus,
  History, Sparkles, BookOpen, AlertOctagon, BarChart3, RefreshCw
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Used only when the optional local API is unavailable.  Keeping this payload
// explicit prevents an offline demo from being presented as live telemetry.
const PROTOTYPE_LIVE_INTELLIGENCE = {
  timestamp: 'Prototype scenario snapshot',
  feature_alignment: { status: 'ALIGNED', missing_features: [] },
  historical_comparison: {
    rainfall_7d_sum: { value: 42.0, historical_mean: 38.6, percentile: 61 },
    total_reservoir_level: { value: 8_120.0, historical_mean: 7_760.0, percentile: 58 },
    rainfall_daily: { value: 8.4, historical_mean: 6.9, percentile: 64 },
    temp_max: { value: 31.2, historical_mean: 32.1, percentile: 45 },
  },
  historical_analogs: [
    { date: '2019-11-06', similarity_pct: 83, flood_status: false, key_metrics: { total_reservoir_level: 7_940, rainfall_7d_sum: 39.0 } },
    { date: '2017-10-30', similarity_pct: 76, flood_status: false, key_metrics: { total_reservoir_level: 8_010, rainfall_7d_sum: 44.0 } },
  ],
  prediction: { risk_level: 'LOW', probability: 0.12, state: 0 },
  uncertainty: { p10: 0.05, p90: 0.22, width: 0.17 },
  explainability: [
    { feature: 'rainfall_7d_sum', importance: 0.34 },
    { feature: 'total_reservoir_level', importance: 0.28 },
    { feature: 'rainfall_daily', importance: 0.22 },
    { feature: 'temp_max', importance: 0.16 },
  ],
  model: { name: 'Prototype temporal flood-risk model', latency_ms: 'Offline demo' },
  nova_summary: {
    situation: 'Low prototype flood-risk index under the saved demonstration scenario.',
    model_outlook: 'No threshold crossing is projected within the prototype horizon.',
    drivers: 'Seven-day rainfall and combined reservoir level are the largest contributors.',
    context: 'Closest archived patterns are nominal comparison periods, not validated flood impacts.',
  },
};

export default function LiveFloodIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchLiveIntelligence = async () => {
    try {
      setIsRefreshing(true);
      const response = await fetch(`${API_URL}/api/predictions/live`);
      if (!response.ok) throw new Error("Failed to fetch live intelligence");
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setData(PROTOTYPE_LIVE_INTELLIGENCE);
      setError('Live backend is unavailable. Showing a clearly labelled saved prototype scenario.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLiveIntelligence();
    const interval = setInterval(fetchLiveIntelligence, 30000); // 30s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-500 space-y-4">
        <Activity className="h-10 w-10 animate-spin text-indigo-600" />
        <p className="text-xs uppercase font-bold tracking-wider text-slate-600">Connecting to Chennai telemetry pipeline...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-2xl flex items-start gap-4">
        <AlertTriangle className="h-6 w-6 text-red-600 shrink-0" />
        <div>
          <h3 className="font-bold text-sm mb-1">Live Telemetry Pipeline Error</h3>
          <p className="text-xs text-red-700">{error}</p>
          <button 
            onClick={fetchLiveIntelligence} 
            className="mt-3 px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const {
    timestamp,
    feature_alignment,
    historical_comparison,
    historical_analogs,
    prediction,
    uncertainty,
    explainability,
    model,
    nova_summary
  } = data;

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'text-white bg-red-600 border-red-700';
      case 'HIGH': return 'text-white bg-orange-500 border-orange-600';
      case 'MODERATE': return 'text-amber-950 bg-amber-400 border-amber-500';
      default: return 'text-white bg-emerald-600 border-emerald-700';
    }
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12 font-sans">
      
      {/* 1. CLEAN LIGHT HEADER */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
            <Radio className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
                Real-Time Flood Intelligence
              </h2>
              <span className={`text-[10px] px-2.5 py-0.5 rounded-full border font-bold uppercase tracking-wider ${error ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'}`}>
                {error ? 'Saved prototype scenario' : 'Live Open-Meteo synced'}
              </span>
            </div>
            <p className="text-slate-500 text-xs mt-0.5 font-medium">
              Greater Chennai Basin Assimilation • Feature Alignment • Historical Analog Matching
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-50 px-3 py-2 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Inference Model</span>
            <span className="font-bold text-slate-800">{model.name}</span>
          </div>
          <div className="bg-slate-50 px-3 py-2 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Latency</span>
            <span className="font-bold text-emerald-600">{model.latency_ms} ms</span>
          </div>
          <button
            onClick={fetchLiveIntelligence}
            disabled={isRefreshing}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200 disabled:opacity-50"
            title="Refresh Live Data"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3 text-amber-950">
          <Info className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <span className="font-bold">Prototype mode:</span> {error}
            <button onClick={fetchLiveIntelligence} className="ml-3 underline font-bold text-amber-900 hover:text-amber-700">
              Retry connection
            </button>
          </div>
        </div>
      )}

      {/* 2. ALIGNMENT WARNING (if any) */}
      {feature_alignment.status !== 'ALIGNED' && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center gap-3 text-amber-900">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
          <div className="text-xs">
            <span className="font-bold">DEGRADED FEATURE ALIGNMENT:</span> Missing telemetry ({feature_alignment.missing_features.join(', ')}). Falling back to historical distribution baseline.
          </div>
        </div>
      )}

      {/* 3. OPERATIONAL SITUATION ASSESSMENT (Clean Light Card) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-xs font-bold text-slate-500 flex items-center gap-2 mb-4 uppercase tracking-wider border-b border-slate-100 pb-2">
          <Sparkles className="h-4 w-4 text-indigo-600" /> Operational Flood Situation Assessment
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="text-slate-500 font-bold block mb-1 uppercase text-[10px]">CURRENT SITUATION</span>
            <span className="text-slate-800 font-medium leading-relaxed">{nova_summary.situation}</span>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="text-slate-500 font-bold block mb-1 uppercase text-[10px]">MODEL OUTLOOK</span>
            <span className="text-slate-800 font-medium leading-relaxed">{nova_summary.model_outlook}</span>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="text-slate-500 font-bold block mb-1 uppercase text-[10px]">PRIMARY DRIVERS</span>
            <span className="text-slate-800 font-medium leading-relaxed">{nova_summary.drivers}</span>
          </div>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
            <span className="text-slate-500 font-bold block mb-1 uppercase text-[10px]">HISTORICAL ANALOG</span>
            <span className="text-slate-800 font-medium leading-relaxed">{nova_summary.context}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Calibrated Risk & Uncertainty */}
        <div className="xl:col-span-4 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col items-center justify-center">
            <h3 className="text-xs font-bold text-slate-500 tracking-wider uppercase mb-6 flex items-center gap-2 w-full border-b border-slate-100 pb-2">
              <Shield className="h-4 w-4 text-indigo-600" /> Calibrated Flood Risk Index
            </h3>
            
            <div className="my-4 text-center">
              <span className={`text-2xl font-black px-5 py-1.5 rounded-xl border uppercase tracking-wider ${getRiskBadgeColor(prediction.risk_level)}`}>
                {prediction.risk_level}
              </span>
              <div className="flex items-end justify-center gap-1 mt-6">
                <span className="text-5xl font-black text-slate-900">{(prediction.probability * 100).toFixed(1)}</span>
                <span className="text-xl font-bold text-slate-500 mb-1">%</span>
              </div>
              <p className="text-[11px] uppercase font-bold text-slate-500 mt-2">Inundation Likelihood</p>
            </div>
            
            <div className="w-full mt-4 p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs">
              <div className="flex justify-between text-[11px] mb-2 text-slate-600 font-medium">
                <span>P10: <strong>{(uncertainty.p10 * 100).toFixed(1)}%</strong></span>
                <span className="font-bold text-slate-700">90% Confidence Interval</span>
                <span>P90: <strong>{(uncertainty.p90 * 100).toFixed(1)}%</strong></span>
              </div>
              <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden relative">
                <div 
                  className="absolute top-0 bottom-0 bg-indigo-200"
                  style={{ left: `${Math.max(0, uncertainty.p10 * 100)}%`, right: `${Math.max(0, 100 - (uncertainty.p90 * 100))}%` }}
                ></div>
                <div 
                  className="absolute top-0 bottom-0 w-2.5 bg-indigo-600 rounded-full shadow-sm"
                  style={{ left: `calc(${prediction.probability * 100}% - 5px)` }}
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 mt-2 font-medium">
                <span>Interval Width: {(uncertainty.width * 100).toFixed(1)}%</span>
                <span className="font-bold text-slate-700">State: {prediction.state === 1 ? 'FLOOD LIKELY' : 'SUB-THRESHOLD'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Feature Distributions, Analogs, Explainability */}
        <div className="xl:col-span-8 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-xs font-bold text-slate-500 tracking-wider uppercase mb-5 flex items-center gap-2 border-b border-slate-100 pb-2">
              <BarChart3 className="h-4 w-4 text-indigo-600" /> Historical Baseline vs Live Telemetry
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['rainfall_7d_sum', 'total_reservoir_level', 'rainfall_daily', 'temp_max'].map(feat => {
                if (!historical_comparison || !historical_comparison[feat]) return null;
                const comp = historical_comparison[feat];
                const pct = comp.percentile;
                const isExtreme = pct > 90 || pct < 10;
                
                return (
                  <div key={feat} className={`p-4 rounded-xl border transition ${isExtreme ? 'bg-amber-50/70 border-amber-200' : 'bg-slate-50 border-slate-100'}`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold uppercase text-slate-700 truncate">{feat.replace(/_/g, ' ')}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${isExtreme ? 'bg-amber-200 text-amber-900' : 'bg-slate-200 text-slate-600'}`}>
                        {pct.toFixed(0)}th Percentile
                      </span>
                    </div>
                    <div className="flex justify-between items-end">
                      <div>
                        <span className="text-2xl font-black text-slate-900">{comp.value.toFixed(1)}</span>
                        <span className="text-xs text-slate-500 ml-1 font-medium">Live</span>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-bold text-slate-700">{comp.historical_mean.toFixed(1)}</span>
                        <span className="text-[10px] text-slate-500 block font-medium">Hist. Baseline Mean</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* HISTORICAL ANALOGS */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h3 className="text-xs font-bold text-slate-500 tracking-wider uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2">
                <History className="h-4 w-4 text-indigo-600" /> Nearest Historical Analogs
              </h3>
              <div className="space-y-3">
                {historical_analogs && historical_analogs.map((analog, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3.5 border border-slate-100 rounded-xl bg-slate-50 hover:bg-slate-100/70 transition">
                    <div>
                      <div className="font-bold text-sm text-slate-800">{analog.date}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5 font-medium">
                        Reservoir: {analog.key_metrics.total_reservoir_level} mcft | 7d-Rain: {analog.key_metrics.rainfall_7d_sum} mm
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-black text-indigo-700">{analog.similarity_pct}% MATCH</div>
                      <div className={`text-[10px] font-bold px-2 py-0.5 rounded inline-block mt-1 ${analog.flood_status ? 'bg-red-100 text-red-800 border border-red-200' : 'bg-slate-200 text-slate-700'}`}>
                        {analog.flood_status ? 'FLOOD EVENT' : 'NOMINAL'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* MODEL EXPLAINABILITY */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <h3 className="text-xs font-bold text-slate-500 tracking-wider uppercase mb-4 flex items-center gap-2 border-b border-slate-100 pb-2">
                <AlertOctagon className="h-4 w-4 text-indigo-600" /> Top Feature Drivers
              </h3>
              <div className="space-y-3 mt-3">
                {explainability && explainability.map((exp, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-700 text-[11px]">{exp.feature.replace(/_/g, ' ')}</span>
                      <span className="text-indigo-600 font-bold">{(exp.importance * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-600 rounded-full"
                        style={{ width: `${exp.importance * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
