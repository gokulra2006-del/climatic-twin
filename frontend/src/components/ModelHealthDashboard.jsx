import React, { useState, useEffect } from 'react';
import {
  Activity, Shield, AlertTriangle, CheckCircle2, Clock,
  Cpu, HardDrive, Layers, RefreshCw, Sparkles, TrendingUp,
  TrendingDown, Minus, Info, AlertOctagon, GitBranch,
  BarChart3, Database, ShieldAlert, ArrowRight, Gauge,
  Sliders, FileText, Check, X
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function ModelHealthDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWindow, setSelectedWindow] = useState('7d');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchModelHealth = async (windowKey = selectedWindow) => {
    try {
      setIsRefreshing(true);
      const response = await fetch(`${API_URL}/api/model-health?window=${windowKey}`);
      if (!response.ok) throw new Error("Failed to fetch model health telemetry");
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
    fetchModelHealth(selectedWindow);
    const interval = setInterval(() => fetchModelHealth(selectedWindow), 30000);
    return () => clearInterval(interval);
  }, [selectedWindow]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 space-y-4">
        <Cpu className="h-12 w-12 animate-pulse text-indigo-400" />
        <p className="text-sm tracking-widest uppercase font-mono">Initializing Model Monitoring Engine...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/60 text-rose-300 p-6 rounded-2xl flex items-start gap-4 backdrop-blur-md">
        <AlertTriangle className="h-8 w-8 text-rose-400 shrink-0" />
        <div>
          <h3 className="font-bold text-lg mb-1">Model Telemetry Pipeline Error</h3>
          <p className="text-sm text-rose-300/80">{error}</p>
          <button 
            onClick={() => fetchModelHealth(selectedWindow)} 
            className="mt-3 px-4 py-1.5 bg-rose-800 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const {
    model_status,
    retraining_readiness,
    champion_model,
    candidate_model,
    feature_drift,
    prediction_drift,
    uncertainty_trend,
    data_quality,
    temporal_drift,
    concept_drift,
    nova_summary
  } = data;

  const getStatusColor = (status) => {
    switch (status) {
      case 'HEALTHY':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'WATCH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'DRIFT DETECTED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'RETRAINING RECOMMENDED':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40';
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-rose-900/60 text-rose-300 border border-rose-700">HIGH</span>;
      case 'MODERATE':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-amber-900/60 text-amber-300 border border-amber-700">MODERATE</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-emerald-900/60 text-emerald-300 border border-emerald-700">LOW</span>;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* 1. Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-indigo-900/40 p-6 rounded-3xl shadow-xl backdrop-blur-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <Cpu className="h-6 w-6" />
              </span>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
                  Model Health & Retraining Intelligence
                  <span className={`text-xs px-3 py-1 rounded-full border font-mono tracking-wider ${getStatusColor(model_status)}`}>
                    ● {model_status}
                  </span>
                </h1>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Production Champion: <span className="text-indigo-300 font-semibold">{champion_model.model_version}</span> | Calibrated Random Forest (Platt Sigmoid)
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Window selector */}
            <div className="flex bg-slate-950/70 border border-slate-800 rounded-xl p-1 text-xs font-mono">
              {['24h', '7d', '30d'].map((w) => (
                <button
                  key={w}
                  onClick={() => setSelectedWindow(w)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition uppercase ${
                    selectedWindow === w
                      ? 'bg-indigo-600 text-white shadow-lg'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {w} Horizon
                </button>
              ))}
            </div>

            <button
              onClick={() => fetchModelHealth(selectedWindow)}
              disabled={isRefreshing}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 disabled:opacity-50"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Confidence Warning if Active */}
        {nova_summary.confidence_warning && (
          <div className="mt-4 p-4 rounded-2xl bg-amber-950/50 border border-amber-800/80 text-amber-200 flex items-center gap-3">
            <AlertOctagon className="h-5 w-5 text-amber-400 shrink-0" />
            <span className="text-xs font-semibold tracking-wide">
              {nova_summary.confidence_warning}
            </span>
          </div>
        )}
      </div>

      {/* 2. KPI Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Retraining Readiness Score */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg relative overflow-hidden backdrop-blur-md">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Retraining Readiness</span>
            <Gauge className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">{retraining_readiness.readiness_score}</span>
            <span className="text-xs font-mono text-slate-400">/ 100</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                retraining_readiness.readiness_score >= 75
                  ? 'bg-rose-500'
                  : retraining_readiness.readiness_score >= 50
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${retraining_readiness.readiness_score}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-indigo-300 mt-2 font-medium">
            Action: {retraining_readiness.recommendation}
          </p>
        </div>

        {/* Temporal Drift Classification */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg backdrop-blur-md">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Temporal Dynamics</span>
            <Clock className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-base font-black text-white truncate">
            {temporal_drift.pattern}
          </div>
          <div className="flex items-center gap-2 mt-3 text-xs font-mono text-slate-400">
            <span>24H: <b className="text-slate-200">{temporal_drift['24h_status']}</b></span>
            <span>•</span>
            <span>7D: <b className="text-slate-200">{temporal_drift['7d_status']}</b></span>
            <span>•</span>
            <span>30D: <b className="text-slate-200">{temporal_drift['30d_status']}</b></span>
          </div>
          <p className="text-[10px] text-slate-500 mt-2 line-clamp-1">
            {temporal_drift.interpretation}
          </p>
        </div>

        {/* Prediction Drift */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg backdrop-blur-md">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Prediction Drift</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">
              {(prediction_drift.live_median_prob * 100).toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-slate-400">
              (Hist: {(prediction_drift.historical_median_prob * 100).toFixed(1)}%)
            </span>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-xs text-slate-400 font-mono">Shift:</span>
            <span className={`text-xs font-mono font-bold ${prediction_drift.probability_shift >= 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {prediction_drift.probability_shift >= 0 ? '+' : ''}{(prediction_drift.probability_shift * 100).toFixed(2)}%
            </span>
            <span className="ml-auto">{getSeverityBadge(prediction_drift.severity)}</span>
          </div>
        </div>

        {/* Sensor Data Quality Gating */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg backdrop-blur-md">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Telemetry Quality Gate</span>
            <Shield className="h-4 w-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">
              {(data_quality.aggregate_score * 100).toFixed(0)}%
            </span>
            <span className="text-xs font-mono text-slate-400">SHS Score</span>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${
              data_quality.telemetry_state === 'NOMINAL' ? 'bg-emerald-900/50 text-emerald-300' : 'bg-rose-900/50 text-rose-300'
            }`}>
              {data_quality.telemetry_state}
            </span>
            <span className="text-[11px] text-slate-400 font-mono ml-auto">
              Degraded: {data_quality.degraded_sources_count}
            </span>
          </div>
        </div>
      </div>

      {/* 3. NOVA AI Health Briefing */}
      <div className="bg-slate-900/90 border border-indigo-900/50 p-6 rounded-3xl shadow-xl relative overflow-hidden backdrop-blur-xl">
        <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shrink-0">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              NOVA Model Health Briefing
              <span className="text-xs font-mono text-indigo-400">● Real-Time Inference Alignment</span>
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed font-sans">
              {nova_summary.briefing}
            </p>
            <div className="pt-2 border-t border-slate-800 text-xs font-mono text-slate-400 flex items-center gap-2">
              <span className="text-indigo-400 font-semibold">Operational Rationale:</span>
              <span>{retraining_readiness.reason}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Top Drifting Features Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-400" />
              Top Drifting Environmental Features
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Statistical comparison of historical training distribution vs recent live observations ({selectedWindow} window)
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Aggregate PSI: <b className="text-indigo-300">{feature_drift.aggregate_psi}</b>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300 font-mono">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[11px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Feature Name</th>
                <th className="py-3 px-4">Training Median</th>
                <th className="py-3 px-4">Live Median</th>
                <th className="py-3 px-4">Variance (%)</th>
                <th className="py-3 px-4">PSI Metric</th>
                <th className="py-3 px-4">KS-Stat (p-val)</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {feature_drift.top_drifting_features.map((feat) => (
                <tr key={feat.feature} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4 font-semibold text-white">
                    {feat.feature.replace(/_/g, ' ')}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{feat.training_median}</td>
                  <td className="py-3.5 px-4 text-slate-200">{feat.live_median}</td>
                  <td className="py-3.5 px-4">
                    <span className={feat.pct_change_median >= 0 ? 'text-amber-400' : 'text-cyan-400'}>
                      {feat.pct_change_median >= 0 ? '+' : ''}{feat.pct_change_median}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-indigo-300">{feat.psi}</td>
                  <td className="py-3.5 px-4 text-xs text-slate-400">
                    {feat.ks_statistic} (p={feat.ks_pvalue})
                  </td>
                  <td className="py-3.5 px-4">{getSeverityBadge(feat.severity)}</td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      feat.status === 'DRIFT DETECTED'
                        ? 'bg-rose-900/40 text-rose-300 border border-rose-800'
                        : feat.status === 'WATCH'
                        ? 'bg-amber-900/40 text-amber-300 border border-amber-800'
                        : 'bg-emerald-900/40 text-emerald-300 border border-emerald-800'
                    }`}>
                      {feat.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Two Column Grid: Uncertainty & Concept Drift / Safe Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uncertainty Monitoring (Phase 11 Integration) */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Uncertainty & Epistemic Dispersion (Phase 11)
            </h3>
            <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-900/40 text-indigo-300 font-mono border border-indigo-800">
              {uncertainty_trend.condition}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block mb-1">Epistemic Variance</span>
              <span className="text-xl font-black text-white">{uncertainty_trend.epistemic_variance_mean}</span>
              <span className="text-[10px] text-slate-500 block mt-1">Tree ensemble variance</span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 font-mono">
              <span className="text-xs text-slate-400 block mb-1">Prediction Interval Width</span>
              <span className="text-xl font-black text-white">{uncertainty_trend.prediction_interval_width_mean}</span>
              <span className="text-[10px] text-slate-500 block mt-1">Split-conformal P90 - P10</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 text-xs text-slate-300 font-sans leading-relaxed">
            <Info className="h-4 w-4 text-indigo-400 inline mr-1.5 -mt-0.5" />
            {uncertainty_trend.note}
          </div>
        </div>

        {/* Concept Drift & Ground-Truth Safeguard */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-cyan-400" />
              Concept Drift & Verified Performance
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              Scientific Guard
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-800/40 text-cyan-200">
            <div className="flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-1">
                  {concept_drift.status}
                </h4>
                <p className="text-xs text-cyan-300/80 leading-relaxed">
                  {concept_drift.scientific_rationale}
                </p>
              </div>
            </div>
          </div>

          {/* Champion vs Candidate Overview */}
          <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800 space-y-2 font-mono text-xs">
            <div className="flex justify-between text-slate-400 pb-1 border-b border-slate-800">
              <span>Metric</span>
              <span>Champion (RF)</span>
              <span>Candidate (HGB)</span>
            </div>
            <div className="flex justify-between text-slate-200">
              <span>ROC-AUC</span>
              <span className="font-bold text-emerald-400">{champion_model.validation_metrics.roc_auc}</span>
              <span className="text-slate-400">{candidate_model.validation_metrics.roc_auc}</span>
            </div>
            <div className="flex justify-between text-slate-200">
              <span>PR-AUC</span>
              <span className="font-bold text-emerald-400">{champion_model.validation_metrics.pr_auc}</span>
              <span className="text-slate-400">{candidate_model.validation_metrics.pr_auc}</span>
            </div>
            <div className="flex justify-between text-slate-200">
              <span>Brier Score</span>
              <span className="font-bold text-emerald-400">{champion_model.validation_metrics.brier_score}</span>
              <span className="text-slate-400">{candidate_model.validation_metrics.brier_score}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Safe Retraining Workflow Architecture */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md">
        <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-emerald-400" />
          Safe Model Retraining Architecture (Human-In-The-Loop)
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center font-mono text-xs">
          {[
            { step: '1', title: 'Live Telemetry', status: 'ACTIVE' },
            { step: '2', title: 'Data Quality Gate', status: 'GATED' },
            { step: '3', title: 'Drift Monitor', status: 'SURVEILLANCE' },
            { step: '4', title: 'Readiness Score', status: 'EVALUATED' },
            { step: '5', title: 'Verified Labels', status: 'HOLD' },
            { step: '6', title: 'Candidate Train', status: 'STANDBY' },
            { step: '7', title: 'Champion Check', status: 'PROTECTED' },
            { step: '8', title: 'Manual Deploy', status: 'POLICY' }
          ].map((item, idx) => (
            <div key={idx} className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block mb-1">STEP {item.step}</span>
              <span className="text-xs font-semibold text-slate-200 leading-tight mb-2">{item.title}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                {item.status}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-4 text-center">
          Strict Policy: Production models are never automatically replaced. Candidate models must demonstrate superior PR-AUC on chronological holdouts before deployment.
        </p>
      </div>
    </div>
  );
}
