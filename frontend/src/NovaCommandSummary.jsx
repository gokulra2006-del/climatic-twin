import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Bot, BrainCircuit, ChevronDown, ChevronUp, ClipboardCheck, Copy, Database, Download, Loader2, RefreshCw, Send, ShieldCheck, TimerReset } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const RISK = { LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200', MODERATE: 'bg-amber-50 text-amber-800 border-amber-200', HIGH: 'bg-orange-50 text-orange-800 border-orange-200', CRITICAL: 'bg-rose-50 text-rose-800 border-rose-200' };
const prompts = ['What should the team do now?', 'What evidence supports this priority?', 'What would trigger escalation?', 'How reliable is this briefing?'];
const riskStyle = (level) => RISK[level] || 'bg-slate-50 text-slate-700 border-slate-200';

export default function NovaCommandSummary({ apiOnline, selectedHazard = 'FLOOD' }) {
  const [summary, setSummary] = useState(null);
  const [provider, setProvider] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [answerMode, setAnswerMode] = useState('');
  const [asking, setAsking] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(() => {
    return localStorage.getItem('climatetwin_nova_expanded') === 'true';
  });

  const toggleExpanded = () => {
    setIsExpanded(prev => {
      const next = !prev;
      localStorage.setItem('climatetwin_nova_expanded', String(next));
      return next;
    });
  };

  const refresh = useCallback(async () => {
    if (!apiOnline) { setError('The local backend is unavailable. Start it, then refresh NOVA.'); setLoading(false); return; }
    setLoading(true); setError('');
    try {
      const [brief, status] = await Promise.all([
        fetch(`${API_URL}/api/ai/command-summary?hazard=${encodeURIComponent(selectedHazard)}`),
        fetch(`${API_URL}/api/ai/provider-status`),
      ]);
      if (!brief.ok) throw new Error('NOVA could not load the current operations brief.');
      setSummary(await brief.json());
      if (status.ok) setProvider(await status.json());
    } catch (err) { setError(err.message || 'Unable to load NOVA.'); }
    finally { setLoading(false); }
  }, [apiOnline, selectedHazard]);

  useEffect(() => { refresh(); }, [refresh]);

  const handover = useMemo(() => {
    if (!summary) return '';
    const brief = summary.decision_brief || {};
    return [`ClimateTwin NOVA shift handover — ${new Date(summary.timestamp).toLocaleString()}`, `Priority: ${summary.priority_threat?.type?.replaceAll('_', ' ') || 'Unavailable'} (${summary.priority_threat?.level || 'UNKNOWN'})`, `Action: ${brief.action || summary.recommended_action}`, `Owner: ${brief.owner || 'Duty analyst'} | Review: ${brief.review_in_minutes || 60} minutes`, `Escalate when: ${brief.escalation_trigger || 'authorised evidence confirms impact.'}`, `Boundary: ${brief.evidence_boundary || summary.method_note || ''}`].join('\n');
  }, [summary]);

  const copyHandover = async () => { try { await navigator.clipboard.writeText(handover); setCopied(true); window.setTimeout(() => setCopied(false), 1800); } catch { setError('Clipboard access was blocked. Copy the handover manually.'); } };
  const downloadHandover = () => { const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([handover], { type: 'text/plain' })); link.download = `climatetwin-nova-handover-${new Date().toISOString().slice(0, 10)}.txt`; link.click(); URL.revokeObjectURL(link.href); };
  const askNova = async (text) => {
    if (!text?.trim()) return;
    setQuestion(text); setAsking(true); setAnswer(null);
    try {
      const response = await fetch(`${API_URL}/api/ai/copilot`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: text, hazard: selectedHazard }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'NOVA could not answer this question.');
      setAnswer(data.answer); setAnswerMode(data.mode);
    } catch { setAnswer('NOVA could not complete this request. Refresh the briefing and try again.'); setAnswerMode('UNAVAILABLE'); }
    finally { setAsking(false); }
  };

  if (loading) return <section aria-live="polite" className="mb-6 rounded-xl border border-slate-200 bg-white p-8 shadow-sm"><div className="flex items-center gap-3 text-slate-700"><Loader2 className="h-5 w-5 animate-spin text-indigo-600" /> Loading NOVA’s evidence-grounded operations brief…</div></section>;
  if (error || !summary) return <section className="mb-6 rounded-xl border border-rose-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div className="flex gap-3"><AlertTriangle className="mt-0.5 h-5 w-5 text-rose-600" /><div><h2 className="font-heading font-bold text-slate-900">NOVA needs attention</h2><p className="mt-1 text-sm text-slate-600">{error || 'No briefing is available.'}</p></div></div><button onClick={refresh} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500"><RefreshCw className="h-4 w-4" /> Retry</button></div></section>;

  const { priority_threat: threat = {}, decision_brief: brief = {}, data_trust: trust = {}, highest_priority_asset: asset = {}, source_ledger: ledger = {}, recommended_checks: checks = [], next_60_minutes: horizon = [] } = summary;
  const level = threat.level || 'UNKNOWN';

  if (!isExpanded) {
    return (
      <section aria-label="NOVA operations workspace" className="mb-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:border-indigo-200">
        <div className="flex flex-col gap-3 p-4 sm:px-6 sm:py-3.5 md:flex-row md:items-center md:justify-between bg-gradient-to-r from-indigo-50/40 via-white to-slate-50/40">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="rounded-lg bg-indigo-50 p-2 text-indigo-700 shrink-0">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex flex-wrap items-center gap-2">
              <span className="font-heading text-sm font-bold text-slate-950">NOVA Workspace</span>
              <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700">DECISION SUPPORT</span>
              <span className="text-slate-300 hidden sm:inline">|</span>
              <span className="text-xs text-slate-500">Priority:</span>
              <span className="text-xs font-semibold text-slate-900">{String(threat.type || 'No priority').replaceAll('_', ' ')}</span>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${riskStyle(level)}`}>{level}</span>
              <span className="text-slate-300 hidden lg:inline">|</span>
              <span className="hidden lg:inline text-xs text-slate-600 truncate max-w-md">
                <strong>Action:</strong> {brief.action || summary.recommended_action}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
            <span className="hidden xl:inline text-xs text-slate-500 mr-1">
              Trust: <strong>{Math.round((trust.score ?? 0) * 100)}%</strong>
            </span>
            <button
              onClick={refresh}
              title="Refresh briefing"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-300 focus:ring-2 focus:ring-indigo-500 transition"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={toggleExpanded}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 shadow-sm focus:ring-2 focus:ring-indigo-500 transition"
            >
              Expand NOVA <ChevronDown className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>
    );
  }

  return <section aria-label="NOVA operations workspace" className="mb-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition">
    <header className="border-b border-slate-200 px-5 py-4 sm:px-6"><div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"><div className="flex items-start gap-3"><div className="rounded-lg bg-indigo-50 p-2.5"><BrainCircuit className="h-6 w-6 text-indigo-700" /></div><div><div className="flex flex-wrap items-center gap-2"><h2 className="font-heading text-xl font-bold text-slate-950">NOVA Operations Workspace</h2><span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[11px] font-bold text-indigo-700">DECISION SUPPORT</span></div><p className="mt-1 text-sm text-slate-500">Prioritise evidence, assign the next check, and prepare a traceable handover.</p></div></div><div className="flex flex-wrap items-center gap-2"><span className="text-xs text-slate-500">Updated {new Date(summary.timestamp).toLocaleTimeString()}</span><button onClick={refresh} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus:ring-2 focus:ring-indigo-500"><RefreshCw className="h-4 w-4" /> Refresh</button><button onClick={toggleExpanded} className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 focus:ring-2 focus:ring-indigo-500 transition">Collapse NOVA <ChevronUp className="h-4 w-4" /></button></div></div></header>

    <div className="grid gap-4 p-5 sm:p-6 xl:grid-cols-3">
      <article className="rounded-xl border border-slate-200 p-4 xl:col-span-2"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Current operational priority</p><h3 className="mt-1 font-heading text-2xl font-bold text-slate-950">{String(threat.type || 'No priority').replaceAll('_', ' ')}</h3></div><span className={`rounded-full border px-3 py-1 text-sm font-bold ${riskStyle(level)}`}>{level}</span></div><p className="mt-3 text-sm leading-6 text-slate-700">{summary.current_situation}</p><div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-700"><ClipboardCheck className="h-4 w-4" /> Next accountable action</div><p className="mt-2 text-base font-semibold text-slate-900">{brief.action || summary.recommended_action}</p><div className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-3"><span><b>Owner:</b> {brief.owner || 'Duty analyst'}</span><span><b>Review:</b> {brief.review_in_minutes || 60} min</span><span><b>Mode:</b> {brief.operating_mode || 'NORMAL'}</span></div></div></article>
      <aside className="rounded-xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Confidence & provenance</p><div className="mt-3 grid grid-cols-2 gap-3"><div><p className="text-2xl font-bold text-slate-950">{Math.round((trust.score ?? 0) * 100)}%</p><p className="text-xs text-slate-500">data trust</p></div><div><p className="text-sm font-bold text-slate-900">{provider?.configured ? 'Provider AI' : 'Local AI'}</p><p className="text-xs text-slate-500">{provider?.configured ? 'server-side key' : 'evidence fallback'}</p></div></div><div className="mt-4 space-y-2 border-t border-slate-200 pt-3 text-xs text-slate-600"><p><b>Telemetry:</b> {ledger.telemetry || 'Current source summary'}</p><p><b>Flood model:</b> {ledger.flood_model || 'Unknown'}</p><p><b>Asset priority:</b> {ledger.asset_priority || 'Screening only'}</p></div></aside>
      <article className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2"><TimerReset className="h-4 w-4 text-indigo-600" /><h3 className="font-heading font-bold text-slate-900">Review timeline</h3></div><div className="mt-3 space-y-3">{horizon.map((item) => <div key={item.horizon} className="flex items-center justify-between gap-3 text-sm"><span className="font-semibold text-slate-700">{item.horizon}</span><span className={`rounded-full border px-2 py-0.5 text-xs font-bold ${riskStyle(item.risk)}`}>{item.risk}</span><span className="text-right text-xs text-slate-500">{item.trend}</span></div>)}</div></article>
      <article className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2"><Database className="h-4 w-4 text-indigo-600" /><h3 className="font-heading font-bold text-slate-900">Priority asset</h3></div><p className="mt-3 font-semibold text-slate-900">{asset['Asset Name'] || 'No asset priority available'}</p><p className="mt-1 text-sm text-slate-600">Risk index: <b>{Number.isFinite(asset['Asset Risk Index']) ? asset['Asset Risk Index'].toFixed(2) : 'Not available'}</b> · {asset['Risk Level'] || 'Unrated'}</p><p className="mt-3 text-xs leading-5 text-slate-500">Prototype screening priority. Confirm it through authorised field sources before resource deployment.</p></article>
      <article className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-600" /><h3 className="font-heading font-bold text-slate-900">Required checks</h3></div><ol className="mt-3 space-y-2 text-sm text-slate-700">{checks.map((check, index) => <li key={check} className="flex gap-2"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600">{index + 1}</span>{check}</li>)}</ol></article>
    </div>

    <div className="border-t border-slate-200 bg-slate-50 p-5 sm:p-6"><div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between"><div><div className="flex items-center gap-2"><Bot className="h-5 w-5 text-indigo-600" /><h3 className="font-heading text-lg font-bold text-slate-950">Ask NOVA</h3></div><p className="mt-1 text-sm text-slate-600">Ask about the supplied evidence, assigned action, or escalation conditions.</p><div className="mt-3 flex flex-wrap gap-2">{prompts.map((prompt) => <button key={prompt} onClick={() => askNova(prompt)} disabled={asking} className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-indigo-400 hover:text-indigo-700 disabled:opacity-50">{prompt}</button>)}</div></div><div className="flex flex-wrap gap-2"><button onClick={copyHandover} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"><Copy className="h-4 w-4" />{copied ? 'Copied' : 'Copy handover'}</button><button onClick={downloadHandover} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700"><Download className="h-4 w-4" /> Download brief</button></div></div><form onSubmit={(event) => { event.preventDefault(); askNova(question); }} className="mt-4 flex gap-2"><label className="sr-only" htmlFor="nova-question">Ask NOVA a question</label><input id="nova-question" value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={1000} placeholder="Ask a focused operational question…" className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200" /><button disabled={!question.trim() || asking} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50">{asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Ask</button></form>{answer && <div aria-live="polite" className="mt-4 rounded-lg border border-indigo-200 bg-white p-4"><p className="text-xs font-bold uppercase tracking-wider text-indigo-700">NOVA response · {answerMode.replaceAll('_', ' ')}</p><p className="mt-2 text-sm leading-6 text-slate-800">{answer}</p></div>}<p className="mt-4 text-xs leading-5 text-slate-500">{brief.evidence_boundary || summary.method_note}</p></div>
  </section>;
}
