import React, { useState, useEffect } from 'react';
import { Shield, Brain, Activity, Clock, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Minus, HelpCircle } from 'lucide-react';

export default function NovaCommandSummary({ apiOnline, selectedHazard = 'FLOOD' }) {
  const [isGenerated, setIsGenerated] = useState(false);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [error, setError] = useState(false);
  const [showAskNova, setShowAskNova] = useState(false);
  const [novaQuestion, setNovaQuestion] = useState(null);
  const [novaAnswer, setNovaAnswer] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(false);
      setErrorMsg('');
      const hazardParam = encodeURIComponent(selectedHazard || 'FLOOD');
      const res = await fetch(`${API_URL}/api/ai/command-summary?hazard=${hazardParam}`);
      if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      setSummary(data);
      setError(false);
    } catch (err) {
      console.error("NOVA AI Fetch Error:", err);
      setError(true);
      setErrorMsg(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isGenerated) return;

    if (apiOnline) {
      fetchSummary();
    } else {
      setError(true);
      setErrorMsg("apiOnline is false (Backend unreachable)");
      setLoading(false);
    }
  }, [apiOnline, API_URL, selectedHazard, isGenerated]);

  if (!isGenerated) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 flex flex-col sm:flex-row justify-between items-center mb-6 shadow-lg">
        <div className="flex items-center gap-4 mb-4 sm:mb-0">
          <div className="bg-indigo-500/10 p-3 rounded-lg border border-indigo-500/20">
            <Brain className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-wide flex items-center gap-2">
              NOVA AI COMMAND SUMMARY
              <span className="text-[9px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded border border-slate-200">STANDBY</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">AI Executive Intelligence Layer is ready for analysis.</p>
          </div>
        </div>
        <button 
          onClick={() => setIsGenerated(true)}
          disabled={!apiOnline}
          className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition shadow-md ${apiOnline ? 'bg-indigo-600 hover:bg-indigo-500 text-slate-900' : 'bg-slate-50 text-slate-500 cursor-not-allowed border border-slate-200'}`}
        >
          <Activity className="h-4 w-4" />
          {apiOnline ? "Generate Live Summary" : "System Offline"}
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 flex justify-center items-center h-48 mb-6 shadow-lg">
        <div className="flex flex-col items-center text-indigo-400 space-y-3">
          <Brain className="h-8 w-8 animate-pulse" />
          <span className="text-sm tracking-widest font-bold">INITIALIZING NOVA AI INTELLIGENCE...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-6 flex flex-col mb-6 shadow-lg">
        <div className="flex justify-between items-center">
            <div className="flex items-center gap-3 text-rose-400">
            <AlertTriangle className="h-6 w-6" />
            <span className="font-bold tracking-wide">NOVA INTELLIGENCE TEMPORARILY UNAVAILABLE</span>
            </div>
            <div className="flex gap-4 items-center">
              <button onClick={fetchSummary} className="px-3 py-1 bg-slate-50 hover:bg-slate-700 text-xs text-slate-700 rounded border border-slate-600 transition">
                Retry Connection
              </button>
              <div className="text-xs text-slate-500">Displaying raw verified system metrics below.</div>
            </div>
        </div>
        <div className="text-[10px] text-rose-500/70 mt-2 font-mono break-all">
            DEBUG: {errorMsg}
        </div>
      </div>
    );
  }

  const {
    priority_threat,
    current_situation,
    why_now,
    what_changed,
    next_60_minutes,
    highest_priority_asset,
    data_trust,
    confidence,
    recommended_action,
    causal_chain
  } = summary;

  const getRiskColor = (level) => {
    switch(level) {
      case 'LOW': return 'text-emerald-400';
      case 'MODERATE': return 'text-amber-400';
      case 'HIGH': return 'text-orange-400';
      case 'CRITICAL': return 'text-rose-500';
      default: return 'text-slate-500';
    }
  };

  const predefinedQuestions = [
    "What is the biggest current threat?",
    "Why is the risk increasing?",
    "What changed recently?",
    "Which asset needs attention?",
    "How confident is the prediction?",
    "What should emergency teams prioritize?",
    "What happens in the next hour?",
    "Are the sensors trustworthy?"
  ];

  const handleAskNova = (q) => {
    setNovaQuestion(q);
    // Simple mapped answers based on summary payload for operational conciseness
    if (q.includes("threat")) setNovaAnswer(`The priority threat is ${priority_threat.type} (Level: ${priority_threat.level}).`);
    else if (q.includes("increasing")) setNovaAnswer(why_now.join(' '));
    else if (q.includes("changed")) setNovaAnswer(what_changed.join(' '));
    else if (q.includes("asset")) setNovaAnswer(`Prioritize ${highest_priority_asset['Asset Name']} (${highest_priority_asset['Risk Level']} Risk).`);
    else if (q.includes("confident")) setNovaAnswer(`Confidence is ${confidence.level} because ${confidence.explanation}`);
    else if (q.includes("teams prioritize")) setNovaAnswer(recommended_action);
    else if (q.includes("next hour")) setNovaAnswer(`Next 60 min outlook: ${next_60_minutes.map(n => `${n.horizon}: ${n.risk}`).join(' | ')}`);
    else if (q.includes("sensors")) setNovaAnswer(`Data Trust is ${data_trust.status} (${(data_trust.score*100).toFixed(0)}%). ${data_trust.explanation}`);
    else setNovaAnswer(current_situation);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6 shadow-xl relative overflow-hidden select-none">
      {/* Background Decorator */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full pointer-events-none"></div>

      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-lg font-black tracking-widest text-slate-900 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-400" /> NOVA AI COMMAND SUMMARY
            <span className="bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded text-[10px] ml-2 font-bold animate-pulse">● LIVE AI</span>
          </h2>
          <p className="text-slate-500 text-xs mt-1">Executive intelligence layer — {new Date(summary.timestamp).toLocaleTimeString()}</p>
        </div>
        
        <div className="flex gap-4">
          <div className="text-right">
            <div className="text-[10px] text-slate-500 font-bold tracking-widest uppercase">AI Confidence</div>
            <div className={`font-black ${getRiskColor(confidence.level)} flex justify-end items-center gap-1`}>
              {confidence.level === 'HIGH' && <CheckCircle2 className="h-3 w-3" />}
              {confidence.level}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-slate-500 font-bold tracking-widest uppercase">Data Trust</div>
            <div className={`font-black ${getRiskColor(data_trust.score > 0.8 ? 'LOW' : 'HIGH')} flex justify-end items-center gap-1`}>
              {(data_trust.score * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        
        {/* Col 1: Current State & Why */}
        <div className="space-y-4">
          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-rose-400 font-bold tracking-widest uppercase mb-1">TOP PRIORITY THREAT</h3>
            <div className="text-xl font-black text-slate-900 mb-2">{priority_threat.type.replace('_', ' ')}</div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Level: <span className={`font-bold ${getRiskColor(priority_threat.level)}`}>{priority_threat.level}</span></span>
              <span className="text-slate-500">Score: <span className="font-bold text-slate-900">{priority_threat.score}</span></span>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-200/50">
              <p className="text-xs text-amber-200/90 font-semibold leading-relaxed">
                <span className="text-slate-500 uppercase text-[9px] block mb-0.5">Action</span>
                {priority_threat.recommended_action}
              </p>
            </div>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase mb-2">WHY NOW?</h3>
            <ul className="space-y-1">
              {why_now.map((reason, i) => (
                <li key={i} className="text-xs text-slate-700 flex items-start gap-1.5">
                  <span className="text-indigo-500 mt-0.5">•</span> {reason}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Col 2: Changes & Next 60 Mins */}
        <div className="space-y-4">
          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase mb-2">WHAT CHANGED?</h3>
            <ul className="space-y-1">
              {what_changed.map((change, i) => (
                <li key={i} className="text-xs text-slate-700 flex items-start gap-1.5">
                  <span className="text-slate-500 mt-0.5">→</span> {change}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase mb-2">NEXT 60 MINUTES</h3>
            <div className="space-y-2">
              {next_60_minutes.map((fc, i) => (
                <div key={i} className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-500 w-16">{fc.horizon}</span>
                  <span className={`font-bold ${getRiskColor(fc.risk)}`}>{fc.risk}</span>
                  <span className="text-slate-500 w-16 text-right">{fc.trend}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Col 3: Causal Chain & Asset Priority */}
        <div className="space-y-4">
          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-emerald-400 font-bold tracking-widest uppercase mb-2">HIGHEST PRIORITY ASSET</h3>
            <div className="text-sm font-bold text-slate-900 truncate" title={highest_priority_asset['Asset Name']}>
              {highest_priority_asset['Asset Name'] || 'No assets critically exposed'}
            </div>
            <div className="text-xs mt-1 text-slate-500">
              Risk Index: <span className="font-bold text-slate-900">{highest_priority_asset['Asset Risk Index']?.toFixed(2) || 'N/A'}</span> 
              <span className="mx-2">•</span> 
              <span className={getRiskColor(highest_priority_asset['Risk Level'])}>{highest_priority_asset['Risk Level'] || 'SAFE'}</span>
            </div>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg flex-1">
            <div className="flex justify-between items-center mb-2">
               <h3 className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase">CAUSAL CHAIN</h3>
               <span className="text-[8px] bg-slate-700 px-1.5 rounded text-slate-700">AI GENERATED</span>
            </div>
            <div className="text-xs text-slate-700 space-y-1 relative pl-3 border-l border-slate-200 ml-1">
              {causal_chain.map((link, i) => (
                <div key={i} className="relative">
                  <span className="absolute -left-4 top-1.5 h-1.5 w-1.5 rounded-full bg-indigo-500"></span>
                  {link}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Ask NOVA Button */}
      <div className="mt-6 border-t border-slate-200/50 pt-4 flex justify-between items-center relative z-10">
        <div className="text-[10px] text-slate-500 flex gap-4 font-semibold">
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> OBSERVED: Sensors</span>
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span> MODEL PREDICTED: Engine</span>
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-indigo-500"></span> AI GENERATED: Nova</span>
        </div>
        <button 
          onClick={() => setShowAskNova(!showAskNova)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-slate-900 text-xs font-bold py-2 px-4 rounded transition shadow-lg"
        >
          <HelpCircle className="h-4 w-4" /> {showAskNova ? 'CLOSE NOVA' : 'ASK NOVA'}
        </button>
      </div>

      {/* Ask NOVA Panel */}
      {showAskNova && (
        <div className="mt-4 bg-slate-50 rounded-lg border border-indigo-500/30 p-4 animate-in fade-in slide-in-from-top-2 relative z-10">
          <div className="flex gap-4">
            <div className="w-1/2 border-r border-slate-200 pr-4">
              <h4 className="text-[10px] text-indigo-300 font-bold tracking-widest uppercase mb-3">Quick Queries</h4>
              <div className="grid grid-cols-1 gap-2">
                {predefinedQuestions.map((q, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleAskNova(q)}
                    className="text-left text-xs bg-white/50 border border-slate-200 hover:border-indigo-400 hover:bg-indigo-900/30 text-slate-700 py-1.5 px-3 rounded transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
            <div className="w-1/2 pl-2">
              <h4 className="text-[10px] text-emerald-400 font-bold tracking-widest uppercase mb-3">NOVA RESPONSE</h4>
              {novaQuestion ? (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 italic">"{novaQuestion}"</div>
                  <div className="text-sm text-slate-900 leading-relaxed border-l-2 border-indigo-500 pl-3">
                    {novaAnswer}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 h-full flex items-center justify-center italic">
                  Select a question to get an AI-generated explanation.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

