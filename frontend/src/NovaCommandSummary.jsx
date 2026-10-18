import React, { useState, useEffect } from 'react';
import { Brain, Activity, AlertTriangle, CheckCircle2, HelpCircle, ClipboardCheck, RefreshCw, ShieldCheck, UserCheck, Send } from 'lucide-react';

export default function NovaCommandSummary({ apiOnline, selectedHazard = 'FLOOD' }) {
  const [isGenerated, setIsGenerated] = useState(false);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [error, setError] = useState(false);
  const [showAskNova, setShowAskNova] = useState(false);
  const [novaQuestion, setNovaQuestion] = useState(null);
  const [novaAnswer, setNovaAnswer] = useState(null);
  const [novaMode, setNovaMode] = useState('');
  const [customQuestion, setCustomQuestion] = useState('');
  const [copilotLoading, setCopilotLoading] = useState(false);

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
    causal_chain,
    decision_brief,
    method_note
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
    "What should the team do now?",
    "Why is this the current priority?",
    "What would trigger escalation?",
    "How reliable is this briefing?",
  ];

  const handleAskNova = async (q) => {
    setNovaQuestion(q);
    setCopilotLoading(true);
    setNovaAnswer(null);
    try {
      const response = await fetch(`${API_URL}/api/ai/copilot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, hazard: selectedHazard || 'FLOOD' })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'NOVA could not answer this question.');
      setNovaAnswer(data.answer);
      setNovaMode(data.mode);
    } catch (err) {
      setNovaAnswer(`${decision_brief?.evidence_boundary || method_note} Please refresh the briefing and try again.`);
      setNovaMode('LOCAL_INTERFACE_FALLBACK');
    } finally {
      setCopilotLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 mb-6 shadow-lg relative overflow-hidden">
      {/* Background Decorator */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full pointer-events-none"></div>

      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-lg font-black tracking-wide text-slate-900 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" /> NOVA OPERATIONS BRIEF
            <span className="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded text-[10px] ml-2 font-bold">LIVE DECISION SUPPORT</span>
          </h2>
          <p className="text-slate-500 text-xs mt-1">A transparent summary of current telemetry and prototype model outputs — {new Date(summary.timestamp).toLocaleTimeString()}</p>
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

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 relative z-10">
        
        {/* Col 1: Current State & Why */}
        <div className="space-y-4">
          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-rose-600 font-bold tracking-widest uppercase mb-1">Current priority</h3>
            <div className="text-xl font-black text-slate-900 mb-2">{priority_threat.type.replace('_', ' ')}</div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">Level: <span className={`font-bold ${getRiskColor(priority_threat.level)}`}>{priority_threat.level}</span></span>
              <span className="text-slate-500">Score: <span className="font-bold text-slate-900">{priority_threat.score}</span></span>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-200/50">
              <p className="text-xs text-slate-700 font-semibold leading-relaxed">
                <span className="text-slate-500 uppercase text-[9px] block mb-0.5">Current assessment</span>
                {current_situation}
              </p>
            </div>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-indigo-600 font-bold tracking-widest uppercase mb-2">Evidence used</h3>
            <ul className="space-y-1">
              {why_now.map((reason, i) => (
                <li key={i} className="text-xs text-slate-700 flex items-start gap-1.5">
                  <span className="text-indigo-500 mt-0.5">•</span> {reason}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Col 2: action and review */}
        <div className="space-y-4">
          <div className="bg-indigo-50 border border-indigo-100 p-4 rounded-lg">
            <div className="flex items-center justify-between gap-3 mb-2">
              <h3 className="text-[10px] text-indigo-700 font-bold tracking-widest uppercase">Recommended next step</h3>
              <span className="text-[10px] font-bold rounded-full px-2 py-1 bg-white text-indigo-700 border border-indigo-100">{decision_brief?.operating_mode || 'NORMAL'}</span>
            </div>
            <p className="text-sm text-slate-800 font-semibold leading-relaxed">{decision_brief?.action || recommended_action}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div><span className="block text-slate-500 text-[10px] uppercase tracking-wide">Owner</span><span className="font-semibold text-slate-800">{decision_brief?.owner || 'Duty analyst'}</span></div>
              <div><span className="block text-slate-500 text-[10px] uppercase tracking-wide">Review</span><span className="font-semibold text-slate-800">in {decision_brief?.review_in_minutes || 60} minutes</span></div>
            </div>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-indigo-600 font-bold tracking-widest uppercase mb-2">Review plan</h3>
            <div className="space-y-2">
              {next_60_minutes.map((fc, i) => (
                <div key={i} className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-500 w-16">{fc.horizon}</span>
                  <span className={`font-bold ${fc.risk === 'REVIEW' ? 'text-indigo-700' : getRiskColor(fc.risk)}`}>{fc.risk}</span>
                  <span className="text-slate-500 w-32 text-right">{fc.trend}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Col 3: Causal Chain & Asset Priority */}
        <div className="space-y-4">
          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg">
            <h3 className="text-[10px] text-emerald-700 font-bold tracking-widest uppercase mb-2">Screening-priority asset</h3>
            <div className="text-sm font-bold text-slate-900 truncate" title={highest_priority_asset['Asset Name']}>
              {highest_priority_asset['Asset Name'] || 'No assets critically exposed'}
            </div>
            <div className="text-xs mt-1 text-slate-500">
              Risk Index: <span className="font-bold text-slate-900">{highest_priority_asset['Asset Risk Index']?.toFixed(2) || 'N/A'}</span> 
              <span className="mx-2">•</span> 
              <span className={getRiskColor(highest_priority_asset['Risk Level'])}>{highest_priority_asset['Risk Level'] || 'SAFE'}</span>
            </div>
            <p className="mt-2 text-[10px] text-slate-500">Prioritisation is model-derived and needs field verification before deployment.</p>
          </div>

          <div className="bg-slate-50/50 border border-slate-200 p-4 rounded-lg flex-1">
            <div className="flex justify-between items-center mb-2">
               <h3 className="text-[10px] text-indigo-600 font-bold tracking-widest uppercase">How this result was derived</h3>
               <span className="text-[8px] bg-slate-200 px-1.5 py-0.5 rounded text-slate-600">TRACEABLE</span>
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

      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 flex gap-3 relative z-10">
        <ShieldCheck className="h-4 w-4 text-amber-700 mt-0.5 shrink-0" />
        <div><p className="text-xs font-bold text-amber-900">Decision boundary</p><p className="text-xs text-amber-800 mt-0.5">{decision_brief?.evidence_boundary || method_note}</p></div>
      </div>

      {/* Ask NOVA Button */}
      <div className="mt-6 border-t border-slate-200/50 pt-4 flex justify-between items-center relative z-10">
        <div className="text-[10px] text-slate-500 flex gap-4 font-semibold">
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> OBSERVED: Sensors</span>
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span> MODEL PREDICTED: Engine</span>
           <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-indigo-500"></span> SYNTHESISED: Nova</span>
        </div>
        <button 
          onClick={() => setShowAskNova(!showAskNova)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2 px-4 rounded transition shadow-lg"
        >
          <HelpCircle className="h-4 w-4" /> {showAskNova ? 'CLOSE NOVA' : 'ASK NOVA'}
        </button>
      </div>

      {/* Ask NOVA Panel */}
      {showAskNova && (
        <div className="mt-4 bg-slate-50 rounded-lg border border-indigo-500/30 p-4 animate-in fade-in slide-in-from-top-2 relative z-10">
          <div className="flex gap-4">
            <div className="w-1/2 border-r border-slate-200 pr-4">
              <h4 className="text-[10px] text-indigo-700 font-bold tracking-widest uppercase mb-3">Useful questions</h4>
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
              <h4 className="text-[10px] text-emerald-700 font-bold tracking-widest uppercase mb-3">NOVA RESPONSE</h4>
              {novaQuestion ? (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 italic">"{novaQuestion}"</div>
                  <div className="text-sm text-slate-900 leading-relaxed border-l-2 border-indigo-500 pl-3">
                    {copilotLoading ? 'Reviewing the current evidence…' : novaAnswer}
                  </div>
                  {!copilotLoading && novaMode && <p className="text-[10px] font-bold text-slate-500 uppercase">Mode: {novaMode.replaceAll('_', ' ')}</p>}
                </div>
              ) : (
                <div className="text-xs text-slate-500 h-full flex items-center justify-center italic">
                  Select a question to get an AI-generated explanation.
                </div>
              )}
            </div>
          </div>
          <form onSubmit={(event) => { event.preventDefault(); if (customQuestion.trim()) handleAskNova(customQuestion.trim()); }} className="mt-4 border-t border-slate-200 pt-3 flex gap-2">
            <label className="sr-only" htmlFor="nova-custom-question">Ask NOVA a question</label>
            <input id="nova-custom-question" value={customQuestion} onChange={(event) => setCustomQuestion(event.target.value)} maxLength={1000} className="min-w-0 flex-1 rounded border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200" placeholder="Ask about the current evidence, action, or uncertainty…" />
            <button type="submit" disabled={!customQuestion.trim() || copilotLoading} className="inline-flex items-center gap-1 rounded bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"><Send className="h-3.5 w-3.5"/>Ask</button>
          </form>
          <p className="mt-2 text-[10px] text-slate-500">NOVA uses an evidence-grounded local fallback until an optional backend-only AI key is configured.</p>
        </div>
      )}
    </div>
  );
}

