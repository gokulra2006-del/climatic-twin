import React, { useState, useEffect } from 'react';
import { 
  Shield, Activity, Clock, Radio, Database, Terminal, CheckCircle2, 
  AlertTriangle, Server, Network, Layers, Zap, Info, X, CloudRain,
  ThermometerSun, Wind, Droplets, Map, TrendingUp, TrendingDown, Minus,
  History, Sparkles, BookOpen, AlertOctagon, BarChart3, RefreshCw
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

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
      setError(err.message);
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
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 space-y-4">
        <Activity className="h-12 w-12 animate-pulse text-emerald-400" />
        <p className="text-sm tracking-widest uppercase font-mono">Initializing Live Feature Alignment Pipeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/60 text-rose-300 p-6 rounded-2xl flex items-start gap-4 backdrop-blur-md">
        <AlertTriangle className="h-8 w-8 text-rose-400 shrink-0" />
        <div>
          <h3 className="font-bold text-lg mb-1">Live Telemetry Pipeline Error</h3>
          <p className="text-sm text-rose-300/80">{error}</p>
          <button 
            onClick={fetchLiveIntelligence} 
            className="mt-3 px-4 py-1.5 bg-rose-800 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg transition"
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
      case 'CRITICAL': return 'text-rose-400 bg-rose-950/60 border-rose-800';
      case 'HIGH': return 'text-orange-400 bg-orange-950/60 border-orange-800';
      case 'MODERATE': return 'text-amber-400 bg-amber-950/60 border-amber-800';
      default: return 'text-emerald-400 bg-emerald-950/60 border-emerald-800';
    }
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12 animate-fadeIn">
      
      {/* 1. HEADER */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/60 rounded-3xl shadow-xl border border-slate-800 p-6 text-white flex flex-col md:flex-row justify-between items-center gap-4 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Radio className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-2xl font-black tracking-tight flex items-center gap-3">
              Real-Time AI Flood Intelligence
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono">
                ● LIVE PIPELINE ACTIVE
              </span>
            </h2>
            <p className="text-slate-400 text-xs font-mono mt-0.5">
              Live Satellite Telemetry Ingestion • Feature Alignment • Historical Analog Matching
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono">
          <div className="bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block text-[10px] uppercase">Champion Model</span>
            <span className="font-bold text-indigo-300">{model.name} (v{model.version})</span>
          </div>
          <div className="bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-500 block text-[10px] uppercase">Latency</span>
            <span className="font-bold text-emerald-400">{model.latency_ms} ms</span>
          </div>
          <button
            onClick={fetchLiveIntelligence}
            disabled={isRefreshing}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 disabled:opacity-50"
            title="Refresh Live Data"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. ALIGNMENT STATUS */}
      {feature_alignment.status !== 'ALIGNED' && (
        <div className="bg-amber-950/50 border border-amber-800/80 p-4 rounded-2xl flex items-center gap-3 text-amber-200">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
          <div className="text-xs font-mono">
            <span className="font-bold">DEGRADED FEATURE ALIGNMENT:</span> Missing live telemetry ({feature_alignment.missing_features.join(', ')}). Falling back to historical distribution tail values.
          </div>
        </div>
      )}

      {/* 3. NOVA AI SUMMARY */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 rounded-3xl shadow-xl border border-indigo-500/30 p-6 relative overflow-hidden backdrop-blur-xl">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-500"></div>
        <h3 className="text-xs font-black tracking-widest text-indigo-300 flex items-center gap-2 mb-4 uppercase">
          <Sparkles className="h-4 w-4" /> NOVA AI Real-Time Flood Assessment
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-sans">
          <div className="bg-slate-950/70 p-4 rounded-2xl border border-slate-800/80">
            <span className="text-indigo-300 font-bold block mb-1 font-mono uppercase text-[10px]">CURRENT SITUATION</span>
            <span className="text-slate-200 leading-relaxed">{nova_summary.situation}</span>
          </div>
          <div className="bg-slate-950/70 p-4 rounded-2xl border border-slate-800/80">
            <span className="text-indigo-300 font-bold block mb-1 font-mono uppercase text-[10px]">MODEL OUTLOOK</span>
            <span className="text-slate-200 leading-relaxed">{nova_summary.model_outlook}</span>
          </div>
          <div className="bg-slate-950/70 p-4 rounded-2xl border border-slate-800/80">
            <span className="text-indigo-300 font-bold block mb-1 font-mono uppercase text-[10px]">PRIMARY DRIVERS</span>
            <span className="text-slate-200 leading-relaxed">{nova_summary.drivers}</span>
          </div>
          <div className="bg-slate-950/70 p-4 rounded-2xl border border-slate-800/80">
            <span className="text-indigo-300 font-bold block mb-1 font-mono uppercase text-[10px]">HISTORICAL ANALOG</span>
            <span className="text-slate-200 leading-relaxed">{nova_summary.context}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Calibrated Risk & Uncertainty */}
        <div className="xl:col-span-4 space-y-6">
          <div className="bg-slate-900/80 rounded-3xl shadow-xl border border-slate-800 p-6 flex flex-col items-center justify-center relative overflow-hidden backdrop-blur-md">
            <h3 className="text-xs font-bold text-slate-400 tracking-wider uppercase mb-6 flex items-center gap-2 w-full font-mono">
              <Shield className="h-4 w-4 text-indigo-400" /> Calibrated Flood Risk
            </h3>
            
            <div className="my-6 text-center">
              <span className={`text-4xl font-black tracking-tight px-6 py-2 rounded-2xl border font-mono ${getRiskBadgeColor(prediction.risk_level)}`}>
                {prediction.risk_level}
              </span>
              <div className="flex items-end justify-center gap-1 mt-6">
                <span className="text-5xl font-black text-white font-mono">{(prediction.probability * 100).toFixed(1)}</span>
                <span className="text-xl font-bold text-slate-400 mb-1 font-mono">%</span>
              </div>
              <p className="text-xs uppercase font-mono text-slate-400 mt-2">Calibrated Inundation Probability</p>
            </div>
            
            <div className="w-full mt-4 p-4 bg-slate-950/70 rounded-2xl border border-slate-800/80 font-mono text-xs">
              <div className="flex justify-between text-[11px] mb-2 text-slate-400">
                <span>P10: {(uncertainty.p10 * 100).toFixed(1)}%</span>
                <span className="font-bold text-slate-300">Conformal Interval (90%)</span>
                <span>P90: {(uncertainty.p90 * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden relative">
                <div 
                  className="absolute top-0 bottom-0 bg-indigo-500/50"
                  style={{ left: `${Math.max(0, uncertainty.p10 * 100)}%`, right: `${Math.max(0, 100 - (uncertainty.p90 * 100))}%` }}
                ></div>
                <div 
                  className="absolute top-0 bottom-0 w-2 bg-indigo-400 rounded-full shadow-lg"
                  style={{ left: `calc(${prediction.probability * 100}% - 4px)` }}
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 mt-2">
                <span>Interval Width: {(uncertainty.width * 100).toFixed(1)}%</span>
                <span>State: {prediction.state === 1 ? 'FLOOD LIKELY' : 'SUB-THRESHOLD'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Feature Distributions, Analogs, Explainability */}
        <div className="xl:col-span-8 space-y-6">
          <div className="bg-slate-900/80 rounded-3xl shadow-xl border border-slate-800 p-6 backdrop-blur-md">
            <h3 className="text-xs font-bold text-slate-400 tracking-wider uppercase mb-5 flex items-center gap-2 font-mono">
              <BarChart3 className="h-4 w-4 text-indigo-400" /> Historical Baseline vs Live Telemetry
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['rainfall_7d_sum', 'total_reservoir_level', 'rainfall_daily', 'temp_max'].map(feat => {
                if (!historical_comparison || !historical_comparison[feat]) return null;
                const comp = historical_comparison[feat];
                const pct = comp.percentile;
                const isExtreme = pct > 90 || pct < 10;
                
                return (
                  <div key={feat} className={`p-4 rounded-2xl border transition ${isExtreme ? 'bg-amber-950/30 border-amber-800/60' : 'bg-slate-950/60 border-slate-800'}`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-mono font-bold uppercase text-slate-200 truncate">{feat.replace(/_/g, ' ')}</span>
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${isExtreme ? 'bg-amber-900/60 text-amber-300' : 'bg-slate-800 text-slate-400'}`}>
                        {pct.toFixed(0)}th Percentile
                      </span>
                    </div>
                    <div className="flex justify-between items-end font-mono">
                      <div>
                        <span className="text-2xl font-black text-white">{comp.value.toFixed(1)}</span>
                        <span className="text-xs text-slate-500 ml-1">Live</span>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-bold text-slate-400">{comp.historical_mean.toFixed(1)}</span>
                        <span className="text-[10px] text-slate-500 block">Hist. Baseline Mean</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* HISTORICAL ANALOGS */}
            <div className="bg-slate-900/80 rounded-3xl shadow-xl border border-slate-800 p-6 backdrop-blur-md">
              <h3 className="text-xs font-bold text-slate-400 tracking-wider uppercase mb-4 flex items-center gap-2 font-mono">
                <History className="h-4 w-4 text-indigo-400" /> Nearest Historical Analogs
              </h3>
              <div className="space-y-3 font-mono">
                {historical_analogs && historical_analogs.map((analog, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3.5 border border-slate-800 rounded-2xl bg-slate-950/60 hover:bg-slate-800/40 transition">
                    <div>
                      <div className="font-bold text-sm text-white">{analog.date}</div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        Reservoir: {analog.key_metrics.total_reservoir_level} | 7d-Rain: {analog.key_metrics.rainfall_7d_sum}mm
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-black text-indigo-400">{analog.similarity_pct}% MATCH</div>
                      <div className={`text-[10px] font-bold px-2 py-0.5 rounded inline-block mt-1 ${analog.flood_status ? 'bg-rose-950/80 text-rose-300 border border-rose-800' : 'bg-slate-800 text-slate-400'}`}>
                        {analog.flood_status ? 'FLOOD CONFIRMED' : 'NON-FLOOD'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* MODEL EXPLAINABILITY */}
            <div className="bg-slate-900/80 rounded-3xl shadow-xl border border-slate-800 p-6 backdrop-blur-md">
              <h3 className="text-xs font-bold text-slate-400 tracking-wider uppercase mb-4 flex items-center gap-2 font-mono">
                <AlertOctagon className="h-4 w-4 text-indigo-400" /> Top Feature Drivers
              </h3>
              <div className="space-y-3 mt-4 font-mono">
                {explainability && explainability.map((exp, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-slate-300 text-[11px]">{exp.feature.replace(/_/g, ' ')}</span>
                      <span className="text-indigo-400 font-bold">{(exp.importance * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-500 rounded-full"
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
