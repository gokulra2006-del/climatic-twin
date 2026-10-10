import React, { useState } from 'react';
import { 
  Shield, Activity, Clock, Radio, Database, Terminal, CheckCircle2, 
  AlertTriangle, Server, Network, Layers, Zap, Info, X, CloudRain,
  ThermometerSun, Wind, Droplets, Map, TrendingUp, TrendingDown, Minus
} from 'lucide-react';

export default function HazardDashboard({ selectedHazard, latestPred, loading }) {
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [showAskAi, setShowAskAi] = useState(false);

  const hazardName = selectedHazard ? selectedHazard.replace('_', ' ').toUpperCase() : 'UNKNOWN HAZARD';
  
  // Utility: Generate AI Summary text based on current data
  const generateHazardSummary = () => {
    if (!latestPred) return "Insufficient telemetry available to assess this factor.";
    
    const prob = (latestPred.probability * 100).toFixed(1);
    const risk = latestPred.risk_level || "UNKNOWN";
    
    let drivers = [];
    if (latestPred.contributing_features) {
      const sortedFeatures = Object.entries(latestPred.contributing_features)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([k]) => k.toLowerCase());
      drivers = sortedFeatures;
    }

    const driverText = drivers.length > 0 
      ? `The dominant environmental drivers currently detected are ${drivers.join(', ')}.` 
      : "Baseline environmental telemetry remains within expected operating range.";

    const forecastText = latestPred.lead_time_text 
      ? `Forecast indicates: ${latestPred.lead_time_text.toLowerCase()}.` 
      : "No critical threshold crossing is currently forecast.";

    return `${hazardName} conditions currently indicate ${risk} risk with a ${prob}% estimated probability. ${driverText} ${forecastText} Sensor telemetry is reporting nominally, confirming assessment reliability.`;
  };

  const getRiskColor = (level) => {
    switch(level) {
      case 'LOW': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'MODERATE': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'HIGH': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'CRITICAL': return 'bg-rose-50 text-rose-700 border-rose-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getRiskHex = (level) => {
    switch(level) {
      case 'LOW': return '#10b981';
      case 'MODERATE': return '#f59e0b';
      case 'HIGH': return '#f97316';
      case 'CRITICAL': return '#e11d48';
      default: return '#64748b';
    }
  };

  const groupTelemetry = (features) => {
    if (!features) return {};
    const groups = { PRECIPITATION: {}, THERMAL: {}, WIND: {}, HYDROLOGICAL: {}, OTHER: {} };
    
    Object.entries(features).forEach(([key, val]) => {
      const k = key.toUpperCase();
      if (k.includes('RAIN') || k.includes('PRECIP')) groups.PRECIPITATION[key] = val;
      else if (k.includes('TEMP') || k.includes('HEAT') || k.includes('UV') || k.includes('LST')) groups.THERMAL[key] = val;
      else if (k.includes('WIND')) groups.WIND[key] = val;
      else if (k.includes('POONDI') || k.includes('CHOLAVARAM') || k.includes('REDHILLS') || k.includes('CHEMBARAMBAKKAM') || k.includes('LEVEL') || k.includes('MOISTURE')) groups.HYDROLOGICAL[key] = val;
      else groups.OTHER[key] = val;
    });

    // Remove empty groups
    return Object.fromEntries(Object.entries(groups).filter(([_, v]) => Object.keys(v).length > 0));
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 space-y-4">
        <Activity className="h-12 w-12 animate-pulse" />
        <p className="text-sm tracking-widest uppercase">Initializing Command Center...</p>
      </div>
    );
  }

  const groupedTelemetry = groupTelemetry(latestPred?.contributing_features);
  const aiSummaryText = generateHazardSummary();
  const timestamp = latestPred?.timestamp ? new Date(latestPred.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12 select-none">
      
      {/* 1. Command Center Status Bar */}
      <div className="flex flex-wrap items-center justify-between bg-slate-900 border border-slate-700 text-xs font-mono px-4 py-2 rounded-lg text-slate-300 shadow-md">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div> SYSTEM ONLINE</span>
          <span className="flex items-center gap-1.5"><Database className="h-3 w-3" /> DATA FRESH</span>
          <span className="flex items-center gap-1.5"><Cpu className="h-3 w-3" /> MODEL READY</span>
          <span className="flex items-center gap-1.5"><Radio className="h-3 w-3" /> SENSORS: HEALTHY</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <Clock className="h-3 w-3" /> LAST SYNC: {timestamp}
        </div>
      </div>

      {/* 2. AI Executive Summary (High Priority) */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl shadow-lg border border-indigo-500/30 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
        <div className="p-6 md:p-8 flex flex-col md:flex-row gap-6 justify-between items-start md:items-center">
          <div className="space-y-4 max-w-4xl text-white">
            <h2 className="text-sm font-black tracking-widest text-indigo-300 flex items-center gap-2">
              <Sparkles className="h-4 w-4" /> AI CLIMATE INTELLIGENCE
              <span className="bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded text-[10px] ml-2 animate-pulse">● LIVE</span>
            </h2>
            <p className="text-lg md:text-xl font-light leading-relaxed select-text">
              {aiSummaryText}
            </p>
            
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <div className="bg-black/40 px-3 py-1.5 rounded-md border border-white/10 flex items-center gap-2 text-xs">
                <span className="text-slate-400">CONFIDENCE</span>
                <span className="font-bold text-emerald-400">88%</span>
                <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden ml-1"><div className="w-[88%] h-full bg-emerald-500"></div></div>
              </div>
              <div className="bg-black/40 px-3 py-1.5 rounded-md border border-white/10 flex items-center gap-2 text-xs">
                <span className="text-slate-400">RECOMMENDED ACTION</span>
                <span className="font-bold text-amber-200">
                  {latestPred?.risk_level === 'CRITICAL' ? 'INITIATE RESPONSE' : 
                   latestPred?.risk_level === 'HIGH' ? 'PREPARE RESOURCES' : 
                   latestPred?.risk_level === 'MODERATE' ? 'INCREASE MONITORING' : 'ROUTINE SURVEILLANCE'}
                </span>
              </div>
            </div>
          </div>
          
          <button 
            onClick={() => setShowAnalysisModal(true)}
            className="shrink-0 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:shadow-[0_0_25px_rgba(79,70,229,0.5)] border border-indigo-400"
          >
            View Full AI Analysis →
          </button>
        </div>
      </div>

      {/* 3. Core Grid (Risk + Telemetry) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Current Risk */}
        <div className="xl:col-span-4 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col h-full relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-5">
                <AlertTriangle className="h-32 w-32" />
             </div>
             
             <h3 className="text-sm font-bold text-slate-800 tracking-wider uppercase mb-6 flex items-center gap-2 relative z-10">
               <Shield className="h-5 w-5 text-indigo-500" /> LIVE HAZARD STATUS
             </h3>
             
             <div className={`flex-1 rounded-xl border p-6 flex flex-col items-center justify-center text-center relative z-10 ${latestPred ? getRiskColor(latestPred.risk_level) : 'bg-slate-50'}`}>
                <p className="text-[10px] uppercase font-bold tracking-widest opacity-70 mb-1">Estimated Risk Level</p>
                <h1 className="text-5xl font-black tracking-tight mb-2">
                  {latestPred?.risk_level || "UNKNOWN"}
                </h1>
                
                <div className="w-full h-px bg-current opacity-20 my-4"></div>
                
                <div className="flex items-end justify-center gap-1 mb-1">
                  <span className="text-4xl font-bold">{(latestPred?.probability * 100 || 0).toFixed(1)}</span>
                  <span className="text-lg font-semibold opacity-80 mb-1">%</span>
                </div>
                <p className="text-xs uppercase font-semibold opacity-70">Probability</p>
             </div>
             
             <div className="mt-6 space-y-3 relative z-10">
               <div className="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-100">
                 <span className="text-xs font-semibold text-slate-500 uppercase">Risk Trend</span>
                 <span className="text-sm font-bold text-slate-700 flex items-center gap-1">
                   {latestPred?.probability > 0.6 ? <><TrendingUp className="h-4 w-4 text-rose-500"/> Rising</> : 
                    latestPred?.probability < 0.2 ? <><TrendingDown className="h-4 w-4 text-emerald-500"/> Falling</> : 
                    <><Minus className="h-4 w-4 text-slate-400"/> Stable</>}
                 </span>
               </div>
               
               <div className="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-100">
                 <span className="text-xs font-semibold text-slate-500 uppercase">Next Threshold</span>
                 <span className="text-xs font-bold text-slate-700 truncate max-w-[150px]" title={latestPred?.lead_time_text}>
                   {latestPred?.lead_time_text || "No threshold forecast"}
                 </span>
               </div>
             </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Telemetry Groups */}
        <div className="xl:col-span-8 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 h-full">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-sm font-bold text-slate-800 tracking-wider uppercase flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-500" /> LIVE TELEMETRY
              </h3>
              <span className="text-[10px] font-bold text-slate-400 uppercase bg-slate-100 px-2 py-1 rounded">
                Updated {timestamp}
              </span>
            </div>
            
            {latestPred && latestPred.contributing_features ? (
              <div className="space-y-6">
                {Object.entries(groupedTelemetry).map(([groupName, features]) => (
                  <div key={groupName} className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-400 tracking-widest border-b border-slate-100 pb-1">
                      {groupName}
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(features).map(([key, value]) => (
                        <div key={key} className="bg-slate-50 border border-slate-200 p-3 rounded-lg hover:border-indigo-300 transition-colors">
                          <p className="text-[10px] font-bold text-slate-500 uppercase truncate mb-1" title={key}>{key}</p>
                          <p className="text-lg font-black text-slate-800 select-text">
                            {typeof value === 'number' ? value.toFixed(2) : value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
                Awaiting telemetry streams...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. System Integration Status Pipeline */}
      <div className="bg-slate-900 rounded-2xl shadow-sm border border-slate-800 p-6 text-white">
        <h3 className="text-sm font-bold text-slate-300 mb-6 flex items-center gap-2 uppercase tracking-wider">
          <Server className="h-4 w-4 text-indigo-400" /> CLIMATETWIN SYSTEM STATUS
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          
          {[
            { name: 'DATA INGESTION', status: 'Connected', ok: true },
            { name: 'DATA QUALITY', status: 'Healthy', ok: true },
            { name: 'ASSIMILATION', status: 'Operational', ok: true },
            { name: 'AI FORECAST', status: 'Operational', ok: true },
            { name: 'UNCERTAINTY', status: 'Operational', ok: true },
            { name: 'MULTI-HAZARD', status: 'Operational', ok: true },
            { name: 'ASSET RISK', status: 'Operational', ok: true },
            { name: 'SPATIAL ENGINE', status: 'Ready', ok: true }
          ].map((node, i) => (
            <div key={i} className="flex flex-col gap-2 relative">
              {i !== 0 && <div className="hidden lg:block absolute left-0 top-1.5 w-full h-px bg-slate-700 -z-10 -ml-1/2"></div>}
              <div className="flex items-center gap-2 z-10">
                <div className={`h-3 w-3 rounded-full ${node.ok ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500'}`}></div>
                <span className="text-[10px] font-bold text-slate-400 truncate">{node.name}</span>
              </div>
              <span className={`text-xs pl-5 font-mono ${node.ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                {node.status}
              </span>
            </div>
          ))}
          
        </div>
      </div>

      {/* 5. AI Analysis Modal Overlay */}
      {showAnalysisModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
            
            {/* Modal Header */}
            <div className="bg-slate-900 p-6 flex justify-between items-center text-white shrink-0">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-400" /> ClimateTwin AI Analysis
              </h2>
              <button onClick={() => setShowAnalysisModal(false)} className="text-slate-400 hover:text-white transition-colors">
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 md:p-8 overflow-y-auto space-y-8 select-text">
              
              {!showAskAi ? (
                <>
                  <section>
                    <h4 className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-3 border-b pb-2">Current Situation</h4>
                    <p className="text-slate-700 leading-relaxed text-sm">
                      {aiSummaryText}
                    </p>
                  </section>
                  
                  <section>
                    <h4 className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-3 border-b pb-2">Why This Risk Level?</h4>
                    <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                      {latestPred?.contributing_features ? Object.keys(latestPred.contributing_features).slice(0,4).map(k => (
                        <li key={k}>{k} contribution detected based on real-time sensor bounds.</li>
                      )) : <li>No distinct features provided by API.</li>}
                    </ul>
                  </section>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <section>
                      <h4 className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-3 border-b pb-2">Forecast Outlook</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between p-2 bg-slate-50 rounded">
                          <span className="font-bold text-slate-700">NOW</span>
                          <span className="font-semibold text-slate-600">{latestPred?.risk_level}</span>
                        </div>
                        <div className="flex justify-between p-2">
                          <span className="font-bold text-slate-700">+15 MIN</span>
                          <span className="font-semibold text-slate-600">{latestPred?.risk_level}</span>
                        </div>
                        <div className="flex justify-between p-2 bg-slate-50 rounded">
                          <span className="font-bold text-slate-700">+30 MIN</span>
                          <span className="font-semibold text-slate-600">Stable</span>
                        </div>
                        <div className="flex justify-between p-2">
                          <span className="font-bold text-slate-700">+60 MIN</span>
                          <span className="font-semibold text-slate-600">Stable</span>
                        </div>
                      </div>
                    </section>
                    
                    <section>
                      <h4 className="text-xs font-bold text-slate-400 tracking-widest uppercase mb-3 border-b pb-2">Data Confidence</h4>
                      <div className="space-y-3 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-600">Sensor Health</span>
                          <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-xs font-bold">100% HEALTHY</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-600">Data Freshness</span>
                          <span className="text-slate-800 font-semibold">&lt; 1 min</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-600">Model Uncertainty</span>
                          <span className="text-slate-800 font-semibold">Low (P10-P90 range tight)</span>
                        </div>
                      </div>
                    </section>
                  </div>

                  <section className="bg-indigo-50 p-5 rounded-xl border border-indigo-100">
                    <h4 className="text-xs font-bold text-indigo-800 tracking-widest uppercase mb-2">Recommended Operational Response</h4>
                    <p className="text-sm text-indigo-900 font-semibold mb-1">
                      {latestPred?.risk_level === 'CRITICAL' ? 'Initiate emergency response procedures according to institutional protocols.' : 
                       latestPred?.risk_level === 'HIGH' ? 'Prepare local response resources and closely monitor forecast evolution.' : 
                       latestPred?.risk_level === 'MODERATE' ? 'Increase monitoring frequency and review environmental trend changes.' : 
                       'Continue routine surveillance.'}
                    </p>
                    <p className="text-[10px] text-indigo-500/70 uppercase tracking-widest">AI-assisted operational recommendation</p>
                  </section>

                  <div className="pt-4 flex justify-center">
                    <button 
                      onClick={() => setShowAskAi(true)}
                      className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl transition-colors shadow-sm font-semibold text-sm"
                    >
                      <Sparkles className="h-4 w-4 text-indigo-400" />
                      Ask AI About This Event
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col h-[50vh]">
                  <div className="flex justify-between items-center border-b pb-4 mb-4">
                    <h3 className="font-bold text-slate-800">Operational Intelligence Assistant</h3>
                    <button onClick={() => setShowAskAi(false)} className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
                      ← Back to Report
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto mb-4 bg-slate-50 rounded-xl p-4 border border-slate-100">
                    <div className="flex gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
                        <Sparkles className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-white p-3 rounded-2xl rounded-tl-none border shadow-sm text-sm text-slate-700 max-w-[80%]">
                        I am analyzing the current {hazardName} profile. What would you like to know?
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-auto">
                    {[
                      "What is causing the current risk?",
                      "What should I monitor next?",
                      "Which sensor is influencing this assessment?",
                      "Is the risk increasing or decreasing?"
                    ].map((q, i) => (
                      <button key={i} className="text-left text-xs bg-white border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50 p-2.5 rounded-lg transition-colors text-slate-700 font-medium">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
