import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, ClipboardCheck, RefreshCw, ShieldAlert } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const statusStyle = {
  READY_FOR_EVALUATION: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  READY_FOR_IMPORT: 'bg-blue-100 text-blue-800 border-blue-200',
  SCENARIO_READY: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  READY_FOR_CHECK: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  PARTIAL: 'bg-amber-100 text-amber-800 border-amber-200',
  PROVENANCE_GATED: 'bg-amber-100 text-amber-800 border-amber-200',
  PROTOTYPE_ONLY: 'bg-amber-100 text-amber-800 border-amber-200',
  BLOCKED: 'bg-rose-100 text-rose-800 border-rose-200',
}

export default function ResearchReadinessPanel() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API_URL}/api/research-readiness/summary`)
      if (!response.ok) throw new Error(`Readiness request failed (${response.status})`)
      setReport(await response.json())
    } catch (requestError) {
      setError(requestError.message || 'The evidence-readiness service is unavailable.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-5">
          <div>
            <div className="flex items-center gap-2 text-indigo-700 text-xs font-bold uppercase tracking-wide mb-2">
              <ClipboardCheck className="h-4 w-4" /> Publication evidence gate
            </div>
            <h2 className="text-2xl font-black text-slate-900">Research Evidence Readiness</h2>
            <p className="text-sm text-slate-500 leading-6 mt-2 max-w-3xl">
              This board separates completed software from evidence still needed for defensible research claims. It never turns simulated or proxy outputs into field validation.
            </p>
          </div>
          <button onClick={load} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 disabled:opacity-60 px-4 py-2.5 text-xs font-bold text-slate-700">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh evidence status
          </button>
        </div>
      </section>

      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800 flex gap-3"><AlertTriangle className="h-5 w-5 shrink-0" />{error}</div>}

      {loading && !report ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500"><RefreshCw className="h-5 w-5 animate-spin mx-auto mb-3 text-indigo-500" />Checking evidence maturity…</div>
      ) : report && (
        <>
          <section className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900 flex gap-3">
            <ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" />
            <span><strong>Claim policy:</strong> {report.journal_claim_policy}</span>
          </section>
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.items.map((item) => (
              <article key={item.gap} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-bold text-slate-900">{item.gap}</h3>
                  <span className={`shrink-0 border rounded-full px-2.5 py-1 text-[10px] font-black tracking-wide ${statusStyle[item.status] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>{item.status.replaceAll('_', ' ')}</span>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-600">{item.evidence}</p>
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <div className="text-[10px] font-black uppercase tracking-wide text-slate-500">To close this gap</div>
                  <ul className="mt-2 space-y-1.5 text-xs text-slate-700">
                    {item.required_next_evidence.map((next) => <li key={next} className="flex gap-2"><CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0 text-indigo-500" />{next}</li>)}
                  </ul>
                </div>
                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-[11px] leading-4 text-slate-600"><strong className="text-slate-800">Claim boundary:</strong> {item.claim_boundary}</div>
              </article>
            ))}
          </section>
        </>
      )}
    </div>
  )
}
