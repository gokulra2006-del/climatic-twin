import { useEffect, useState } from 'react'
import { CheckCircle2, ClipboardCheck, Database, Globe2, Languages, LockKeyhole, Radio, Send, ShieldCheck } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const tone = (area) => area.includes('Security') ? 'border-rose-200 bg-rose-50/40' : area.includes('Equity') ? 'border-sky-200 bg-sky-50/40' : 'border-slate-200 bg-white'

export default function ResearchOperationsHub() {
  const [overview, setOverview] = useState(null)
  const [security, setSecurity] = useState(null)
  const [liveData, setLiveData] = useState(null)
  const [draft, setDraft] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [advisory, setAdvisory] = useState({ hazard: 'Flood', level: 'Moderate', location: 'Chennai', evidence_status: 'prototype' })
  const [action, setAction] = useState({ action_type: 'verify_telemetry', status: 'planned', location: 'Chennai', actor_name: 'local operator', evidence_status: 'unverified', outcome_note: '' })

  const load = async () => {
    setLoading(true)
    try {
      const [overviewResponse, securityResponse, liveResponse] = await Promise.all([
        fetch(`${API_URL}/api/research-operations/overview`),
        fetch(`${API_URL}/api/research-operations/security-readiness`),
        fetch(`${API_URL}/api/research-operations/live-data-status`),
      ])
      if (!overviewResponse.ok || !securityResponse.ok || !liveResponse.ok) throw new Error('Research workflow service is unavailable.')
      setOverview(await overviewResponse.json())
      setSecurity(await securityResponse.json())
      setLiveData(await liveResponse.json())
    } catch (error) {
      setMessage(error.message)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])
  const createDraft = async () => {
    setMessage('')
    const response = await fetch(`${API_URL}/api/research-operations/advisory-draft`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(advisory) })
    const data = await response.json()
    if (!response.ok) return setMessage(data.detail || 'Could not create the draft.')
    setDraft(data)
  }
  const logAction = async () => {
    setMessage('')
    const response = await fetch(`${API_URL}/api/research-operations/action-outcomes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(action) })
    const data = await response.json()
    setMessage(response.ok ? `Action evidence logged to ${data.saved_to}.` : (data.detail || 'Could not log the action.'))
  }

  if (loading) return <div className="max-w-7xl mx-auto text-sm text-slate-500 p-8">Loading research operations…</div>
  return <div className="max-w-7xl mx-auto space-y-6">
    <section className="rounded-2xl border border-indigo-100 bg-gradient-to-r from-indigo-50 via-white to-emerald-50 p-6 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div><p className="text-xs uppercase font-bold tracking-widest text-indigo-600">Publication evidence workflow</p><h1 className="mt-1 text-2xl font-black text-slate-900">Evidence & Action Hub</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Turn the remaining research gaps into traceable work: import evidence, evaluate event windows, record human decisions, and keep prototype outputs separate from verified findings.</p></div>
        <button onClick={load} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white hover:bg-slate-700">Refresh status</button>
      </div>
    </section>

    {message && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900">{message}</div>}

    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div className="flex items-start gap-3"><span className={`mt-1 rounded-full p-2 ${liveData?.status === 'LIVE_WEATHER_AVAILABLE' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}><Radio className="h-4 w-4"/></span><div><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Live-data truth panel</p><h2 className="text-lg font-black text-slate-900">{liveData?.status === 'LIVE_WEATHER_AVAILABLE' ? 'Live weather feed connected' : 'Live weather feed unavailable'}</h2><p className="mt-1 text-sm text-slate-600">{liveData?.boundary}</p></div></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{liveData?.updated_at ? `Updated ${new Date(liveData.updated_at).toLocaleTimeString()}` : 'No current timestamp'}</span></div><div className="mt-4 grid gap-3 md:grid-cols-4">{liveData?.feeds?.map(feed => <div key={feed.name} className="rounded-xl border border-slate-200 bg-slate-50 p-3"><p className="text-sm font-bold text-slate-800">{feed.name}</p><p className={`mt-1 text-xs font-bold uppercase ${feed.state === 'live' ? 'text-emerald-600' : feed.state === 'simulated' ? 'text-amber-600' : 'text-slate-500'}`}>{feed.state.replaceAll('_', ' ')}</p><p className="mt-2 text-xs text-slate-500">{feed.source}</p></div>)}</div>{liveData?.snapshot && <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl border border-indigo-100 bg-indigo-50/50 p-3 text-sm sm:grid-cols-4"><span><b>Temp:</b> {liveData.snapshot.temperature_c ?? '—'} °C</span><span><b>Humidity:</b> {liveData.snapshot.humidity_percent ?? '—'}%</span><span><b>Rain, 7d:</b> {liveData.snapshot.rainfall_7d_mm ?? '—'} mm</span><span><b>Root-zone moisture:</b> {liveData.snapshot.soil_moisture_root_zone ?? '—'}</span></div>}</section>

    <section><div className="mb-3 flex items-center gap-2"><ClipboardCheck className="h-5 w-5 text-indigo-600"/><h2 className="font-bold text-slate-900">Research gap closure plan</h2></div><div className="grid gap-3 md:grid-cols-2">
      {overview?.items?.map((item) => <article key={item.area} className={`rounded-xl border p-4 ${tone(item.area)}`}><h3 className="font-bold text-slate-900">{item.area}</h3><p className="mt-2 text-sm text-slate-600"><span className="font-semibold text-slate-800">Available now:</span> {item.current}</p><p className="mt-2 text-sm text-indigo-700"><span className="font-semibold">Next workflow:</span> {item.workflow}</p><ul className="mt-3 space-y-1 text-xs text-slate-600">{item.needed.map((need) => <li key={need} className="flex gap-2"><span className="text-amber-500">•</span>{need}</li>)}</ul><p className="mt-3 border-t border-slate-200 pt-3 text-xs font-medium text-rose-700">Claim boundary: {item.boundary}</p></article>)}
    </div></section>

    <section className="grid gap-6 lg:grid-cols-2">
      <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><Languages className="h-5 w-5 text-indigo-600"/><h2 className="font-bold text-slate-900">Bilingual advisory draft</h2></div><p className="mt-2 text-sm text-slate-600">Prepare accessible English and Tamil text for authorised review. This tool never publishes an alert.</p><div className="mt-4 grid gap-3 sm:grid-cols-2">
        {[['Hazard','hazard'],['Level','level'],['Location','location']].map(([label,key]) => <label key={key} className="text-xs font-semibold text-slate-600">{label}<input value={advisory[key]} onChange={(e) => setAdvisory({...advisory, [key]: e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"/></label>)}
        <label className="text-xs font-semibold text-slate-600">Evidence status<select value={advisory.evidence_status} onChange={(e) => setAdvisory({...advisory, evidence_status:e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"><option>prototype</option><option>proxy</option><option>historical_real</option></select></label>
      </div><button onClick={createDraft} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-700"><Globe2 className="h-4 w-4"/>Create review draft</button>
      {draft && <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm"><p className="font-bold text-amber-700">{draft.status.replaceAll('_', ' ')}</p><p className="mt-3 text-slate-700">{draft.english}</p><p className="mt-3 leading-6 text-slate-700">{draft.tamil}</p><p className="mt-3 text-xs text-slate-500">{draft.accessibility_note}</p></div>}</article>

      <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><Send className="h-5 w-5 text-emerald-600"/><h2 className="font-bold text-slate-900">Human action & outcome log</h2></div><p className="mt-2 text-sm text-slate-600">Record a reviewed response. Attach a traceable source before presenting it as historical evidence.</p><div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-semibold text-slate-600">Action<select value={action.action_type} onChange={(e) => setAction({...action, action_type:e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"><option>verify_telemetry</option><option>inspect_asset</option><option>issue_advisory</option><option>deploy_pump</option><option>road_advisory</option></select></label>
        <label className="text-xs font-semibold text-slate-600">Status<select value={action.status} onChange={(e) => setAction({...action, status:e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"><option>planned</option><option>approved</option><option>completed</option><option>not_completed</option></select></label>
        <label className="text-xs font-semibold text-slate-600">Location<input value={action.location} onChange={(e) => setAction({...action, location:e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"/></label>
        <label className="text-xs font-semibold text-slate-600">Evidence status<select value={action.evidence_status} onChange={(e) => setAction({...action, evidence_status:e.target.value})} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"><option>unverified</option><option>proxy</option><option>synthetic</option><option>historical_real</option></select></label>
      </div><label className="mt-3 block text-xs font-semibold text-slate-600">Outcome note<textarea value={action.outcome_note} onChange={(e) => setAction({...action, outcome_note:e.target.value})} className="mt-1 min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="What was reviewed or observed?"/></label><button onClick={logAction} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-white hover:bg-emerald-700"><CheckCircle2 className="h-4 w-4"/>Log reviewed action</button></article>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><Database className="h-5 w-5 text-indigo-600"/><h2 className="font-bold text-slate-900">Verified evidence import pack</h2></div><p className="mt-2 text-sm text-slate-600">Download a blank, provenance-aware template, populate it only from traceable records, then use the Impact Catalogue to validate and import the data. Templates themselves contain no evidence.</p><div className="mt-4 flex flex-wrap gap-3">{[['impact_catalogue','Impact records'],['infrastructure_dependencies','Dependency edges'],['drought_replay','2019 drought inputs']].map(([name,label]) => <a key={name} href={`${API_URL}/api/research-operations/templates/${name}`} className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-bold text-indigo-700 hover:bg-indigo-100">Download {label} CSV</a>)}</div></section>

    <section className="grid gap-4 lg:grid-cols-2"><article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-indigo-600"/><h2 className="font-bold text-slate-900">Research promotion gate</h2></div><ol className="mt-3 space-y-2 text-sm text-slate-700">{overview?.promotion_gate?.map((gate, index) => <li key={gate} className="flex gap-3"><span className="font-black text-indigo-600">{index + 1}</span>{gate}</li>)}</ol></article><article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><LockKeyhole className="h-5 w-5 text-rose-600"/><h2 className="font-bold text-slate-900">Security & governance boundary</h2></div><p className="mt-2 text-sm font-medium text-rose-700">{security?.boundary}</p><div className="mt-3 grid gap-3 sm:grid-cols-2"><div><p className="text-xs font-bold uppercase text-slate-500">Implemented</p><ul className="mt-1 text-sm text-slate-700">{security?.implemented?.map(x => <li key={x}>• {x}</li>)}</ul></div><div><p className="text-xs font-bold uppercase text-slate-500">Required before deployment</p><ul className="mt-1 text-sm text-slate-700">{security?.required_before_deployment?.map(x => <li key={x}>• {x}</li>)}</ul></div></div></article></section>
  </div>
}
