import React, { useState, useEffect } from 'react';
import { 
  CloudRain, Wind, AlertTriangle, Shield, RefreshCw, 
  Activity, CloudLightning, Waves, Droplets, MapPin, Gauge
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ExtremeRainfallDashboard({ 
  latestPred, 
  loading, 
  onRefresh 
}) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(Date.now());

  useEffect(() => {
    if (latestPred) setLastUpdated(Date.now());
  }, [latestPred]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (onRefresh) await onRefresh();
    setTimeout(() => setIsRefreshing(false), 800);
  };

  if (loading && !latestPred) {
    return (
      <div className="flex flex-col justify-center items-center h-96 space-y-4">
        <RefreshCw className="h-12 w-12 text-indigo-500 animate-spin" />
        <p className="text-gray-500 animate-pulse text-sm">Evaluating convective CAPE energy & cloudburst potential...</p>
      </div>
    );
  }

  const riskLevel = latestPred?.risk_level || 'LOW';
  const prob = latestPred?.probability ?? 0.10;
  const features = latestPred?.contributing_features || {};

  const cape = features["Convective Energy (CAPE)"] ?? 450.0;
  const rainMm = features["Current Precip (mm)"] ?? 0.0;

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'bg-purple-600 text-white border-purple-700 shadow-sm';
      case 'HIGH': return 'bg-indigo-600 text-white border-indigo-700 shadow-sm';
      case 'MODERATE': return 'bg-blue-500 text-white border-blue-600 shadow-sm';
      default: return 'bg-emerald-500 text-white border-emerald-600 shadow-sm';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-700 via-blue-700 to-indigo-800 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-black/20 text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded">
              Atmospheric Convective Monitor
            </span>
            <span className="text-xs opacity-90">
              High-Resolution Numerical Convective Available Potential Energy (CAPE)
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight flex items-center gap-2">
            <CloudRain className="h-7 w-7 text-indigo-200" />
            Extreme Rainfall & Cloudburst Intelligence
          </h1>
          <p className="text-indigo-100 text-sm mt-1 max-w-2xl">
            Hyperlocal precipitation nowcasting monitoring convective updraft instability, mesoscale convective systems, and short-horizon urban deluge probabilities.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="bg-white hover:bg-indigo-50 text-indigo-900 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 shadow-sm transition active:scale-95 disabled:opacity-75"
        >
          <RefreshCw className={`h-4 w-4 text-indigo-600 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh Doppler Intel
        </button>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Risk Probability */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cloudburst Probability</p>
            <div className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider border ${getRiskBadgeColor(riskLevel)}`}>
              {riskLevel}
            </div>
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {(prob * 100).toFixed(1)}%
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${prob > 0.6 ? 'bg-purple-600' : prob > 0.3 ? 'bg-indigo-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, Math.max(5, prob * 100))}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Lead time: <strong>6 Hours</strong> convective lead window
          </p>
        </div>

        {/* Convective Energy CAPE */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Atmospheric Instability (CAPE)</p>
            <CloudLightning className="h-4 w-4 text-purple-600" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {cape} <span className="text-xs font-medium text-slate-500">J/kg</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-purple-600 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (cape / 2500.0) * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Threshold: <strong className="text-slate-800">{cape > 1500 ? 'Severe Thunderstorm Potential' : 'Stable Troposphere'}</strong>
          </p>
        </div>

        {/* Current Precipitation Intensity */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Current Rainfall Rate</p>
            <Droplets className="h-4 w-4 text-blue-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {rainMm} <span className="text-xs font-medium text-slate-500">mm/hr</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(5, (rainMm / 50.0) * 100))}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Status: <strong className="text-slate-800">{rainMm > 20 ? 'Heavy Inundating Rain' : 'Light / Trace Precipitation'}</strong>
          </p>
        </div>

        {/* Urban Storm Drain Saturation Index */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Drain Surcharge Buffer</p>
            <Waves className="h-4 w-4 text-cyan-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            85.0% <span className="text-xs font-medium text-slate-500">Free Head</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div className="h-full bg-cyan-500 rounded-full w-[85%]"></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Adyar & Cooum micro-catchment channels nominal
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-indigo-500" />
              Storm Action & Pump Pre-positioning
            </h2>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Stationary Pump Stations</p>
                <p className="text-xs text-slate-700 font-medium">
                  32 macro-pumps along Buckingham Canal primed on standby grid power.
                </p>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Subway Sump Pumps</p>
                <p className="text-xs text-slate-700 font-medium">
                  Gengu Reddy, RBI, and Villivakkam underpasses automated auto-start relays operational.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
            <Activity className="h-5 w-5 text-indigo-500" />
            Convective Energy Diagnostic
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Thermodynamic soundings for Greater Chennai atmospheric column
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Lifted Index (LI)</p>
              <p className="text-2xl font-black text-slate-800">-1.2</p>
              <span className="text-[10px] text-emerald-600 font-bold">Weak thunderstorm risk</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Precipitable Water (PWAT)</p>
              <p className="text-2xl font-black text-slate-800">42 mm</p>
              <span className="text-[10px] text-blue-600 font-bold">Moderate moisture load</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Deep Layer Shear</p>
              <p className="text-2xl font-black text-slate-800">18 kts</p>
              <span className="text-[10px] text-indigo-600 font-bold">Unorganized cellular convection</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
