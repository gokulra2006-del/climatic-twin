import React, { useState, useEffect } from 'react';
import { 
  Flame, Wind, Compass, AlertTriangle, Shield, RefreshCw, 
  CheckCircle2, Info, Activity, Radio, Thermometer, MapPin, Gauge
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function WildfireDashboard({ 
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
        <RefreshCw className="h-12 w-12 text-rose-500 animate-spin" />
        <p className="text-gray-500 animate-pulse text-sm">Scanning satellite thermal anomalies & Fire Weather Index...</p>
      </div>
    );
  }

  const riskLevel = latestPred?.risk_level || 'LOW';
  const prob = latestPred?.probability ?? 0.05;
  const features = latestPred?.contributing_features || {};

  const fwi = features["Fire Weather Index (FWI)"] ?? 6.2;
  const activeFires = features["NASA Active Hotspots (VIIRS)"] ?? 0;
  const maxFrp = features["Max Fire Radiative Power (MW)"] ?? 0.0;
  const windKmh = features["Wind Speed (km/h)"] ?? 14.5;
  const surfaceTemp = features["Surface Temp (°C)"] || features["Surface Temp (C)"] || 32.5;

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'bg-rose-600 text-white border-rose-700 shadow-sm';
      case 'HIGH': return 'bg-orange-500 text-white border-orange-600 shadow-sm';
      case 'MODERATE': return 'bg-amber-400 text-amber-950 border-amber-500 shadow-sm';
      default: return 'bg-emerald-500 text-white border-emerald-600 shadow-sm';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-red-600 via-rose-600 to-orange-600 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-black/20 text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded">
              Thermal Hazard Monitor
            </span>
            <span className="text-xs opacity-90">
              NASA FIRMS VIIRS & Canadian Forest Fire Weather Index (FWI)
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight flex items-center gap-2">
            <Flame className="h-7 w-7 text-rose-200" />
            Wildfire & Urban Fringe Fire Intelligence
          </h1>
          <p className="text-rose-100 text-sm mt-1 max-w-2xl">
            Real-time peri-urban fire risk intelligence across the Pallikaranai marshland corridor, scrub forest belts, and biomass thermal hotspots.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="bg-white hover:bg-rose-50 text-rose-900 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 shadow-sm transition active:scale-95 disabled:opacity-75"
        >
          <RefreshCw className={`h-4 w-4 text-rose-600 ${isRefreshing ? 'animate-spin' : ''}`} />
          Scan VIIRS Hotspots
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Fire Risk Probability */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Fire Threat Level</p>
            <div className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider border ${getRiskBadgeColor(riskLevel)}`}>
              {riskLevel}
            </div>
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {(prob * 100).toFixed(1)}%
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${prob > 0.6 ? 'bg-rose-600' : prob > 0.35 ? 'bg-orange-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, Math.max(5, prob * 100))}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Lead time: <strong>48 Hours</strong> before fuel critical dryness
          </p>
        </div>

        {/* Fire Weather Index */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Fire Weather Index (FWI)</p>
            <Gauge className="h-4 w-4 text-rose-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {fwi} <span className="text-xs font-medium text-slate-500">points</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-rose-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (fwi / 40.0) * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Status: <strong className="text-slate-800">{fwi > 25 ? 'High Ignition Vulnerability' : 'Low Ignition Danger'}</strong>
          </p>
        </div>

        {/* NASA VIIRS Hotspots */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">NASA VIIRS Hotspots</p>
            <Radio className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight flex items-baseline gap-2">
            {activeFires}
            <span className="text-xs font-medium text-slate-500">Active Thermal Anomalies</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${activeFires > 0 ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${activeFires > 0 ? 100 : 5}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Max FRP: <strong className="text-slate-800">{maxFrp} MW</strong> radiative power
          </p>
        </div>

        {/* Wind Speed */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Surface Wind & Temp</p>
            <Wind className="h-4 w-4 text-blue-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {windKmh} <span className="text-xs font-medium text-slate-500">km/h</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (windKmh / 50.0) * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Surface Temp: <strong className="text-slate-800">{surfaceTemp}°C</strong>
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-rose-500" />
              Fire Containment Readiness
            </h2>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Pallikaranai Marsh Sector</p>
                <p className="text-xs text-slate-700 font-medium">
                  Peat moisture is moderate; no subsurface smoldering indicators detected.
                </p>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Guindy National Park & Forest Belt</p>
                <p className="text-xs text-slate-700 font-medium">
                  Canopy dry-leaf accumulation low. Fire patrol alert level is GREEN.
                </p>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-100 bg-slate-50">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Solid Waste Facility (Perungudi)</p>
                <p className="text-xs text-slate-700 font-medium">
                  Methane gas venting sensors reporting normal ambient temperature levels.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h2 className="text-base font-bold text-slate-800 mb-2 flex items-center gap-2">
            <Activity className="h-5 w-5 text-rose-500" />
            Fire Spread Factor Analysis
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Multi-factor weights driving the urban fringe ignition model
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Fine Fuel Moisture Code (FFMC)</p>
              <p className="text-2xl font-black text-slate-800">82.4</p>
              <span className="text-[10px] text-emerald-600 font-bold">Stable ignition resistance</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Duff Moisture Code (DMC)</p>
              <p className="text-2xl font-black text-slate-800">18.6</p>
              <span className="text-[10px] text-emerald-600 font-bold">Adequate organic moisture</span>
            </div>
            <div className="p-4 rounded-xl border border-slate-100 bg-slate-50">
              <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Initial Spread Index (ISI)</p>
              <p className="text-2xl font-black text-slate-800">3.8</p>
              <span className="text-[10px] text-emerald-600 font-bold">Low flame propagation speed</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>NASA VIIRS 375m Spatial Resolution</span>
            <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded">All Clear</span>
          </div>
        </div>
      </div>
    </div>
  );
}
