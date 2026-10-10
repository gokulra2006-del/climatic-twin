import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, Shield, Clock, TrendingUp, Activity, CheckCircle, Search, Terminal,
  Radio, ChevronDown, CheckCircle2, ChevronRight, X
} from 'lucide-react';
import AlertModal from './AlertModal';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function EarlyWarningCenter() {
  const [alerts, setAlerts] = useState({ active: [], history: [] });
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState('');
  
  const fetchAlerts = async () => {
    try {
      // Ask backend to evaluate first to ensure freshness
      await fetch(`${API_URL}/api/alerts/evaluate`, { method: 'POST' });
      
      const res = await fetch(`${API_URL}/api/alerts/`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.error("Failed to fetch alerts", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const iv = setInterval(fetchAlerts, 15000); // 15 sec polling
    return () => clearInterval(iv);
  }, []);

  const handleSimulate = async (scenario) => {
    setIsSimulating(true);
    setSimulationStatus(`Starting ${scenario}...`);
    try {
      const res = await fetch(`${API_URL}/api/alerts/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario })
      });
      if (res.ok) {
        const data = await res.json();
        setSimulationStatus(data.status);
        await fetchAlerts();
      }
    } catch(e) {
      console.error(e);
      setSimulationStatus('Simulation failed');
    } finally {
      setIsSimulating(false);
    }
  };

  const getSeverityColors = (severity) => {
    switch(severity) {
      case 'CRITICAL': return 'bg-red-600 text-white border-red-700 shadow-sm';
      case 'WARNING': return 'bg-orange-500 text-white border-orange-600 shadow-sm';
      case 'ADVISORY': return 'bg-amber-400 text-amber-900 border-amber-500 shadow-sm';
      case 'WATCH': return 'bg-yellow-400 text-yellow-900 border-yellow-500 shadow-sm';
      default: return 'bg-blue-500 text-white border-blue-600 shadow-sm';
    }
  };

  const activeAlertList = alerts.active || [];
  const hasCritical = activeAlertList.some(a => a.severity === 'CRITICAL');

  return (
    <div className="space-y-6 font-sans">
      
      {/* HEADER ROW */}
      <div className={`flex flex-col md:flex-row justify-between items-start md:items-center gap-4 p-5 rounded-xl border shadow-2xl overflow-hidden relative ${hasCritical ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
        <div className="absolute top-0 right-0 p-3 opacity-10">
           <Radio className={`w-32 h-32 ${hasCritical ? 'animate-ping text-red-500' : 'text-slate-500'}`} />
        </div>
        <div className="z-10">
          <h1 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-3">
             <Shield className={`w-7 h-7 ${hasCritical ? 'text-red-500' : 'text-indigo-600'}`} />
             EARLY WARNING CENTER
          </h1>
          <p className="text-xs text-slate-500 flex items-center gap-2 mt-2 font-mono">
            <span className={`w-2 h-2 rounded-full ${hasCritical ? 'bg-red-500' : 'bg-emerald-500'} animate-pulse`}></span>
            SYSTEM STATUS: {hasCritical ? 'EMERGENCY OPERATIONS ACTIVE' : 'NOMINAL MONITORING'}
          </p>
        </div>
        <div className="z-10 flex gap-2">
           <button 
             onClick={() => handleSimulate('RESET')}
             className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded border border-slate-300 transition"
           >
             RETURN TO LIVE DATA
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* ACTIVE ALERTS COLUMN */}
        <div className="lg:col-span-2 space-y-4">
           <h2 className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 border-b border-slate-200 pb-2">
             <AlertTriangle className="w-4 h-4 text-orange-500" /> ACTIVE THREATS ({activeAlertList.length})
           </h2>
           
           {loading ? (
              <div className="p-10 flex justify-center"><Terminal className="w-6 h-6 text-slate-500 animate-pulse" /></div>
           ) : activeAlertList.length === 0 ? (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-10 flex flex-col items-center justify-center text-center">
                 <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-3 opacity-50" />
                 <h3 className="text-slate-700 font-bold mb-1">No Active Alerts</h3>
                 <p className="text-slate-500 text-sm">All environmental parameters are within safe operational thresholds.</p>
              </div>
           ) : (
             <div className="space-y-4">
               {activeAlertList.map(alert => (
  <div key={alert.alert_id} className={`bg-white rounded-xl shadow-sm border transition-all duration-200 hover:shadow-md cursor-pointer ${alert.severity === 'CRITICAL' ? 'border-red-200 border-l-4 border-l-red-500' : 'border-slate-200 border-l-4 border-l-orange-400'}`} onClick={() => setSelectedAlert(alert)}>
    <div className="p-5 flex flex-col md:flex-row gap-5 items-start">
      {/* SEVERITY BADGE */}
      <div className="flex-shrink-0 flex flex-col items-center justify-center w-28 md:border-r border-slate-100 md:pr-5">
        <div className={`px-3 py-1.5 rounded-md text-[11px] font-black tracking-wider uppercase w-full text-center border ${getSeverityColors(alert.severity)}`}>
          {alert.severity}
        </div>
        <div className="text-[10px] font-mono text-slate-400 mt-3 text-center bg-slate-50 px-2 py-1 rounded w-full">
          ID: {alert.alert_id.substring(0,8)}
        </div>
      </div>
      
      {/* MAIN CONTENT */}
      <div className="flex-grow w-full">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-sm md:text-base font-bold text-slate-800 uppercase tracking-wide">
            {alert.hazard.replace('_', ' ')} COMPOUND THREAT
          </h3>
          <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100">{new Date(alert.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
        </div>
        
        <p className="text-sm text-slate-600 font-medium mb-4">{alert.trigger}</p>
        
        <div className="flex flex-wrap gap-3">
          <div className="bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg min-w-[110px]">
            <p className="text-[9px] uppercase text-slate-500 font-bold mb-1">LEAD TIME</p>
            <p className="text-xs font-mono font-bold text-slate-800">{alert.lead_time}</p>
          </div>
          <div className="bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg min-w-[110px]">
            <p className="text-[9px] uppercase text-slate-500 font-bold mb-1">CONFIDENCE</p>
            <p className="text-xs font-mono font-bold text-slate-800">{alert.confidence}</p>
          </div>
          <div className="bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg flex-grow">
            <p className="text-[9px] uppercase text-slate-500 font-bold mb-1">PRIORITY ASSET</p>
            <p className="text-xs font-mono font-bold text-slate-800 truncate">
              {alert.affected_assets?.length > 0 ? alert.affected_assets[0].name || alert.affected_assets[0].code : 'None'}
            </p>
          </div>
        </div>
      </div>
      
      {/* ACTION */}
      <div className="hidden md:flex items-center justify-center self-stretch pl-2">
        <ChevronRight className="w-5 h-5 text-slate-400 hover:text-indigo-500 transition-colors" />
      </div>
    </div>
  </div>
))}
             </div>
           )}
        </div>

        {/* SIMULATION & HISTORY COLUMN */}
        <div className="space-y-6">
           <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-lg">
             <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 border-b border-slate-200 pb-2 mb-4">
               <Activity className="w-4 h-4 text-indigo-600" /> SIMULATE EMERGENCY
             </h2>
             <p className="text-[10px] text-slate-500 mb-4 uppercase tracking-wide">For demonstration and drills only.</p>
             
             <div className="space-y-2">
               <button onClick={() => handleSimulate('SCENARIO_B_HEAVY_RAIN')} className="w-full text-left px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium transition flex justify-between">
                 <span>Scenario B: Heavy Rain</span> <TrendingUp className="w-4 h-4 text-orange-600" />
               </button>
               <button onClick={() => handleSimulate('SCENARIO_C_RAIN_PLUS_FULL_RESERVOIR')} className="w-full text-left px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium transition flex justify-between">
                 <span>Scenario C: Rain + Full Reservoir</span> <TrendingUp className="w-4 h-4 text-red-600" />
               </button>
               <button onClick={() => handleSimulate('SCENARIO_D_EXTREME_CYCLONIC_DELUGE')} className="w-full text-left px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-medium transition flex justify-between">
                 <span>Scenario D: Cyclonic Deluge</span> <AlertTriangle className="w-4 h-4 text-red-500" />
               </button>
             </div>
             
             {simulationStatus && (
               <div className="mt-4 p-2 bg-indigo-50 border border-indigo-200 rounded text-[10px] text-indigo-700 font-mono text-center">
                 {simulationStatus}
               </div>
             )}
           </div>

           <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-lg max-h-96 overflow-y-auto">
             <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 border-b border-slate-200 pb-2 mb-4">
               <Clock className="w-4 h-4 text-slate-500" /> EVENT HISTORY
             </h2>
             {alerts.history && alerts.history.length > 0 ? (
                <div className="space-y-3">
                   {alerts.history.slice(0, 10).map((h, i) => (
                      <div key={i} className="text-xs border-l-2 border-slate-600 pl-3 py-1">
                         <span className="text-[10px] text-slate-500 font-mono block">{new Date(h.timestamp).toLocaleString()}</span>
                         <span className="text-slate-700 font-medium">
                            [{h.severity}] {h.hazard} {h.status === 'RESOLVED' ? 'resolved' : 'escalation'}
                         </span>
                      </div>
                   ))}
                </div>
             ) : (
                <p className="text-xs text-slate-500 text-center">No recent history</p>
             )}
           </div>
        </div>
      </div>
      
      {/* MODAL */}
      {selectedAlert && (
         <AlertModal 
            alert={selectedAlert} 
            onClose={() => setSelectedAlert(null)} 
            onAcknowledge={async () => {
               await fetch(`${API_URL}/api/alerts/${selectedAlert.alert_id}/acknowledge`, { method: 'POST' });
               setSelectedAlert(null);
               fetchAlerts();
            }}
            onResolve={async () => {
               await fetch(`${API_URL}/api/alerts/${selectedAlert.alert_id}/resolve`, { method: 'POST' });
               setSelectedAlert(null);
               fetchAlerts();
            }}
         />
      )}
    </div>
  );
}





