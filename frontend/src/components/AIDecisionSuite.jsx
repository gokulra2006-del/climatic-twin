import React, { useState, useEffect } from 'react';
import {
  BrainCircuit, ShieldAlert, FileText, Sliders, Volume2, CheckCircle2,
  AlertTriangle, RefreshCw, Sparkles, Send, Download, BarChart2,
  Clock, ArrowRight, Layers, ShieldCheck, Database, Info, Loader2,
  ChevronRight, Activity, Zap, ThumbsUp, CheckSquare, MessageSquare,
  Building, Radio, Globe, History, TrendingUp, AlertOctagon, PhoneCall,
  UserCheck, Shield, Users
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function AIDecisionSuite({ selectedHazard = 'FLOOD' }) {
  const [activeTab, setActiveTab] = useState('response_plan');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Threat level for response plan and alerts
  const [threatLevel, setThreatLevel] = useState('WATCH');

  // Loaded Data States
  const [responsePlan, setResponsePlan] = useState(null);
  const [sitRep, setSitRep] = useState(null);
  const [riskNarrative, setRiskNarrative] = useState(null);
  const [actions, setActions] = useState([]);
  const [guardian, setGuardian] = useState(null);
  const [historicalEvents, setHistoricalEvents] = useState([]);
  const [postEventData, setPostEventData] = useState(null);
  const [smartAlerts, setSmartAlerts] = useState(null);
  const [providerStatus, setProviderStatus] = useState(null);
  const [lastSyncedAt, setLastSyncedAt] = useState(null);

  // Counterfactual Simulator State
  const [rainfallDelta, setRainfallDelta] = useState(25);
  const [pumpFailure, setPumpFailure] = useState(false);
  const [reservoirBuffer, setReservoirBuffer] = useState(15);
  const [counterfactualResult, setCounterfactualResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Grounded Assistant Chat State
  const [chatMessage, setChatMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'assistant',
      text: 'Vanakkam! I am NOVA. Ask a focused operational question and I will answer from the currently loaded ClimateTwin briefing. I will identify unavailable or unverified inputs instead of filling gaps with estimates.',
      citations: ['NOVA evidence boundary'],
      badge: 'DECISION SUPPORT',
      data_nature: 'ANALYSIS',
      source: 'ClimateTwin Knowledge Base',
      timestamp: new Date().toISOString()
    }
  ]);

  // Alert sign-off state
  const [alertDispatched, setAlertDispatched] = useState(false);

  // Load all data on mount and on refresh
  const loadAllData = async (level = threatLevel) => {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([
        fetchResponsePlan(level),
        fetchSitRep(),
        fetchRiskNarrative(),
        fetchActions(),
        fetchGuardian(),
        fetchHistorical(),
        fetchPostEvent(),
        fetchSmartAlerts(level),
        fetchProviderStatus()
      ]);
      setLastSyncedAt(new Date().toISOString());
    } catch (err) {
      console.error('Error loading AI suite data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProviderStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/provider-status`);
      if (res.ok) setProviderStatus(await res.json());
    } catch (e) {
      console.warn('Failed to load NOVA provider status', e);
    }
  };

  useEffect(() => {
    loadAllData(threatLevel);
  }, []);

  const fetchResponsePlan = async (level) => {
    try {
      const res = await fetch(`${API_URL}/api/ai/response-plan?hazard=${selectedHazard}&threat_level=${level}`);
      if (res.ok) {
        const data = await res.json();
        setResponsePlan(data);
      }
    } catch (e) {
      console.warn('Failed to load response plan', e);
    }
  };

  const fetchSitRep = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/situation-report`);
      if (res.ok) setSitRep(await res.json());
    } catch (e) {
      console.warn('Failed to load SitRep', e);
    }
  };

  const fetchRiskNarrative = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/risk-narratives`);
      if (res.ok) setRiskNarrative(await res.json());
    } catch (e) {
      console.warn('Failed to load risk narratives', e);
    }
  };

  const fetchActions = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/prioritise-actions`);
      if (res.ok) {
        const data = await res.json();
        setActions(data.ranked_actions || []);
      }
    } catch (e) {
      console.warn('Failed to load actions', e);
    }
  };

  const fetchGuardian = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/data-quality-guardian`);
      if (res.ok) setGuardian(await res.json());
    } catch (e) {
      console.warn('Failed to load guardian', e);
    }
  };

  const fetchHistorical = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/historical-comparator`);
      if (res.ok) {
        const data = await res.json();
        setHistoricalEvents(data.historical_comparisons || []);
      }
    } catch (e) {
      console.warn('Failed to load historical comparator', e);
    }
  };

  const fetchPostEvent = async () => {
    try {
      const res = await fetch(`${API_URL}/api/ai/post-event-learning`);
      if (res.ok) setPostEventData(await res.json());
    } catch (e) {
      console.warn('Failed to load post-event data', e);
    }
  };

  const fetchSmartAlerts = async (level) => {
    try {
      const res = await fetch(`${API_URL}/api/ai/smart-alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threat_level: level, target_zone: 'Greater Chennai' })
      });
      if (res.ok) setSmartAlerts(await res.json());
    } catch (e) {
      console.warn('Failed to load smart alerts', e);
    }
  };

  const runCounterfactual = async () => {
    setSimulating(true);
    try {
      const res = await fetch(`${API_URL}/api/ai/what-if-counterfactual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rainfall_delta_pct: rainfallDelta,
          pump_station_failure: pumpFailure,
          reservoir_capacity_delta_pct: reservoirBuffer,
          subway_drainage_blocked: false
        })
      });
      if (res.ok) {
        setCounterfactualResult(await res.json());
      }
    } catch (e) {
      console.error('What-if simulation error:', e);
    } finally {
      setSimulating(false);
    }
  };

  const sendAssistantMessage = async (queryText) => {
    const text = queryText || chatMessage;
    if (!text.trim()) return;

    setChatHistory(prev => [...prev, { role: 'user', text }]);
    setChatMessage('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/ai/copilot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, hazard: selectedHazard })
      });
      const data = await res.json();
      if (res.ok) {
        setChatHistory(prev => [
          ...prev,
          {
            role: 'assistant',
            text: data.answer,
            citations: data.citations || ['NOVA evidence boundary'],
            badge: data.badge || 'DECISION SUPPORT',
            intent: data.intent || 'DECISION_SUPPORT',
            data_nature: data.data_nature || 'ANALYSIS',
            source: data.source || 'ClimateTwin Telemetry',
            timestamp: data.timestamp || new Date().toISOString(),
            safety_notice: data.safety_notice,
            forecast_summary: data.forecast_summary
          }
        ]);
      } else {
        throw new Error(data.detail || 'Assistant error');
      }
    } catch (e) {
      setChatHistory(prev => [
        ...prev,
        {
          role: 'assistant',
          text: 'NOVA could not retrieve a verified answer. Refresh the live inputs and try again; no fallback measurement has been shown.',
          citations: ['Live data connection unavailable'],
          badge: 'ERROR / UNAVAILABLE',
          intent: 'ERROR',
          data_nature: 'SYSTEM_NOTICE',
          source: 'Local Telemetry Gateway',
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const downloadSitRep = () => {
    if (!sitRep) return;
    const dataToExport = sitRep;
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chennai_sitrep_${new Date().toISOString().slice(0, 16)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Command bar */}
      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-700">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-900">NOVA operational workspace</h1>
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-600">10 tools</span>
              </div>
              <p className="mt-1 max-w-2xl text-sm text-slate-600">Use one decision tool at a time: review current inputs, prepare an operator-approved response, and retain the evidence trail.</p>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <span className="flex items-center justify-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              {providerStatus
                ? (providerStatus.configured ? `AI: ${providerStatus.provider || 'CONNECTED'}` : 'LOCAL EVIDENCE MODE')
                : 'CHECKING AI MODE'}
            </span>
            <button
              onClick={() => loadAllData(threatLevel)}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh sources
            </button>
          </div>
        </div>

        <nav aria-label="NOVA decision tools" className="grid grid-cols-2 gap-2 border-t border-slate-100 p-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-10">
          {[
            { id: 'response_plan', label: '1. Response Plan', icon: FileText },
            { id: 'assistant', label: '2. Grounded Assistant', icon: MessageSquare },
            { id: 'sitrep', label: '3. SitRep Digest', icon: Activity },
            { id: 'narratives', label: '4. Explainable Risk', icon: Sparkles },
            { id: 'what_if', label: '5. What-If Simulator', icon: Sliders },
            { id: 'alerts', label: '6. Bilingual Alerts', icon: Volume2 },
            { id: 'prioritisation', label: '7. Action Ranking', icon: CheckSquare },
            { id: 'guardian', label: '8. Data Guardian', icon: ShieldCheck },
            { id: 'historical', label: '9. Event Comparator', icon: History },
            { id: 'learning', label: '10. Post-Event Audit', icon: BarChart2 }
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex min-h-[42px] items-center gap-1.5 rounded-lg px-2.5 py-2 text-left text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
                  active
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-50 text-slate-600 hover:bg-indigo-50 hover:text-indigo-800'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </section>

      <div className="flex flex-col gap-2 rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-slate-700 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-700" />
          <span>
            <strong>Operational boundary:</strong> current API readings inform the workspace; response plans, alert drafts, and what-if results remain operator-reviewed planning support and never dispatch external actions automatically.
          </span>
        </div>
        {lastSyncedAt && <span className="shrink-0 text-xs font-medium text-sky-800">Last checked {new Date(lastSyncedAt).toLocaleTimeString()}</span>}
      </div>

      {/* TAB 1: AI RESPONSE PLAN GENERATOR */}
      {activeTab === 'response_plan' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  AI Automated Response Playbook Generator
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Deterministic action protocols mapping live hazard severity to Chennai municipal responder workflows (GCC, CMWSSB, TANGEDCO).
                </p>
              </div>
              <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200">
                <span className="text-xs font-bold text-slate-600 px-2">Threat Level:</span>
                {['NORMAL', 'WATCH', 'WARNING', 'EMERGENCY'].map(lvl => (
                  <button
                    key={lvl}
                    onClick={() => {
                      setThreatLevel(lvl);
                      fetchResponsePlan(lvl);
                      fetchSmartAlerts(lvl);
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                      threatLevel === lvl
                        ? lvl === 'EMERGENCY'
                          ? 'bg-rose-600 text-white shadow-sm'
                          : lvl === 'WARNING'
                          ? 'bg-amber-500 text-white shadow-sm'
                          : lvl === 'WATCH'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-emerald-600 text-white shadow-sm'
                        : 'text-slate-600 hover:bg-slate-200/70'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="py-16 flex flex-col justify-center items-center text-slate-500 text-sm">
                <Loader2 className="h-6 w-6 animate-spin mb-2 text-indigo-600" />
                Synthesising tactical response plan for {threatLevel}...
              </div>
            ) : responsePlan ? (
              <div className="space-y-6">
                {/* Tactical Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Plan ID & Status</span>
                    <p className="text-base font-bold text-slate-900 mt-1">{responsePlan.plan_id || 'ARP-CHN-2026'}</p>
                    <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                      {responsePlan.threat_level || threatLevel}
                    </span>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Primary Hazard</span>
                    <p className="text-base font-bold text-slate-900 mt-1">{responsePlan.primary_hazard || selectedHazard}</p>
                    <span className="text-xs text-slate-500">Greater Chennai Basin</span>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Lead Authority</span>
                    <p className="text-base font-bold text-indigo-700 mt-1">Greater Chennai Corp (GCC)</p>
                    <span className="text-xs text-slate-500">Incident Commander (1913)</span>
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Escalation Horizon</span>
                    <p className="text-base font-bold text-amber-700 mt-1">
                      {Array.isArray(responsePlan.escalation_timeline) && responsePlan.escalation_timeline.length > 0
                        ? responsePlan.escalation_timeline[responsePlan.escalation_timeline.length - 1].time_offset
                        : 'T+180 min'}
                    </p>
                    <span className="text-xs text-slate-500">Scheduled audit cycle</span>
                  </div>
                </div>

                {/* Immediate Tactical Actions */}
                <div>
                  <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-emerald-600" />
                    Immediate Tactical Actions Required
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {(responsePlan.immediate_actions || [
                      "Maintain routine telemetry polling across 8 IMD AWS and CMWSSB gauges.",
                      "Verify backup diesel generator fuel reserves at GCC zonal headquarters.",
                      "Ensure trash screens along arterial stormwater drains remain clear of solid waste."
                    ]).map((action, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-indigo-300 transition">
                        <span className="h-6 w-6 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-slate-800 leading-relaxed">{action}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">Responsible: GCC / CMWSSB</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Responsible Teams & Priority Locations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Responsible Teams */}
                  <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5 text-blue-600" />
                      Assigned Municipal Response Teams
                    </h4>
                    <div className="space-y-2">
                      {(responsePlan.responsible_teams || [
                        { team: "GCC Control Room (1913 PGR)", lead: "Duty Officer", contact_role: "Public Grievance Monitoring" },
                        { team: "State Disaster Management (TNSDMA)", lead: "Meteorologist on Duty", contact_role: "Radar Tracking" }
                      ]).map((item, i) => (
                        <div key={i} className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg text-xs">
                          <div>
                            <span className="font-bold text-slate-800">{item.team || item.name}</span>
                            <span className="text-[11px] text-slate-500 block">Lead: {item.lead || 'Station Chief'}</span>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {item.contact_role || 'Active'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Priority Locations */}
                  <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <Building className="h-3.5 w-3.5 text-amber-600" />
                      Priority Vulnerable Wards & Corridors
                    </h4>
                    <div className="space-y-2">
                      {(responsePlan.priority_locations || [
                        { name: "Velachery Micro-Basin", zone: "Zone 13 (Adyar)", urgency: "HIGH_VULNERABILITY" },
                        { name: "Vyasarpadi Subway Corridor", zone: "Zone 4 (Tondiarpet)", urgency: "CRITICAL_SUBWAY" }
                      ]).map((loc, i) => (
                        <div key={i} className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg text-xs">
                          <div>
                            <span className="font-bold text-slate-800">
                              {typeof loc === 'object' ? loc.name : loc}
                            </span>
                            <span className="text-[11px] text-slate-500 block">
                              {typeof loc === 'object' ? `Zone: ${loc.zone}` : 'Chennai Low-Lying'}
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                            {typeof loc === 'object' ? loc.urgency : 'ELEVATED'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Escalation Timeline */}
                {Array.isArray(responsePlan.escalation_timeline) && responsePlan.escalation_timeline.length > 0 && (
                  <div className="border border-slate-200 rounded-xl p-4 bg-white">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-indigo-600" />
                      Tactical Escalation Milestones
                    </h4>
                    <div className="flex flex-col sm:flex-row gap-3">
                      {responsePlan.escalation_timeline.map((step, si) => (
                        <div key={si} className="flex-1 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                          <span className="font-mono font-bold text-indigo-700 block">{step.time_offset}</span>
                          <span className="text-slate-700 mt-1 block">{step.milestone}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Human-in-the-Loop Safeguard Notice */}
                <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl flex items-start gap-3">
                  <ShieldCheck className="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-900 leading-relaxed">
                    <strong>Human-in-the-Loop Governance:</strong> {responsePlan.human_in_the_loop_requirement || 'Operational actions are AI-generated decision recommendations. Final dispatch authority rests with the Greater Chennai Corporation Incident Commander.'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-sm text-slate-500">
                Click a threat level above to generate an operational playbook.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: EVIDENCE-GROUNDED NOVA ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-indigo-600" />
                Evidence-Grounded NOVA Natural Language Assistant
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Answers strictly from physical telemetry, SRTM DEM elevation, and calibrated GNN-LSTM predictions. Refuses hallucination.
              </p>
            </div>
            <span className="px-3 py-1 bg-indigo-50 border border-indigo-200 rounded-full text-xs font-bold text-indigo-700">
              STRICT EVIDENCE GROUNDED
            </span>
          </div>

          {/* Quick Prompts */}
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-xs font-bold text-slate-500 py-1">Sample Queries:</span>
            {[
              "What is the weather outside?",
              "Is there a chance of rainfall in my area?",
              "Will it rain in the next 6 hours?",
              "It is sunny here.",
              "Why is flood risk high in Adyar?",
              "What changed since yesterday?"
            ].map((prompt, i) => (
              <button
                key={i}
                onClick={() => sendAssistantMessage(prompt)}
                className="px-3 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 border border-slate-200 rounded-full text-xs font-medium text-slate-700 transition"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Chat Messages Area */}
          <div className="h-[420px] overflow-y-auto space-y-3 p-4 bg-slate-50/60 rounded-xl border border-slate-200">
            {chatHistory.map((item, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${item.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-xs ${
                    item.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                  }`}
                >
                  {item.role === 'assistant' && (item.badge || item.data_nature || item.source) && (
                    <div className="mb-2 pb-2 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {item.badge && (
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase ${
                              item.badge === 'CURRENT OBSERVATION'
                                ? 'bg-sky-50 text-sky-700 border border-sky-200'
                                : item.badge === 'FORECAST'
                                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                : item.badge === 'LOCATION MISMATCH'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : item.badge.includes('ERROR')
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-slate-100 text-slate-700 border border-slate-200'
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                        {item.data_nature && (
                          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                            • {item.data_nature}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        {item.source && <span>{item.source}</span>}
                        {item.timestamp && (
                          <span>
                            {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  <p className="whitespace-pre-line">{item.text}</p>
                  {item.citations && item.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Citations:</span>
                      {item.citations.map((c, ci) => (
                        <span
                          key={ci}
                          className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-50 text-indigo-700 border border-indigo-200"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex items-center gap-2 text-xs text-indigo-600 p-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Querying Digital Twin knowledge base and sensor telemetry...
              </div>
            )}
          </div>

          {/* Chat Input Bar */}
          <div className="flex gap-2">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendAssistantMessage()}
              placeholder="Ask NOVA about Adyar flood risk, Chembarambakkam reservoir release, or vulnerable subways..."
              className="flex-1 px-4 py-2.5 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
            <button
              onClick={() => sendAssistantMessage()}
              disabled={chatLoading}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl flex items-center gap-2 transition"
            >
              <Send className="h-4 w-4" />
              Ask
            </button>
          </div>
        </div>
      )}

      {/* TAB 3: AI SITUATION REPORT (SITREP) */}
      {activeTab === 'sitrep' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Activity className="h-5 w-5 text-indigo-600" />
                Hourly Operational Situation Report (SitRep)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Automated digest of multi-hazard conditions, 24h changes, and priority actions across Chennai.
              </p>
            </div>
            <button
              onClick={downloadSitRep}
              className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-lg text-xs font-semibold text-slate-800 flex items-center gap-1.5 transition"
            >
              <Download className="h-3.5 w-3.5" />
              Download SitRep (JSON/CSV)
            </button>
          </div>

          {sitRep ? (
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-700 tracking-wider uppercase">Executive Overview</span>
                  <span className="text-xs text-slate-400">Generated: {new Date(sitRep.timestamp || sitRep.generated_at || Date.now()).toLocaleString()}</span>
                </div>
                <p className="text-sm font-medium text-slate-800 leading-relaxed">
                  {sitRep.executive_summary_text || 'No verified situation report text is currently available.'}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 border border-slate-200 rounded-xl bg-white">
                  <span className="text-xs font-bold text-slate-500 uppercase">Current operational posture</span>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {sitRep.current_hazards?.[0]?.level || 'Not reported'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Operational posture from the decision-support engine</p>
                </div>
                <div className="p-4 border border-slate-200 rounded-xl bg-white">
                  <span className="text-xs font-bold text-slate-500 uppercase">Reservoir Combined Storage</span>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {sitRep.reservoir_summary?.total_storage_mcft != null ? `${Number(sitRep.reservoir_summary.total_storage_mcft).toLocaleString()} Mcft` : 'Not reported'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1 font-semibold">{sitRep.reservoir_summary?.source || 'Source not reported'}</p>
                </div>
                <div className="p-4 border border-slate-200 rounded-xl bg-white">
                  <span className="text-xs font-bold text-slate-500 uppercase">Most Exposed Corridor</span>
                  <p className="text-xl font-bold text-amber-700 mt-1">
                    {sitRep.high_risk_assets?.[0]?.asset || 'No asset screening result'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">{sitRep.high_risk_assets?.[0]?.zone || 'Awaiting current screening result'}</p>
                </div>
                <div className="p-4 border border-slate-200 rounded-xl bg-white">
                  <span className="text-xs font-bold text-slate-500 uppercase">Telemetry Health</span>
                  <p className="text-xl font-bold text-emerald-600 mt-1">
                    {sitRep.sensor_health?.shs != null ? `${Math.round(sitRep.sensor_health.shs * 100)}%` : 'Not reported'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">{sitRep.sensor_health?.healthy_count ?? 0} healthy · {sitRep.sensor_health?.degraded_count ?? 0} degraded</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-slate-400">Loading SitRep data...</div>
          )}
        </div>
      )}

      {/* TAB 4: EXPLAINABLE RISK NARRATIVES */}
      {activeTab === 'narratives' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              Explainable Risk Narratives & Conformal Uncertainty Bounds
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Converts complex SHAP feature attributions and conformal prediction intervals into plain English for municipal commissioners.
            </p>
          </div>

          {riskNarrative ? (
            <div className="space-y-4">
              <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl">
                <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider">Operational Plain-English Narrative</span>
                <p className="text-sm text-slate-800 mt-1 leading-relaxed font-medium">
                  {riskNarrative.narrative || riskNarrative.plain_english_narrative || riskNarrative.narrative_text || 'No explanatory narrative is available.'}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-slate-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-slate-700 uppercase mb-3">Key Feature Drivers (SHAP)</h4>
                  <div className="space-y-2">
                    {(riskNarrative.driver_importance || riskNarrative.top_feature_drivers || []).map((f, i) => (
                      <div key={i} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-xs">
                        <span className="font-semibold text-slate-700">{f.feature}</span>
                        <span className="font-mono font-bold text-indigo-600">{f.contribution_pct != null ? `${f.contribution_pct}%` : f.shap_value ?? 'Not reported'}</span>
                      </div>
                    ))}
                    {(riskNarrative.driver_importance || riskNarrative.top_feature_drivers || []).length === 0 && <p className="text-xs text-slate-500">Feature attribution is not available for the current input stream.</p>}
                  </div>
                </div>

                <div className="border border-slate-200 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-slate-700 uppercase mb-3">Conformal Prediction Bounds (90% Confidence)</h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-500">Predicted Flood Likelihood:</span>
                        <span className="font-bold text-slate-800">
                          Not reported
                        </span>
                      </div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-500">Conformal Prediction Interval:</span>
                        <span className="font-mono font-bold text-emerald-600">
                          {riskNarrative.uncertainty_evaluation?.interval_width_90 != null ? `Width ${Number(riskNarrative.uncertainty_evaluation.interval_width_90).toFixed(3)}` : 'Not reported'}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Conformal Width:</span>
                        <span className="font-mono text-slate-700">
                          {riskNarrative.uncertainty_evaluation?.confidence_tier || 'Not reported'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-slate-400">Loading risk narrative...</div>
          )}
        </div>
      )}

      {/* TAB 5: AI WHAT-IF SIMULATOR */}
      {activeTab === 'what_if' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="h-5 w-5 text-indigo-600" />
              AI Multi-Hazard Counterfactual What-If Simulator
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulate compound climate shocks: precipitation spikes, infrastructure cascade failures, and reservoir buffers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-50 p-5 rounded-xl border border-slate-200">
            {/* Control 1: Rainfall */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-2">
                <span>Rainfall Intensity Delta:</span>
                <span className="font-bold text-indigo-600">{rainfallDelta > 0 ? `+${rainfallDelta}%` : `${rainfallDelta}%`}</span>
              </div>
              <input
                type="range"
                min="-50"
                max="100"
                step="5"
                value={rainfallDelta}
                onChange={(e) => setRainfallDelta(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400">Perturbs Open-Meteo IMD precipitation</span>
            </div>

            {/* Control 2: Pump failure */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-2">
                <span>Central Pump Station Status:</span>
                <span className={`font-bold ${pumpFailure ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {pumpFailure ? 'OFFLINE (FAILED)' : 'ONLINE (NORMAL)'}
                </span>
              </div>
              <button
                onClick={() => setPumpFailure(!pumpFailure)}
                className={`w-full py-2 rounded-lg text-xs font-bold transition border ${
                  pumpFailure
                    ? 'bg-rose-50 border-rose-300 text-rose-700 shadow-xs'
                    : 'bg-emerald-50 border-emerald-300 text-emerald-700 shadow-xs'
                }`}
              >
                {pumpFailure ? 'Simulating Central Failure' : 'Central Station Healthy'}
              </button>
            </div>

            {/* Control 3: Reservoir Buffer */}
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-2">
                <span>Reservoir Freeboard Buffer:</span>
                <span className="font-bold text-indigo-600">{reservoirBuffer}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={reservoirBuffer}
                onChange={(e) => setReservoirBuffer(Number(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400">Remaining flood absorption capacity</span>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={runCounterfactual}
              disabled={simulating}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl flex items-center gap-2 transition shadow-sm"
            >
              {simulating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Run Counterfactual Simulation
            </button>
          </div>

          {counterfactualResult && (
            <div className="p-5 bg-indigo-50/50 border border-indigo-200 rounded-xl space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                Counterfactual Simulation Findings
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-3.5 bg-white border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 font-semibold">Baseline Risk</span>
                  <p className="text-xl font-bold text-slate-700 mt-1">
                    {counterfactualResult.baseline_risk_score != null ? `${Math.round(counterfactualResult.baseline_risk_score * 100)}%` : 'Not reported'}
                  </p>
                </div>
                <div className="p-3.5 bg-white border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 font-semibold">Simulated Perturbed Risk</span>
                  <p className="text-xl font-bold text-rose-600 mt-1">
                    {counterfactualResult.simulated_risk_score != null ? `${Math.round(counterfactualResult.simulated_risk_score * 100)}%` : 'Not reported'}
                  </p>
                </div>
                <div className="p-3.5 bg-white border border-slate-200 rounded-lg">
                  <span className="text-xs text-slate-500 font-semibold">Risk Delta</span>
                  <p className="text-xl font-bold text-amber-600 mt-1">
                    {counterfactualResult.score_delta != null ? `${counterfactualResult.score_delta >= 0 ? '+' : ''}${Math.round(counterfactualResult.score_delta * 100)}%` : 'Not reported'}
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                <strong>Scenario assumptions:</strong> {counterfactualResult.assumptions?.join(' ') || counterfactualResult.counterfactual_disclaimer || 'No scenario explanation is available.'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 6: SMART BILINGUAL ALERT WRITER */}
      {activeTab === 'alerts' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Volume2 className="h-5 w-5 text-indigo-600" />
                Smart Bilingual Alert Writer (English & தமிழ்)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Automatically formats tailored alerts for citizens, municipal dispatch, and hospital infrastructure with human sign-off.
              </p>
            </div>
            <span className="px-3 py-1 bg-amber-50 border border-amber-200 rounded-full text-xs font-bold text-amber-800">
              HUMAN SIGN-OFF REQUIRED
            </span>
          </div>

          {smartAlerts ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* English Version */}
              <div className="p-5 border border-slate-200 rounded-xl bg-slate-50/50 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-700 uppercase">English Advisory Draft</span>
                  <span className="text-xs font-bold text-amber-600">{smartAlerts.threat_level || 'WARNING'}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">
                  {smartAlerts.alerts?.public_advisory?.title_en || 'No alert draft available'}
                </h3>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {smartAlerts.alerts?.public_advisory?.body_en || 'Generate a draft after current inputs are available.'}
                </p>
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-[11px] font-semibold text-slate-500">Action: </span>
                  <span className="text-[11px] text-slate-700">{smartAlerts.alerts?.public_advisory?.action_en || 'Not reported'}</span>
                </div>
              </div>

              {/* Tamil Version */}
              <div className="p-5 border border-indigo-200 rounded-xl bg-indigo-50/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-700 uppercase">தமிழ் எச்சரிக்கை அறிவிப்பு</span>
                  <span className="text-xs font-bold text-amber-600">எச்சரிக்கை</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900">
                  {smartAlerts.alerts?.public_advisory?.title_ta || 'எச்சரிக்கை வரைவு கிடைக்கவில்லை'}
                </h3>
                <p className="text-xs text-slate-700 leading-relaxed font-sans">
                  {smartAlerts.alerts?.public_advisory?.body_ta || 'தற்போதைய உள்ளீடுகள் கிடைத்த பிறகு வரைவை உருவாக்கவும்.'}
                </p>
                <div className="pt-2 border-t border-indigo-200">
                  <span className="text-[11px] font-semibold text-slate-500">செயல்: </span>
                  <span className="text-[11px] text-slate-700">{smartAlerts.alerts?.public_advisory?.action_ta || 'தகவல் இல்லை'}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-slate-400">Generating bilingual alert drafts...</div>
          )}

          <div className="flex items-center justify-between p-4 bg-slate-100 rounded-xl">
            <span className="text-xs text-slate-600">
              <strong>Audit Policy:</strong> No advisory is published to sirens or GCC WhatsApp gateways without explicit human operator confirmation.
            </span>
            <button
              onClick={() => setAlertDispatched(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg transition"
            >
              {alertDispatched ? '✓ Approval recorded — external delivery disabled' : 'Record operator approval'}
            </button>
          </div>
        </div>
      )}

      {/* TAB 7: ACTION PRIORITISATION ENGINE */}
      {activeTab === 'prioritisation' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-indigo-600" />
              Action Prioritisation Engine (MAUT Utility Matrix)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranks municipal interventions by expected benefit (35%), urgency (25%), exposed population (20%), and confidence (20%).
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 bg-slate-50">
                  <th className="p-3">Rank</th>
                  <th className="p-3">Action Description</th>
                  <th className="p-3">Target Location</th>
                  <th className="p-3">Agency</th>
                  <th className="p-3">Urgency</th>
                  <th className="p-3">Benefit</th>
                  <th className="p-3">Exposed Pop</th>
                  <th className="p-3">Cost</th>
                  <th className="p-3 font-bold text-indigo-600">Net Utility Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actions.map((act, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition">
                    <td className="p-3 font-bold text-indigo-600">#{act.priority_rank || i + 1}</td>
                    <td className="p-3 font-semibold text-slate-800">{act.title || 'Not reported'}</td>
                    <td className="p-3 text-slate-600">{act.resource_availability || 'Not reported'}</td>
                    <td className="p-3 text-slate-500 font-medium">{act.department || 'Not reported'}</td>
                    <td className="p-3">{act.urgency || 'Not reported'}</td>
                    <td className="p-3">{act.expected_benefit_score ?? 'Not reported'}</td>
                    <td className="p-3 font-mono">{act.affected_population != null ? act.affected_population.toLocaleString() : 'Not reported'}</td>
                    <td className="p-3 font-medium text-slate-500">{act.cost_tier || 'Not reported'}</td>
                    <td className="p-3 font-bold text-indigo-700 bg-indigo-50/50">
                      {act.priority_utility_score ?? 'Not reported'}
                    </td>
                  </tr>
                ))}
                {actions.length === 0 && <tr><td colSpan="9" className="p-6 text-center text-slate-500">No prioritised actions are available from the current API response.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 8: AI DATA QUALITY GUARDIAN */}
      {activeTab === 'guardian' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-indigo-600" />
              AI Data Quality Guardian (Safety Watchdog)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Continuously monitors telemetry freshness and plausibility, blocking autonomous escalation if feeds degrade.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`p-4 rounded-xl border ${guardian?.automated_escalation_permitted ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
              <div className="flex items-center gap-2 text-slate-800 font-bold text-sm mb-1">
                <ShieldCheck className="h-5 w-5 text-indigo-600" />
                Data Quality Guardrail Status: {guardian?.guardian_status || 'Awaiting API response'}
              </div>
              <p className="text-xs text-slate-700">
                Telemetry health: {guardian?.aggregate_telemetry_health != null ? `${guardian.aggregate_telemetry_health}%` : 'Not reported'} · Reservoir mode: {guardian?.reservoir_provenance_mode || 'Not reported'}
              </p>
            </div>

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-xs font-bold text-slate-700 uppercase">Autonomous Escalation Gate</span>
              <p className="text-xs text-slate-600 mt-1">
                {guardian?.guardian_rule || 'Awaiting current guardian policy.'}
              </p>
            </div>
          </div>

          {/* Monitored Feeds Table */}
          <div className="border border-slate-200 rounded-xl overflow-hidden mt-2">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="p-3">Sensor Feed Name</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Latency</th>
                  <th className="p-3">Plausibility</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(guardian?.active_flags || []).map((feed, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-800">{feed.source}</td>
                    <td className="p-3 text-slate-600">{feed.issue}</td>
                    <td className="p-3">—</td>
                    <td className="p-3 text-amber-700 font-bold">Requires review</td>
                    <td className="p-3 font-bold text-rose-700">{feed.severity}</td>
                  </tr>
                ))}
                {(guardian?.active_flags || []).length === 0 && <tr><td colSpan="5" className="p-6 text-center text-slate-500">No active quality flags were returned by the guardian.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 9: HISTORICAL EVENT COMPARATOR */}
      {activeTab === 'historical' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <History className="h-5 w-5 text-indigo-600" />
              Historical Event Comparator & Vector Analogy Matching
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Compares current live weather and reservoir states against verified historical disaster benchmarks.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {historicalEvents.map((ev, i) => (
              <div key={i} className="p-5 border border-slate-200 rounded-xl bg-slate-50/50 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{ev.event_name}</h4>
                    <span className="text-xs text-slate-500">{ev.dates}</span>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
                    {ev.similarity_score_pct}% Match
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed">
                  <strong>Past Impact:</strong> {ev.past_observed_impact}
                </p>
                {ev.key_differences && ev.key_differences.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
                    <strong>Current Difference:</strong> {ev.key_differences[0]}
                  </div>
                )}
              </div>
            ))}
            {historicalEvents.length === 0 && <p className="col-span-full rounded-xl border border-slate-200 p-6 text-center text-sm text-slate-500">No historical-comparison result is available from the current API response.</p>}
          </div>
        </div>
      )}

      {/* TAB 10: POST-EVENT LEARNING & HINDCAST */}
      {activeTab === 'learning' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="pb-3 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-indigo-600" />
              Post-Event Learning & Hindcast Verification
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Evaluates past issued warnings against ground-truth outcomes to compute lead times, false alarm ratios, and model retraining cues.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50">
              <span className="text-xs font-bold text-slate-500 uppercase">Average Lead Time</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{postEventData?.operational_metrics?.average_response_delay_minutes != null ? `${postEventData.operational_metrics.average_response_delay_minutes} min` : 'Not reported'}</p>
              <span className="text-[10px] text-slate-400">Operational-response metric</span>
            </div>
            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50">
              <span className="text-xs font-bold text-slate-500 uppercase">False Alarm Ratio (FAR)</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">Not reported</p>
              <span className="text-[10px] text-slate-400">Requires independently verified warning outcomes</span>
            </div>
            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50">
              <span className="text-xs font-bold text-slate-500 uppercase">Effective Actions</span>
              <p className="text-2xl font-bold text-indigo-600 mt-1">
                {postEventData?.operational_metrics?.effective_interventions ?? 3} / {postEventData?.operational_metrics?.total_actions_evaluated ?? 4}
              </p>
              <span className="text-[10px] text-slate-400">Retrospective operational records</span>
            </div>
            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50">
              <span className="text-xs font-bold text-slate-500 uppercase">Model Retraining Status</span>
              <p className="text-2xl font-bold text-emerald-700 mt-1">REVIEW REQUIRED</p>
              <span className="text-[10px] text-slate-400">Use Model Health for current drift evidence</span>
            </div>
          </div>

          {/* Verified Hindcast Cases */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
              Verified Ground-Truth Hindcast Events
            </h4>
            <div className="space-y-3">
              {(postEventData?.verified_hindcast_cases || []).map((c, idx) => (
                <div key={idx} className="p-4 border border-slate-200 rounded-xl bg-white space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 text-sm">{c.event_title}</span>
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                      {c.assessment}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600">
                    <strong>Ground Truth:</strong> {c.ground_truth_outcome} (Lead Time: {c.issued_lead_time_hours}h)
                  </p>
                  <p className="text-xs text-indigo-700">
                    <strong>Post-Event Learning:</strong> {c.learning_recommendation}
                  </p>
                </div>
              ))}
              {(!postEventData?.verified_hindcast_cases || postEventData.verified_hindcast_cases.length === 0) && <p className="rounded-xl border border-slate-200 p-5 text-center text-sm text-slate-500">No verified post-event cases are available. Import source-backed outcomes before evaluating warning performance.</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
