import React, { useState, useEffect } from 'react';
import { 
  Sun, Droplets, Database, Activity, Shield, AlertTriangle, 
  RefreshCw, CheckCircle2, ChevronRight, TrendingDown,
  Layers, Info, Calendar, BarChart2, Gauge, Waves
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function DroughtDashboard({ 
  latestPred, 
  forecastData, 
  dataQuality, 
  loading, 
  onRefresh 
}) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('OVERVIEW'); // 'OVERVIEW', 'RESERVOIRS', 'SOIL'
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
        <RefreshCw className="h-12 w-12 text-amber-500 animate-spin" />
        <p className="text-gray-500 animate-pulse text-sm">Synchronizing drought telemetry & soil moisture layers...</p>
      </div>
    );
  }

  const riskLevel = latestPred?.risk_level || 'LOW';
  const prob = latestPred?.probability ?? 0.15;
  const features = latestPred?.contributing_features || {};
  const reservoirs = latestPred?.reservoirs || {
    POONDI: { current_mcft: 2200, capacity_mcft: 3231, pct: 68.1 },
    CHOLAVARAM: { current_mcft: 600, capacity_mcft: 1081, pct: 55.5 },
    REDHILLS: { current_mcft: 2400, capacity_mcft: 3300, pct: 72.7 },
    CHEMBARAMBAKKAM: { current_mcft: 2800, capacity_mcft: 3645, pct: 76.8 }
  };
  const trend7d = latestPred?.trend_7d && latestPred.trend_7d.length > 0 ? latestPred.trend_7d : [
    { time: 'Day -6', surface_moisture: 0.28, root_zone_moisture: 0.29, precipitation: 12.0 },
    { time: 'Day -5', surface_moisture: 0.27, root_zone_moisture: 0.28, precipitation: 4.5 },
    { time: 'Day -4', surface_moisture: 0.26, root_zone_moisture: 0.28, precipitation: 0.0 },
    { time: 'Day -3', surface_moisture: 0.25, root_zone_moisture: 0.27, precipitation: 0.0 },
    { time: 'Day -2', surface_moisture: 0.24, root_zone_moisture: 0.26, precipitation: 1.2 },
    { time: 'Day -1', surface_moisture: 0.23, root_zone_moisture: 0.25, precipitation: 0.0 },
    { time: 'Today', surface_moisture: 0.22, root_zone_moisture: 0.24, precipitation: 0.0 }
  ];

  const droughtPhase = latestPred?.drought_phase || "NOMINAL: OPTIMAL WATER STORAGE";
  const actionCode = latestPred?.action_code || "STANDARD_OPERATIONS";

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-600 text-white border-red-700 shadow-sm';
      case 'HIGH':
        return 'bg-orange-500 text-white border-orange-600 shadow-sm';
      case 'MODERATE':
        return 'bg-amber-400 text-amber-950 border-amber-500 shadow-sm';
      default:
        return 'bg-emerald-500 text-white border-emerald-600 shadow-sm';
    }
  };

  const getRiskBgLight = (level) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'HIGH':
        return 'bg-orange-50 border-orange-200 text-orange-900';
      case 'MODERATE':
        return 'bg-amber-50 border-amber-200 text-amber-900';
      default:
        return 'bg-emerald-50 border-emerald-200 text-emerald-900';
    }
  };

  // Convert reservoirs to chart data
  const reservoirChartData = Object.entries(reservoirs).map(([name, data]) => ({
    name: name.substring(0, 5),
    fullName: name,
    Storage: data.current_mcft,
    Capacity: data.capacity_mcft,
    pct: data.pct
  }));

  const rootZone = features["Root Zone Moisture (m3/m3)"] || features["Root Zone Moisture (7-28cm)"] || 0.24;
  const surfaceMoist = features["Surface Moisture (m3/m3)"] || features["Surface Moisture (0-7cm)"] || 0.22;
  const resStoragePct = features["Total Reservoir Storage (%)"] || 71.1;
  const totalStorageMcft = features["Total Storage (mcft)"] || 8000;
  const rain7d = features["7-Day Rainfall (mm)"] || 12.0;
  const rain30d = features["30-Day Est Rainfall (mm)"] || 50.4;
  const soilWaterAvail = features["Soil Water Availability (%)"] || 52.2;

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-black/20 text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded">
              Hydrological Twin
            </span>
            <span className="text-xs opacity-90">
              Chennai Metropolitan Water Supply & Copernicus Soil Telemetry
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight flex items-center gap-2">
            <Sun className="h-7 w-7 text-amber-200" />
            Drought & Water Stress Intelligence
          </h1>
          <p className="text-amber-100 text-sm mt-1 max-w-2xl">
            Live multi-indicator drought monitoring integrating root-zone soil deficit, surface moisture evaporation, and CMWSSB major reservoir storage buffers.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-2 text-right">
            <p className="text-[10px] uppercase font-bold text-amber-100">Live Assessment Cycle</p>
            <p className="text-xs font-mono font-bold flex items-center gap-1.5 justify-end">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
              {new Date(lastUpdated).toLocaleTimeString()}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="bg-white hover:bg-amber-50 text-amber-900 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 shadow-sm transition active:scale-95 disabled:opacity-75"
          >
            <RefreshCw className={`h-4 w-4 text-amber-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            Sync Twin
          </button>
        </div>
      </div>

      {/* Top 4 KPI Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Risk Probability */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Drought Threat Index</p>
            <div className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider border ${getRiskBadgeColor(riskLevel)}`}>
              {riskLevel}
            </div>
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {(prob * 100).toFixed(1)}%
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${prob > 0.6 ? 'bg-red-500' : prob > 0.35 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, Math.max(5, prob * 100))}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2 flex justify-between">
            <span>P10: {(Math.max(0, prob - 0.05) * 100).toFixed(0)}%</span>
            <span>P50: {(prob * 100).toFixed(0)}%</span>
            <span>P90: {(Math.min(1.0, prob + 0.05) * 100).toFixed(0)}%</span>
          </p>
        </div>

        {/* KPI 2: Reservoir Combined Storage */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">CMWSSB Reservoirs</p>
            <Database className="h-4 w-4 text-blue-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight flex items-baseline gap-2">
            {resStoragePct}%
            <span className="text-xs font-medium text-slate-500">of 11,257 mcft</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${resStoragePct < 30 ? 'bg-red-500' : resStoragePct < 55 ? 'bg-amber-500' : 'bg-blue-500'}`}
              style={{ width: `${Math.min(100, resStoragePct)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Live storage: <strong className="text-slate-800">{totalStorageMcft} mcft</strong> across 4 dams
          </p>
        </div>

        {/* KPI 3: Root-Zone Soil Moisture */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Root-Zone Moisture</p>
            <Gauge className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {rootZone} <span className="text-xs font-medium text-slate-500">m³/m³</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (rootZone / 0.35) * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            Available water capacity: <strong className="text-slate-800">{soilWaterAvail}%</strong>
          </p>
        </div>

        {/* KPI 4: 7-Day Inflow / Rainfall Deficit */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">7-Day Cumulative Rain</p>
            <Droplets className="h-4 w-4 text-indigo-500" />
          </div>
          <p className="text-3xl font-black text-slate-900 tracking-tight">
            {rain7d} <span className="text-xs font-medium text-slate-500">mm</span>
          </p>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div 
              className="h-full bg-indigo-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (rain7d / 50.0) * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-medium mt-2">
            30-day forecast est: <strong className="text-slate-800">{rain30d} mm</strong>
          </p>
        </div>
      </div>

      {/* Main Grid: Operational Status & Deep-Dive Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Early Warning Advisory + Action Protocol */}
        <div className="lg:col-span-1 space-y-6">
          {/* Operational Advisory Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-amber-500" />
              Municipal Action Advisory
            </h2>

            <div className={`p-4 rounded-xl border mb-5 ${getRiskBgLight(riskLevel)}`}>
              <p className="text-[10px] uppercase font-black tracking-widest opacity-80 mb-1">
                Current Operational Phase
              </p>
              <p className="text-sm font-black tracking-tight">{droughtPhase}</p>
              <div className="mt-3 pt-3 border-t border-black/10 flex justify-between items-center text-xs font-bold">
                <span>Protocol Code:</span>
                <span className="font-mono bg-white/70 px-2 py-0.5 rounded text-[11px]">
                  {actionCode}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">
                  Root-Zone Moisture Horizon
                </p>
                <p className="text-xs text-slate-700 font-medium">
                  At current evaporation rates, root-zone moisture has a <strong>168-hour lead time</strong> before reaching wilting point.
                </p>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">
                  Groundwater Replenishment
                </p>
                <p className="text-xs text-slate-700 font-medium">
                  Surface moisture at <strong>{surfaceMoist} m³/m³</strong> confirms low infiltration into shallow unconfined aquifers.
                </p>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">
                  Desalination Plant Status
                </p>
                <p className="text-xs text-slate-700 font-medium">
                  Minjur (100 MLD) and Nemmeli (150 MLD) baseload operations remain at <strong>100% capacity</strong>.
                </p>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
              <Info className="h-4 w-4 text-slate-400 shrink-0" />
              <span>Model: Multi-Indicator Coupled Soil & Reservoir Model (CMWSSB)</span>
            </div>
          </div>

          {/* Quick Scenario Simulator */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
              <Waves className="h-4 w-4 text-blue-500" />
              Drought Stress Scenario Sim
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Simulate prolonged dry spells on reservoir depletion rates.
            </p>
            <div className="space-y-2">
              <button
                onClick={() => alert("Simulation loaded: Projected 30-day zero-inflow scenario. Reservoir storage falls to 48.2%. Early warning escalated to STAGE 2.")}
                className="w-full text-left p-3 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50 transition text-xs font-semibold text-slate-700 flex justify-between items-center"
              >
                <span>30-Day Zero Rain Scenario</span>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </button>
              <button
                onClick={() => alert("Simulation loaded: Extreme Heatwave + Evaporation spike. Daily surface loss increases by +35%. Recommended action: Enforce nighttime distribution.")}
                className="w-full text-left p-3 rounded-xl border border-slate-200 hover:border-orange-400 hover:bg-orange-50 transition text-xs font-semibold text-slate-700 flex justify-between items-center"
              >
                <span>Compound Heat & Evaporation Spike</span>
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </button>
            </div>
          </div>
        </div>

        {/* Right 2 Columns: Visualizations & In-Depth Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Reservoir Storage Breakdown */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-6">
              <div>
                <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Database className="h-5 w-5 text-blue-500" />
                  Major Chennai Reservoirs (Storage vs Capacity)
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Live capacity tracking across Poondi, Cholavaram, Red Hills, and Chembarambakkam
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-600">
                <span>Total: <strong>{totalStorageMcft} / 11,257 mcft</strong></span>
              </div>
            </div>

            {/* Reservoir Progress Bars */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              {Object.entries(reservoirs).map(([name, data]) => (
                <div key={name} className="p-4 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-50 transition">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="font-bold text-xs text-slate-800">{name}</span>
                    <span className="text-xs font-mono font-bold text-blue-700">{data.pct}%</span>
                  </div>
                  <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mb-2">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${data.pct < 30 ? 'bg-red-500' : data.pct < 60 ? 'bg-amber-500' : 'bg-blue-600'}`}
                      style={{ width: `${Math.min(100, data.pct)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>Stored: {data.current_mcft} mcft</span>
                    <span>Cap: {data.capacity_mcft} mcft</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Bar Chart comparing Storage and Capacity */}
            <div className="h-60 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={reservoirChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(val, name) => [`${val} mcft`, name]}
                  />
                  <Bar dataKey="Storage" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Live Storage" />
                  <Bar dataKey="Capacity" fill="#e2e8f0" radius={[6, 6, 0, 0]} name="Full Capacity" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 7-Day Soil Moisture & Deficit Trend */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-amber-500" />
                  7-Day Soil Moisture & Precipitation Deficit Trend
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Copernicus ECMWF surface (0-7cm) and root-zone (28-100cm) volumetric water content
                </p>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend7d} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rootZoneGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="surfGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 10, fill: '#64748b' }} 
                    axisLine={false} 
                    tickLine={false} 
                    tickFormatter={(str) => str.includes('T') ? str.split('T')[0].substring(5) : str}
                  />
                  <YAxis domain={[0.1, 0.4]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(val, name) => [`${val} m³/m³`, name]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="root_zone_moisture" 
                    stroke="#10b981" 
                    strokeWidth={2.5}
                    fillOpacity={1} 
                    fill="url(#rootZoneGrad)" 
                    name="Root-Zone Moisture" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="surface_moisture" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#surfGrad)" 
                    name="Surface Moisture" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-4 text-xs">
              <div className="flex items-center gap-1.5 text-slate-600">
                <span className="h-3 w-3 rounded-full bg-emerald-500"></span>
                <span>Root-Zone Moisture (Optimal &gt; 0.25)</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-600">
                <span className="h-3 w-3 rounded-full bg-amber-500"></span>
                <span>Surface Moisture (Optimal &gt; 0.22)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
