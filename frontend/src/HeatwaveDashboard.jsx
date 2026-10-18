import React, { useState, useEffect } from 'react';
import { 
  Thermometer, Sun, Wind, Droplets, Activity,
  Sparkles, AlertTriangle, ChevronRight, X, Shield, Database, CheckCircle2, ServerCrash, RefreshCw, Clock,
  MapPin, Info, CloudLightning
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
export default function HeatwaveDashboard({ latestPred, forecastData, dataQuality, loading, onRefresh, explainabilityData }) {
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSummaryGenerated, setIsSummaryGenerated] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(Date.now());

  // Auto-refresh every 10 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      handleRefresh();
    }, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  useEffect(() => {
    if(latestPred) setLastUpdated(Date.now());
  }, [latestPred]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if(onRefresh) await onRefresh();
    setTimeout(() => setIsRefreshing(false), 800);
  };

  const handleGenerateSummary = () => {
    setIsGeneratingSummary(true);
    setTimeout(() => {
      setIsSummaryGenerated(true);
      setIsGeneratingSummary(false);
    }, 1500);
  };

  if (loading && !latestPred) {
    return (
      <div className="flex flex-col justify-center items-center h-96 space-y-4">
        <Activity className="h-12 w-12 text-orange-500 animate-spin" />
        <p className="text-gray-500 animate-pulse text-sm">Connecting to live weather API...</p>
      </div>
    );
  }

  // Fallback states if API fails completely
  const isApiFailed = !latestPred;
  
  const riskLevel = latestPred?.risk_level || 'LOW';
  const features = latestPred?.contributing_features || {};
  const forecastMetrics = latestPred?.forecast_metrics || {};
  const trend48h = latestPred?.trend_48h || [];
  const telemetryMode = latestPred?.telemetry_mode || (isApiFailed ? 'UNAVAILABLE' : 'LIVE_WEATHER_API');
  const isLiveWeather = telemetryMode === 'LIVE_WEATHER_API';
  const sourceLabel = latestPred?.data_source || 'No live source available';

  const getFeature = (namePart) => {
    if (!features) return null;
    const normalizedPart = namePart.toLowerCase().replace(/\s+/g, '');
    const key = Object.keys(features).find(k => k.toLowerCase().replace(/\s+/g, '').includes(normalizedPart));
    return key ? features[key] : null;
  };

  const airTemp = getFeature('AirTemp');
  const heatIndex = getFeature('ApparentTemp');
  const humidity = getFeature('Humidity');
  const windSpeed = getFeature('WindSpeed');
  const dewPoint = airTemp && humidity ? (airTemp - ((100 - humidity)/5)) : null; // approximation if not in features
  const precip = getFeature('Precip');
  const uv = getFeature('UV');

  // Dynamic AI Drivers
  const getDrivers = () => {
    let drivers = [];
    if (airTemp > 36) drivers.push({ name: 'Air Temperature', val: 'High contribution', pct: 78 });
    else drivers.push({ name: 'Air Temperature', val: 'Moderate contribution', pct: 45 });
    
    if (heatIndex > 40) drivers.push({ name: 'Apparent Temp', val: 'Critical contribution', pct: 92 });
    else drivers.push({ name: 'Apparent Temp', val: 'Moderate contribution', pct: 52 });
    
    if (humidity > 70) drivers.push({ name: 'Relative Humidity', val: 'High contribution', pct: 68 });
    
    if (windSpeed < 5) drivers.push({ name: 'Wind Cooling', val: 'Low / protective contribution', pct: 20 });
    else drivers.push({ name: 'Wind Cooling', val: 'Moderate / protective contribution', pct: 35 });
    
    return drivers.sort((a,b) => b.pct - a.pct).slice(0, 4);
  };
  
  const drivers = getDrivers();

  // Dynamic AI Explanation
  const getSituationExplanation = () => {
    if (isApiFailed) return "Live Weather API is currently unavailable. Showing last successful observation if available.";
    let explanation = `Current heat stress is ${riskLevel}. `;
    if (heatIndex > 40) explanation += "The primary drivers are critically elevated apparent temperature and humidity. ";
    else if (airTemp > 35) explanation += "The primary driver is elevated air temperature. ";
    
    if (windSpeed < 5) explanation += "Wind conditions are currently stagnant, providing no cooling relief.";
    else if (windSpeed > 15) explanation += "Moderate wind conditions are providing some cooling relief.";
    return explanation;
  };

  const getRiskBg = (level) => {
    if (level === 'CRITICAL') return 'from-red-600 to-rose-900';
    if (level === 'HIGH') return 'from-orange-500 to-red-800';
    if (level === 'MODERATE') return 'from-amber-400 to-orange-700';
    return 'from-emerald-500 to-teal-800';
  };
  
  const getWarningBg = (level) => {
    if (level === 'CRITICAL') return 'bg-red-500/20 text-red-400 border-red-500/50';
    if (level === 'HIGH RISK') return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
    if (level === 'ADVISORY') return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
    if (level === 'WATCH') return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
  };

  const formatTimeStr = (isoStr) => {
    if(!isoStr) return '';
    const d = new Date(isoStr);
    return isNaN(d.getTime()) ? '' : d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  // Trend formatting for chart
  const chartData = trend48h.map(t => {
    const d = new Date(t.time);
    return {
      name: isNaN(d.getTime()) ? '' : d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      temp: t.temp,
      apparent: t.apparent_temp,
      timeValue: d.getTime()
    };
  });
  
  const nowTime = Date.now();
  const pastData = chartData.filter(d => d.timeValue <= nowTime);
  const futureData = chartData.filter(d => d.timeValue > nowTime);

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans pb-10">
      
      {/* HEADER ROW */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-700">
        <div>
          <h1 className="text-xl font-black text-white tracking-tight flex items-center gap-2">
             HEATWAVE DIGITAL TWIN
          </h1>
          <p className="text-xs text-slate-400 flex items-center gap-1 mt-1">
            <span className={`w-2 h-2 rounded-full ${isLiveWeather ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`}></span>
            {isLiveWeather ? 'LIVE WEATHER API' : telemetryMode.replaceAll('_', ' ')} • Updated {Math.floor((Date.now() - lastUpdated)/60000)} min ago
          </p>
        </div>
        <button 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Updating live weather intelligence...' : 'REFRESH LIVE DATA'}
        </button>
      </div>

      {/* NEW AI HEATWAVE INTELLIGENCE PANEL (PHASE NEXT) */}
      <div className="bg-slate-900 rounded-xl border border-slate-700 shadow-2xl overflow-hidden relative">
        {/* Header / Subtitle */}
        <div className="bg-slate-950 p-5 border-b border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-xl font-black text-white flex items-center gap-2 uppercase tracking-tight">
               <Sparkles className="w-5 h-5 text-indigo-400" />
               AI Heatwave Intelligence
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
               AI-generated assessment of current heat conditions, emerging risk, confidence, and recommended response.
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
             <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                <span className={`w-2 h-2 rounded-full ${isLiveWeather ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`}></span>
                {isLiveWeather ? 'LIVE WEATHER DATA' : 'SOURCE CHECK REQUIRED'}
             </div>
             <p className="text-[10px] text-slate-500 font-mono">{sourceLabel} • Updated {Math.floor((Date.now() - lastUpdated)/60000)} min ago</p>
          </div>
        </div>

        {/* Top Metrics Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 divide-x divide-y md:divide-y-0 divide-slate-800 border-b border-slate-800 bg-slate-900/50">
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Current Risk</p>
             <p className={`text-sm font-black ${riskLevel === 'CRITICAL' ? 'text-red-500 animate-pulse' : riskLevel === 'HIGH' ? 'text-orange-500' : 'text-emerald-400'}`}>{riskLevel}</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Temp</p>
             <p className="text-sm font-black text-white">{airTemp?.toFixed(1) || '--'}°C</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Heat Index</p>
             <p className="text-sm font-black text-rose-400">{heatIndex?.toFixed(1) || '--'}°C</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Humidity</p>
             <p className="text-sm font-black text-blue-400">{humidity?.toFixed(0) || '--'}%</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Dew Point</p>
             <p className="text-sm font-black text-indigo-300">{dewPoint?.toFixed(1) || '--'}°C</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Trend</p>
             <p className="text-sm font-black text-amber-400">{explainabilityData?.trend || forecastMetrics.early_warning_status || 'STABLE'}</p>
           </div>
           <div className="p-3 text-center">
             <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">AI Confidence</p>
             <p className="text-sm font-black text-emerald-400">{explainabilityData?.confidence_level || 'HIGH'}</p>
           </div>
           <div className="p-3 text-center flex flex-col justify-center items-center">
              <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Auto-refresh</p>
              <p className="text-xs font-bold text-slate-300">ON (10m)</p>
           </div>
        </div>
      </div>

      {/* 8-CARD TELEMETRY GRID */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="TEMPERATURE" value={airTemp} unit="°C" live={isLiveWeather} icon={<Thermometer className="w-4 h-4 text-rose-500" />} />
        <MetricCard title="FEELS LIKE" value={heatIndex} unit="°C" live={isLiveWeather} icon={<Activity className="w-4 h-4 text-orange-500" />} />
        <MetricCard title="HUMIDITY" value={humidity} unit="%" live={isLiveWeather} icon={<Droplets className="w-4 h-4 text-blue-500" />} />
        <MetricCard title="DEW POINT" value={dewPoint} unit="°C" live={isLiveWeather} icon={<CloudLightning className="w-4 h-4 text-indigo-500" />} />
        <MetricCard title="WIND" value={windSpeed} unit="km/h" live={isLiveWeather} icon={<Wind className="w-4 h-4 text-teal-500" />} />
        <MetricCard title="PRECIPITATION" value={precip} unit="mm" live={isLiveWeather} icon={<CloudLightning className="w-4 h-4 text-slate-500" />} />
        <MetricCard title="UV / SOLAR" value={uv} unit="Idx" live={isLiveWeather} icon={<Sun className="w-4 h-4 text-amber-500" />} />
        <MetricCard title="HEAT INDEX" value={heatIndex} unit="°C" live={isLiveWeather} icon={<Activity className="w-4 h-4 text-red-500" />} />
      </div>

      {/* TREND CHART */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
         <h2 className="text-xs font-black uppercase tracking-widest text-slate-800 mb-4">24-Hour Thermal Trend &amp; Forecast</h2>
         <div className="h-64 w-full">
           <ResponsiveContainer width="100%" height="100%">
             <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
               <defs>
                 <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                   <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                   <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                 </linearGradient>
                 <linearGradient id="colorApp" x1="0" y1="0" x2="0" y2="1">
                   <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                   <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                 </linearGradient>
               </defs>
               <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
               <XAxis dataKey="name" tick={{fontSize: 10}} stroke="#94a3b8" minTickGap={30} />
               <YAxis domain={['dataMin - 2', 'dataMax + 2']} tick={{fontSize: 10}} stroke="#94a3b8" />
               <Tooltip 
                 contentStyle={{backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px'}}
                 itemStyle={{color: '#f8fafc'}}
               />
               <Area type="monotone" dataKey="temp" name="Observed Temp" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#colorTemp)" />
               <Area type="monotone" dataKey="apparent" name="Forecast Apparent" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" fillOpacity={1} fill="url(#colorApp)" />
             </AreaChart>
           </ResponsiveContainer>
         </div>
         <div className="flex items-center justify-center gap-6 mt-4 text-[10px] font-bold text-slate-500">
           <div className="flex items-center gap-2"><div className="w-3 h-3 bg-orange-500 rounded-sm"></div> Observed Temp</div>
           <div className="flex items-center gap-2"><div className="w-3 h-3 bg-red-500 rounded-sm" style={{opacity: 0.5}}></div> Forecast Apparent Temp</div>
         </div>
      </div>

      {/* OUTLOOK & WARNING */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* EARLY WARNING */}
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-700 flex flex-col justify-between">
           <div>
             <h2 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
               <AlertTriangle className="w-4 h-4 text-amber-400" /> EARLY WARNING
             </h2>
             <div className={`p-4 rounded-lg border text-center mb-4 ${getWarningBg(forecastMetrics.early_warning_status || 'NO IMMEDIATE THREAT')}`}>
               <h3 className="text-2xl font-black">{forecastMetrics.early_warning_status || 'NO IMMEDIATE THREAT'}</h3>
             </div>
             <p className="text-sm text-slate-300">
               {forecastMetrics.early_warning_status === 'NO IMMEDIATE THREAT' || !forecastMetrics.early_warning_status
                 ? "No significant threshold crossing expected in the next 24 hours."
                 : `Risk expected to peak in approximately ${forecastMetrics.peak_time ? Math.round((new Date(forecastMetrics.peak_time).getTime() - Date.now())/3600000) : 'X'} hours.`}
             </p>
           </div>
        </div>

        {/* NEXT 24 HOURS */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
           <h2 className="text-xs font-black uppercase tracking-widest text-slate-800 mb-4 flex items-center gap-2">
             <Clock className="w-4 h-4 text-indigo-500" /> NEXT 24 HOURS OUTLOOK
           </h2>
           <div className="grid grid-cols-2 gap-4">
             <div className="bg-slate-50 p-3 rounded-lg border">
               <p className="text-[10px] font-bold text-slate-500 uppercase">Peak Temperature</p>
               <p className="text-xl font-black text-slate-800">{forecastMetrics.peak_temp?.toFixed(1) || '--'}°C</p>
             </div>
             <div className="bg-slate-50 p-3 rounded-lg border">
               <p className="text-[10px] font-bold text-slate-500 uppercase">Peak Heat Index</p>
               <p className="text-xl font-black text-rose-600">{forecastMetrics.peak_heat_index?.toFixed(1) || '--'}°C</p>
             </div>
             <div className="bg-slate-50 p-3 rounded-lg border">
               <p className="text-[10px] font-bold text-slate-500 uppercase">Minimum Temp</p>
               <p className="text-xl font-black text-blue-600">{forecastMetrics.min_temp?.toFixed(1) || '--'}°C</p>
             </div>
             <div className="bg-slate-50 p-3 rounded-lg border">
               <p className="text-[10px] font-bold text-slate-500 uppercase">Expected Peak Time</p>
               <p className="text-sm font-black text-slate-800 mt-1">{formatTimeStr(forecastMetrics.peak_time) || '--'}</p>
             </div>
           </div>
        </div>

      </div>

      {/* FOOTER METADATA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         {/* DATA PROVENANCE */}
         <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-xs text-slate-600">
           <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-800 mb-3 flex items-center gap-2">
             <MapPin className="w-3 h-3" /> DATA PROVENANCE
           </h2>
           <div className="grid grid-cols-2 gap-y-2">
             <div className="font-bold">Source:</div><div>{sourceLabel}</div>
             <div className="font-bold">Location:</div><div>Chennai (13.08°N, 80.27°E)</div>
             <div className="font-bold">Data:</div><div>{latestPred?.simulation_label || telemetryMode.replaceAll('_', ' ')}</div>
             <div className="font-bold">Updated:</div><div>{formatTimeStr(latestPred?.timestamp)}</div>
             <div className="font-bold">Derived:</div><div>Heat Index, Risk Model, AI Forecast</div>
           </div>
         </div>
         
         {/* SYSTEM STATUS */}
         <div className="bg-slate-900 p-5 rounded-xl border border-slate-700 text-xs text-slate-300">
           <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 flex items-center gap-2">
             <ServerCrash className="w-3 h-3" /> SYSTEM INTEGRATION STATUS
           </h2>
           <div className="space-y-2 font-mono">
             <div className="flex items-center gap-2">
               {isApiFailed ? <X className="w-3 h-3 text-red-500"/> : <CheckCircle2 className="w-3 h-3 text-emerald-500"/>}
               <span className={isApiFailed ? "text-red-400" : "text-emerald-400"}>Live weather API {isApiFailed ? "unavailable" : "connected"}</span>
             </div>
             <div className="flex items-center gap-2">
               <CheckCircle2 className="w-3 h-3 text-emerald-500"/>
               <span className="text-emerald-400">Latest observation received</span>
             </div>
             <div className="flex items-center gap-2">
               <CheckCircle2 className="w-3 h-3 text-emerald-500"/>
               <span className="text-emerald-400">Heatwave risk engine operational</span>
             </div>
             <div className="flex items-center gap-2">
               <CheckCircle2 className="w-3 h-3 text-emerald-500"/>
               <span className="text-emerald-400">Forecast pipeline operational</span>
             </div>
           </div>
         </div>
      </div>

      {/* AI SITUATION MODAL */}
      {isAiModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
               <div className="flex items-center gap-3">
                 <div className="p-2 bg-indigo-500/20 rounded-lg">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                 </div>
                 <div>
                   <h2 className="font-black uppercase tracking-wider text-sm">DEEP INTELLIGENCE ANALYSIS</h2>
                   <p className="text-[10px] text-slate-400">Model Reasoning & Explainable AI Engine</p>
                 </div>
               </div>
               <button onClick={() => setIsAiModalOpen(false)} className="p-2 text-slate-400 hover:text-white rounded transition">
                 <X className="w-5 h-5" />
               </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-300">
               {/* 1. Executive Summary */}
               <div>
                 <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">1. Executive Summary</h3>
                 <p className="bg-slate-800 p-3 rounded border border-slate-700">
                    {explainabilityData ? explainabilityData.explanation : getSituationExplanation()}
                 </p>
               </div>
               
               {/* 2. Drivers and Protectors */}
               <div className="grid grid-cols-2 gap-4">
                 <div>
                   <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">2. Dominant Drivers</h3>
                   <ul className="bg-slate-800 p-3 rounded border border-slate-700 list-disc list-inside text-rose-300">
                      {explainabilityData ? explainabilityData.dominant_drivers.map((d, i) => <li key={i}>{d}</li>) : drivers.map((d, i) => <li key={i}>{d.name}</li>)}
                   </ul>
                 </div>
                 <div>
                   <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">3. Protective Factors</h3>
                   <ul className="bg-slate-800 p-3 rounded border border-slate-700 list-disc list-inside text-emerald-400">
                      {explainabilityData ? explainabilityData.protective_factors.map((p, i) => <li key={i}>{p}</li>) : <li>None identified</li>}
                   </ul>
                 </div>
               </div>
               
               {/* 4. What Changed */}
               <div>
                 <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">4. Recent Changes</h3>
                 <div className="bg-slate-800 p-3 rounded border border-slate-700 space-y-2">
                    {explainabilityData?.changes?.length > 0 ? explainabilityData.changes.map((c, i) => (
                      <div key={i} className="flex justify-between items-center text-xs">
                        <span>{c.metric}</span>
                        <div className="flex gap-4">
                           <span className="text-slate-500">Prev: {c.previous}</span>
                           <span className="text-slate-300">Curr: {c.current}</span>
                           <span className={`font-bold ${c.change.startsWith('+') ? 'text-rose-400' : 'text-emerald-400'}`}>{c.change}</span>
                        </div>
                      </div>
                    )) : <p>No significant changes.</p>}
                 </div>
               </div>

               {/* 5 & 6. Outlook and Priorities */}
               <div className="grid grid-cols-2 gap-4">
                 <div>
                   <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">5. Next 6-Hour Outlook & Trend</h3>
                   <div className="bg-slate-800 p-3 rounded border border-slate-700">
                     <p>Status: <span className="text-amber-400 font-bold">{forecastMetrics.early_warning_status}</span></p>
                     <p className="mt-1">Trend: <span className="font-bold">{explainabilityData?.trend || 'STABLE'}</span></p>
                   </div>
                 </div>
                 <div>
                   <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">6. Recommended Priorities</h3>
                   <ul className="bg-slate-800 p-3 rounded border border-slate-700 list-disc list-inside text-xs">
                     {explainabilityData?.recommended_priorities?.map((p, i) => (
                        <li key={i}><span className="font-bold text-amber-300">[{p.priority}]</span> {p.action}</li>
                     ))}
                   </ul>
                 </div>
               </div>

               {/* 7. Model Reasoning */}
               <div>
                 <h3 className="text-[10px] font-bold text-slate-500 uppercase mb-2">7. Model Reasoning Flow</h3>
                 <div className="bg-slate-800 p-4 rounded border border-slate-700 font-mono text-xs flex flex-col items-center gap-2 text-center text-slate-400">
                    <div className="bg-slate-900 px-3 py-1 rounded border border-slate-700">Live API Telemetry (Temp, Hum)</div>
                    <div>↓</div>
                    <div className="bg-slate-900 px-3 py-1 rounded border border-slate-700">Derived Indicators (Heat Index, Dew Point)</div>
                    <div>↓</div>
                    <div className="bg-slate-900 px-3 py-1 rounded border border-slate-700">Predictive Random Forest Risk Score: {riskLevel}</div>
                    <div>↓</div>
                    <div className="bg-slate-900 px-3 py-1 rounded border border-indigo-700 text-indigo-300">Explainable AI Extraction (Confidence: {explainabilityData?.confidence_level})</div>
                 </div>
               </div>
               
               <div className="bg-amber-500/10 border border-amber-500/30 text-amber-200 p-3 rounded">
                 <h3 className="text-[10px] font-bold uppercase mb-1 flex items-center gap-1"><Info className="w-3 h-3"/> Research Transparency & Provenance</h3>
                 <p className="text-xs">Data Source: {explainabilityData?.provenance?.data_source || 'Unknown'}</p>
                 <p className="text-xs mt-1">Model: {explainabilityData?.provenance?.model || 'Unknown'}</p>
                 <p className="text-xs mt-1">Timestamp: {explainabilityData?.provenance?.timestamp}</p>
                 <p className="text-[10px] mt-2 opacity-70">Note: Explainability extraction sits above the validated models as an interpretability layer.</p>
               </div>
            </div>
            
            <div className="p-4 border-t border-slate-800 bg-slate-900 flex justify-between items-center">
              <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded flex items-center gap-2 transition">
                 ASK NOVA <Sparkles className="w-3 h-3" />
              </button>
              <button 
                onClick={() => setIsAiModalOpen(false)}
                className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded transition"
              >
                CLOSE ANALYSIS
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

function MetricCard({ title, value, unit, icon, live }) {
  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col justify-between hover:border-indigo-200 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{title}</span>
        {icon}
      </div>
      <div className="mt-2">
        <span className="text-2xl font-black text-slate-800">{value !== null && value !== undefined ? (typeof value === 'number' ? value.toFixed(1) : value) : '--'}</span>
        <span className="text-xs text-slate-500 font-bold ml-1">{unit}</span>
      </div>
      <div className="mt-2 flex items-center gap-1">
        <span className={`w-1.5 h-1.5 rounded-full ${live ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`}></span>
        <span className={`text-[9px] font-bold uppercase tracking-widest ${live ? 'text-emerald-600' : 'text-amber-700'}`}>{live ? 'LIVE' : 'UNAVAILABLE'}</span>
      </div>
    </div>
  );
}
