import React from 'react';
import { 
  X, AlertTriangle, Shield, Clock, Activity, CheckCircle, BrainCircuit,
  ShieldAlert, Database
} from 'lucide-react';

export default function AlertModal({ alert, onClose, onAcknowledge, onResolve }) {
  if (!alert) return null;

  const getSeverityColors = (severity) => {
    switch(severity) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'WARNING': return 'bg-orange-500/20 text-orange-600 border-orange-500/50';
      case 'ADVISORY': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'WATCH': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      default: return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        
        {/* MODAL HEADER */}
        <div className={`p-5 flex justify-between items-center border-b ${alert.severity === 'CRITICAL' ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
          <div className="flex items-center gap-4">
             <div className={`px-3 py-1.5 rounded text-xs font-black tracking-wider uppercase ${getSeverityColors(alert.severity)}`}>
                {alert.severity}
             </div>
             <div>
                <h2 className="text-xl font-black text-slate-900 tracking-tight">{alert.hazard} THREAT ANALYSIS</h2>
                <p className="text-xs text-slate-500 font-mono">ID: {alert.alert_id} • DETECTED: {new Date(alert.timestamp).toLocaleTimeString()}</p>
             </div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-900 transition">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* MODAL BODY */}
        <div className="p-6 overflow-y-auto flex-grow space-y-6">
           
           {/* NOVA AI EXPLANATION */}
           <div className="bg-indigo-950/30 border border-indigo-500/30 rounded-lg p-5 relative overflow-hidden">
             <div className="absolute top-0 right-0 p-3 opacity-10">
               <BrainCircuit className="w-24 h-24 text-indigo-600" />
             </div>
             <h3 className="text-xs font-bold text-indigo-600 uppercase tracking-widest mb-2 flex items-center gap-2">
               <BrainCircuit className="w-4 h-4" /> NOVA ALERT INTELLIGENCE SUMMARY
             </h3>
             <p className="text-sm text-slate-600 leading-relaxed relative z-10 font-medium">
               {alert.explanation}
             </p>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             
             {/* LEFT COLUMN: TRIGGER & EVIDENCE */}
             <div className="space-y-6">
                <div>
                   <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">TRIGGER CONDITION</h3>
                   <div className="bg-slate-50 rounded p-3 text-sm text-slate-700 border border-slate-200 font-medium">
                      <AlertTriangle className="w-4 h-4 text-orange-500 inline mr-2" />
                      {alert.trigger}
                   </div>
                </div>

                <div>
                   <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">SCIENTIFIC EVIDENCE</h3>
                   <div className="space-y-3">
                     {alert.evidence && Object.entries(alert.evidence).map(([category, items]) => (
                        <div key={category} className="bg-slate-50 rounded p-3 border border-slate-200">
                           <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">{category}</p>
                           <ul className="space-y-1">
                             {Object.entries(items).map(([k, v]) => (
                                <li key={k} className="text-xs text-slate-600 flex justify-between">
                                  <span>{k}</span>
                                  <span className="font-mono text-indigo-300">{typeof v === 'number' ? v.toFixed(2) : v}</span>
                                </li>
                             ))}
                           </ul>
                        </div>
                     ))}
                   </div>
                </div>
             </div>

             {/* RIGHT COLUMN: FORECAST, ASSETS, TRUST */}
             <div className="space-y-6">
                <div>
                   <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">FORECAST & LEAD TIME</h3>
                   <div className="grid grid-cols-2 gap-3">
                      <div className="bg-slate-50 rounded p-3 border border-slate-200">
                         <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">WARNING TIME</p>
                         <p className="text-sm font-black text-orange-600">{alert.lead_time}</p>
                      </div>
                      <div className="bg-slate-50 rounded p-3 border border-slate-200">
                         <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">RISK SCORE</p>
                         <p className="text-sm font-black text-rose-600">{alert.score.toFixed(2)}</p>
                      </div>
                   </div>
                </div>

                <div>
                   <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">PRIORITY AFFECTED ASSETS</h3>
                   <div className="space-y-2">
                      {alert.affected_assets && alert.affected_assets.length > 0 ? (
                         alert.affected_assets.map((asset, idx) => (
                            <div key={idx} className="bg-slate-50 border-l-2 border-rose-500 rounded p-3 flex justify-between items-center">
                               <div>
                                  <p className="text-xs font-bold text-slate-800">{asset.name || asset.code}</p>
                                  <p className="text-[10px] text-slate-500">{asset.category || 'Infrastructure'}</p>
                               </div>
                               <div className="text-right">
                                  <p className="text-[10px] text-slate-500 uppercase">Risk Index</p>
                                  <p className="text-xs font-black text-rose-600">{asset.asset_risk_index?.toFixed(2) || 'N/A'}</p>
                               </div>
                            </div>
                         ))
                      ) : (
                         <div className="text-xs text-slate-500 italic">No critical assets identified in immediate threat zone.</div>
                      )}
                   </div>
                </div>

                <div>
                   <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">DATA TRUST & CONFIDENCE</h3>
                   <div className="bg-slate-50 rounded p-3 border border-slate-200 flex items-start gap-3">
                      <Database className="w-5 h-5 text-indigo-600 mt-0.5" />
                      <div>
                         <p className="text-sm font-black text-indigo-300">{alert.confidence} CONFIDENCE</p>
                         <p className="text-[10px] text-slate-500 mt-1">
                            {alert.confidence === 'HIGH' 
                              ? 'Sensor network is fully nominal. Forecast uncertainty is low.' 
                              : 'Alert based on limited observations or elevated forecast uncertainty. Proceed with caution.'}
                         </p>
                      </div>
                   </div>
                </div>
             </div>
           </div>
        </div>

        {/* MODAL FOOTER */}
        <div className="p-5 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
           <button onClick={onAcknowledge} className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-700 border-slate-300 text-xs font-bold rounded transition border border-slate-700">
             ACKNOWLEDGE
           </button>
           <button onClick={onResolve} className="px-4 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-600 border border-emerald-500/50 text-xs font-bold rounded transition">
             MARK RESOLVED
           </button>
        </div>
      </div>
    </div>
  );
}

