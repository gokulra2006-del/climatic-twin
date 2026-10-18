import React, { useState, useEffect } from 'react';
import {
  Activity, Shield, AlertTriangle, CheckCircle2, Clock,
  Cpu, HardDrive, Layers, RefreshCw, Sparkles, TrendingUp,
  TrendingDown, Minus, Info, AlertOctagon, GitBranch,
  BarChart3, Database, ShieldAlert, ArrowRight, Gauge,
  Sliders, FileText, Check, X
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Offline demonstration data. It is intentionally labelled in the interface so
// it cannot be mistaken for live production-model telemetry.
const PROTOTYPE_MODEL_HEALTH = {
  model_status: 'HEALTHY',
  retraining_readiness: {
    readiness_score: 28,
    recommendation: 'Continue monitoring',
    reason: 'No material prototype drift trigger is active in the saved scenario.',
  },
  champion_model: {
    model_version: 'RF-chronological-v1',
    validation_metrics: { roc_auc: 0.89, pr_auc: 0.83, brier_score: 0.028 },
  },
  candidate_model: {
    validation_metrics: { roc_auc: 0.87, pr_auc: 0.80, brier_score: 0.031 },
  },
  feature_drift: {
    aggregate_psi: 0.07,
    top_drifting_features: [
      { feature: 'rainfall_7d_sum', training_median: 38.6, live_median: 42.0, pct_change_median: 8.8, psi: 0.08, ks_statistic: 0.12, ks_pvalue: 0.41, severity: 'LOW', status: 'NOMINAL' },
      { feature: 'total_reservoir_level', training_median: 7760, live_median: 8120, pct_change_median: 4.6, psi: 0.06, ks_statistic: 0.10, ks_pvalue: 0.56, severity: 'LOW', status: 'NOMINAL' },
      { feature: 'rainfall_daily', training_median: 6.9, live_median: 8.4, pct_change_median: 21.7, psi: 0.12, ks_statistic: 0.18, ks_pvalue: 0.18, severity: 'MODERATE', status: 'WATCH' },
    ],
  },
  prediction_drift: { live_median_prob: 0.12, historical_median_prob: 0.11, probability_shift: 0.01, severity: 'LOW' },
  uncertainty_trend: {
    condition: 'STABLE',
    epistemic_variance_mean: '0.04',
    prediction_interval_width_mean: '0.17',
    note: 'Saved prototype values show stable ensemble spread; this is not a real-time calibration claim.',
  },
  data_quality: { aggregate_score: 0.96, telemetry_state: 'PROTOTYPE', degraded_sources_count: 0 },
  temporal_drift: {
    pattern: 'Stable prototype baseline',
    '24h_status': 'NOMINAL',
    '7d_status': 'NOMINAL',
    '30d_status': 'WATCH',
    interpretation: 'Saved scenario only; establish monitored windows after backend deployment.',
  },
  concept_drift: {
    status: 'VERIFIED LABELS REQUIRED',
    scientific_rationale: 'A concept-drift conclusion requires new verified impact labels; the prototype does not infer it from unlabelled telemetry alone.',
  },
  nova_summary: {
    briefing: 'The saved model-health scenario demonstrates the review workflow: data-quality gates, feature drift, uncertainty monitoring, and human approval before retraining.',
  },
};

export default function ModelHealthDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWindow, setSelectedWindow] = useState('7d');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncNotice, setSyncNotice] = useState(null);

  const fetchModelHealth = async (windowKey = selectedWindow) => {
    try {
      setIsRefreshing(true);
      const response = await fetch(`${API_URL}/api/model-health?window=${windowKey}`);
      if (!response.ok) throw new Error("Failed to fetch model health telemetry");
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setData(PROTOTYPE_MODEL_HEALTH);
      setError('Live backend is unavailable. Showing a clearly labelled saved prototype model-health scenario.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const syncLiveTelemetry = async () => {
    try {
      setIsSyncing(true);
      const res = await fetch(`${API_URL}/api/model-health/sync-live`, { method: 'POST' });
      const json = await res.json();
      if (res.ok) {
        setSyncNotice(`Synchronized ${json.ingested_observations_count} live observation intervals into model surveillance.`);
        await fetchModelHealth(selectedWindow);
      } else {
        setSyncNotice('Unable to sync live telemetry from external feeds.');
      }
    } catch (e) {
      setSyncNotice('Could not reach backend live telemetry ingestion endpoint.');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncNotice(null), 6000);
    }
  };

  useEffect(() => {
    fetchModelHealth(selectedWindow);
    const interval = setInterval(() => fetchModelHealth(selectedWindow), 30000);
    return () => clearInterval(interval);
  }, [selectedWindow]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-500 space-y-4">
        <Cpu className="h-10 w-10 animate-spin text-indigo-600" />
        <p className="text-xs uppercase font-bold tracking-wider text-slate-600">Initializing Model Monitoring Engine...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 p-6 rounded-2xl flex items-start gap-4">
        <AlertTriangle className="h-6 w-6 text-red-600 shrink-0" />
        <div>
          <h3 className="font-bold text-sm mb-1">Model Telemetry Pipeline Error</h3>
          <p className="text-xs text-red-700">{error}</p>
          <button 
            onClick={() => fetchModelHealth(selectedWindow)} 
            className="mt-3 px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg transition"
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
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'WATCH':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      case 'DRIFT DETECTED':
        return 'bg-rose-50 text-rose-800 border-rose-300';
      case 'RETRAINING RECOMMENDED':
        return 'bg-purple-50 text-purple-800 border-purple-300';
      default:
        return 'bg-slate-50 text-slate-800 border-slate-300';
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-red-100 text-red-800 border border-red-200">HIGH</span>;
      case 'MODERATE':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-amber-100 text-amber-800 border border-amber-200">MODERATE</span>;
      case 'PENDING':
      case 'INSUFFICIENT_DATA':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-slate-100 text-slate-600 border border-slate-200">PENDING</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-emerald-100 text-emerald-800 border border-emerald-200">LOW</span>;
    }
  };

  const formatTemporalBadge = (st) => {
    if (!st || st === 'INSUFFICIENT_DATA') {
      return <span className="text-slate-500 font-semibold">Awaiting</span>;
    }
    return <b className="text-slate-800">{st}</b>;
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12 font-sans">
      {/* 1. Clean Header Card */}
      <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
                <Cpu className="h-6 w-6" />
              </span>
              <div>
                <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
                  Model Health & Retraining Intelligence
                  <span className={`text-[10px] px-2.5 py-0.5 rounded-full border uppercase font-bold tracking-wider ${getStatusColor(model_status)}`}>
                    {model_status}
                  </span>
                </h1>
                <p className="text-xs text-slate-500 mt-0.5 font-medium">
                  Production Champion: <span className="text-indigo-600 font-semibold">{champion_model.model_version}</span> | Calibrated Random Forest (Platt Sigmoid)
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Window selector */}
            <div className="flex bg-slate-100 border border-slate-200 rounded-xl p-1 text-xs">
              {['24h', '7d', '30d'].map((w) => (
                <button
                  key={w}
                  onClick={() => setSelectedWindow(w)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition uppercase ${
                    selectedWindow === w
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {w} Horizon
                </button>
              ))}
            </div>

            <button
              onClick={syncLiveTelemetry}
              disabled={isSyncing}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition border border-indigo-200 disabled:opacity-50"
              title="Poll latest Open-Meteo weather telemetry and record observation"
            >
              <Activity className={`h-3.5 w-3.5 ${isSyncing ? 'animate-pulse text-indigo-600' : ''}`} />
              {isSyncing ? 'Syncing…' : 'Sync Live Weather'}
            </button>

            <button
              onClick={() => fetchModelHealth(selectedWindow)}
              disabled={isRefreshing}
              className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200 disabled:opacity-50"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
            </button>
          </div>
        </div>

        {syncNotice && (
          <div className="mt-3 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center gap-2 font-medium">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{syncNotice}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-950 flex items-start gap-3">
            <Info className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
            <div className="text-xs leading-relaxed">
              <span className="font-bold">Prototype mode:</span> {error}
              <button onClick={() => fetchModelHealth(selectedWindow)} className="ml-3 underline font-bold text-amber-900 hover:text-amber-700">
                Retry connection
              </button>
            </div>
          </div>
        )}

        {/* Confidence Warning if Active */}
        {nova_summary.confidence_warning && (
          <div className="mt-4 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center gap-3">
            <AlertOctagon className="h-5 w-5 text-amber-600 shrink-0" />
            <span className="text-xs font-semibold">
              {nova_summary.confidence_warning}
            </span>
          </div>
        )}
      </div>

      {/* 2. KPI Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Retraining Readiness Score */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Retraining Readiness</span>
            <Gauge className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">{retraining_readiness.readiness_score}</span>
            <span className="text-xs font-bold text-slate-500">/ 100</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
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
          <p className="text-[11px] text-indigo-700 mt-2 font-semibold">
            Action: {retraining_readiness.recommendation}
          </p>
        </div>

        {/* Temporal Drift Classification */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Temporal Dynamics</span>
            <Clock className="h-4 w-4 text-cyan-600" />
          </div>
          <div className="text-base font-bold text-slate-800 truncate">
            {temporal_drift.pattern}
          </div>
          <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
            <span>24H: {formatTemporalBadge(temporal_drift['24h_status'])}</span>
            <span>•</span>
            <span>7D: {formatTemporalBadge(temporal_drift['7d_status'])}</span>
            <span>•</span>
            <span>30D: {formatTemporalBadge(temporal_drift['30d_status'])}</span>
          </div>
          <p className="text-[10px] text-slate-500 mt-2 line-clamp-1 font-medium">
            {temporal_drift.interpretation}
          </p>
        </div>

        {/* Prediction Drift */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Prediction Drift</span>
            <TrendingUp className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline gap-2">
            {prediction_drift.live_median_prob != null && !isNaN(prediction_drift.live_median_prob) ? (
              <>
                <span className="text-3xl font-black text-slate-900">
                  {(prediction_drift.live_median_prob * 100).toFixed(1)}%
                </span>
                <span className="text-xs font-medium text-slate-500">
                  (Hist: {prediction_drift.historical_median_prob != null && !isNaN(prediction_drift.historical_median_prob) ? `${(prediction_drift.historical_median_prob * 100).toFixed(1)}%` : '5.4%'})
                </span>
              </>
            ) : (
              <div>
                <span className="text-xl font-bold text-slate-700">Awaiting History</span>
                <span className="block text-[11px] font-medium text-slate-400 mt-0.5">
                  Hist Baseline: {prediction_drift.historical_median_prob != null && !isNaN(prediction_drift.historical_median_prob) ? `${(prediction_drift.historical_median_prob * 100).toFixed(1)}%` : '5.4%'}
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-xs text-slate-500 font-medium">Shift:</span>
            {prediction_drift.probability_shift != null && !isNaN(prediction_drift.probability_shift) ? (
              <span className={`text-xs font-bold ${prediction_drift.probability_shift >= 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {prediction_drift.probability_shift >= 0 ? '+' : ''}{(prediction_drift.probability_shift * 100).toFixed(2)}%
              </span>
            ) : (
              <span className="text-xs font-semibold text-slate-400">
                — (Awaiting N ≥ 5)
              </span>
            )}
            <span className="ml-auto">
              {getSeverityBadge(prediction_drift.severity || (prediction_drift.live_median_prob == null ? 'PENDING' : 'LOW'))}
            </span>
          </div>
        </div>

        {/* Sensor Data Quality Gating */}
        <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Telemetry Quality Gate</span>
            <Shield className="h-4 w-4 text-purple-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-900">
              {(data_quality.aggregate_score * 100).toFixed(0)}%
            </span>
            <span className="text-xs font-medium text-slate-500">SHS Score</span>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className={`text-xs px-2 py-0.5 rounded font-bold ${
              data_quality.telemetry_state === 'NOMINAL' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
            }`}>
              {data_quality.telemetry_state}
            </span>
            <span className="text-[11px] text-slate-500 font-medium ml-auto">
              Degraded: {data_quality.degraded_sources_count}
            </span>
          </div>
        </div>
      </div>

      {/* 3. Operational Model Briefing Card */}
      <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 shrink-0">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-2">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              Model Health Briefing
              <span className="text-xs text-indigo-600 font-bold">• Real-Time Inference Alignment</span>
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed font-sans">
              {nova_summary.briefing}
            </p>
            <div className="pt-2 border-t border-slate-100 text-xs text-slate-500 flex items-center gap-2 font-medium">
              <span className="text-indigo-600 font-bold">Operational Rationale:</span>
              <span>{retraining_readiness.reason}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Top Drifting Features Table */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-600" />
              Top Drifting Environmental Features
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Statistical comparison of historical training distribution vs recent live observations ({selectedWindow} window)
            </p>
          </div>
          <div className="text-xs font-semibold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
            Aggregate PSI: <b className="text-indigo-600">{feature_drift.aggregate_psi}</b>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-bold tracking-wider border-b border-slate-200">
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
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {feature_drift.top_drifting_features && feature_drift.top_drifting_features.length > 0 ? (
                feature_drift.top_drifting_features.map((feat) => (
                  <tr key={feat.feature} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-4 font-bold text-slate-800 font-sans">
                      {feat.feature.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">{feat.training_median}</td>
                    <td className="py-3.5 px-4 text-slate-800 font-bold">{feat.live_median}</td>
                    <td className="py-3.5 px-4 font-bold">
                      <span className={feat.pct_change_median >= 0 ? 'text-amber-600' : 'text-blue-600'}>
                        {feat.pct_change_median >= 0 ? '+' : ''}{feat.pct_change_median}%
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-indigo-700">{feat.psi}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-500">
                      {feat.ks_statistic} (p={feat.ks_pvalue})
                    </td>
                    <td className="py-3.5 px-4">{getSeverityBadge(feat.severity)}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        feat.status === 'DRIFT DETECTED'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : feat.status === 'WATCH'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      }`}>
                        {feat.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400 font-sans font-medium">
                    Awaiting streaming telemetry: At least 5 recorded live observations are required before feature distribution drift (PSI, KS-stat) can be calculated.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Uncertainty & Concept Drift Safeguard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uncertainty Monitoring */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-600" />
              Uncertainty & Epistemic Dispersion
            </h3>
            <span className="text-xs px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 font-bold border border-indigo-100">
              {uncertainty_trend.condition || 'STABLE'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-1">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Epistemic Variance</span>
              <span className="text-xl font-black text-slate-800">{uncertainty_trend.epistemic_variance_mean ?? '—'}</span>
              <span className="text-[10px] text-slate-500 block mt-1 font-medium">Tree ensemble variance</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Prediction Interval Width</span>
              <span className="text-xl font-black text-slate-800">{uncertainty_trend.prediction_interval_width_mean ?? '—'}</span>
              <span className="text-[10px] text-slate-500 block mt-1 font-medium">Split-conformal P90 - P10</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 leading-relaxed font-medium">
            <Info className="h-4 w-4 text-indigo-600 inline mr-1.5 -mt-0.5" />
            {uncertainty_trend.note || 'Uncertainty tracking evaluates model confidence across recent live outputs.'}
          </div>
        </div>

        {/* Concept Drift & Ground-Truth Safeguard */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-cyan-600" />
              Concept Drift & Verified Performance
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-bold uppercase">
              Scientific Guard
            </span>
          </div>

          <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 text-blue-900">
            <div className="flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-1">
                  {concept_drift.status}
                </h4>
                <p className="text-xs text-blue-800 leading-relaxed font-medium">
                  {concept_drift.scientific_rationale}
                </p>
              </div>
            </div>
          </div>

          {/* Champion vs Candidate Overview */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-slate-500 pb-1 border-b border-slate-200 font-sans font-bold">
              <span>Metric</span>
              <span>Champion (RF)</span>
              <span>Candidate (HGB)</span>
            </div>
            <div className="flex justify-between text-slate-700">
              <span className="font-sans font-semibold">ROC-AUC</span>
              <span className="font-bold text-emerald-700">{champion_model.validation_metrics.roc_auc}</span>
              <span className="text-slate-500">{candidate_model.validation_metrics.roc_auc}</span>
            </div>
            <div className="flex justify-between text-slate-700">
              <span className="font-sans font-semibold">PR-AUC</span>
              <span className="font-bold text-emerald-700">{champion_model.validation_metrics.pr_auc}</span>
              <span className="text-slate-500">{candidate_model.validation_metrics.pr_auc}</span>
            </div>
            <div className="flex justify-between text-slate-700">
              <span className="font-sans font-semibold">Brier Score</span>
              <span className="font-bold text-emerald-700">{champion_model.validation_metrics.brier_score}</span>
              <span className="text-slate-500">{candidate_model.validation_metrics.brier_score}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Safe Retraining Workflow Architecture */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-emerald-600" />
          Safe Model Retraining Architecture (Human-In-The-Loop)
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs">
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
            <div key={idx} className="bg-slate-50 p-3 rounded-xl border border-slate-100 flex flex-col justify-between">
              <span className="text-[10px] text-slate-500 font-bold block mb-1">STEP {item.step}</span>
              <span className="text-xs font-semibold text-slate-700 leading-tight mb-2">{item.title}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-bold font-mono">
                {item.status}
              </span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-4 text-center font-medium">
          Strict Policy: Production models are never automatically replaced. Candidate models must demonstrate superior PR-AUC on chronological holdouts before deployment.
        </p>
      </div>
    </div>
  );
}
