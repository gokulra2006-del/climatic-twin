import { useEffect, useState } from 'react'
import { Beaker, AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert, Activity, Fingerprint, LockKeyhole } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const Metric = ({ label, value }) => (
  <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">{label}</div>
    <div className="mt-0.5 font-black text-slate-900">{typeof value === 'number' ? value.toFixed(3) : value}</div>
  </div>
)

export default function SyntheticBenchmarkPanel() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = async () => {
    setLoading(true); setError('')
    try {
      const response = await fetch(`${API_URL}/api/synthetic-benchmark/summary`)
      if (!response.ok) throw new Error(`Benchmark report unavailable (${response.status})`)
      setReport(await response.json())
    } catch (e) { setError(e.message || 'Unable to load the synthetic benchmark report.') }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  return <div className="max-w-6xl mx-auto space-y-6 pb-12">
    <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
      <div className="flex flex-col sm:flex-row justify-between gap-5">
        <div><div className="flex items-center gap-2 text-indigo-700 text-xs font-bold uppercase tracking-wide mb-2"><Beaker className="h-4 w-4" /> Reproducible training sandbox</div>
          <h2 className="text-2xl font-black text-slate-900">Synthetic Flood-Risk Benchmark</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">A chronological, simulated benchmark for testing the software and comparing models. It is deliberately isolated from the deployed model.</p>
        </div>
        <button onClick={load} disabled={loading} className="self-start inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-60"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh results</button>
      </div>
    </section>
    {error && <section className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800 flex gap-3"><AlertTriangle className="h-5 w-5 shrink-0" />{error}</section>}
    {loading && !report ? <section className="rounded-2xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">Loading benchmark report…</section> : report && <>
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 flex gap-3"><ShieldAlert className="h-5 w-5 shrink-0 text-amber-700" /><div className="text-sm text-amber-900"><strong>Research boundary:</strong> {report.claim_boundary}</div></section>
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Metric label="Generated rows" value={report.generated_rows?.toLocaleString()} /><Metric label="Synthetic event rate" value={`${(report.positive_rate * 100).toFixed(1)}%`} /><Metric label="Chronological split" value="2014–20 / 2021 / 2022" /><Metric label="Deployment policy" value="Benchmark only" />
      </section>
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {Object.entries(report.models || {}).map(([name, output]) => <article key={name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-4"><h3 className="font-bold text-slate-900">{name}</h3>{name === report.champion && <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-black tracking-wide text-emerald-800">SANDBOX CHAMPION</span>}</div>
          <p className="mt-1 text-xs text-slate-500">Same simulated process, later-year chronological evaluation.</p>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">{Object.entries(output.test_2022 || {}).map(([label, value]) => <Metric key={label} label={`2022 ${label.replace('_', ' ')}`} value={value} />)}</div>
        </article>)}
      </section>
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex gap-3"><Activity className="h-5 w-5 shrink-0 text-indigo-600" /><div><h3 className="font-bold text-slate-900">Calibration check</h3><p className="mt-1 text-xs leading-5 text-slate-500">Whether predicted probabilities agree with simulated event frequencies on the untouched 2022 period.</p></div></div>
          <div className="mt-4 grid grid-cols-2 gap-3"><Metric label="Brier score" value={report.calibration?.test_2022_brier} /><Metric label="Expected calibration error" value={report.calibration?.test_2022_ece} /></div>
          <p className="mt-3 text-[11px] leading-5 text-slate-500">{report.calibration?.meaning}</p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex gap-3"><ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" /><div><h3 className="font-bold text-slate-900">Missing-telemetry resilience</h3><p className="mt-1 text-xs leading-5 text-slate-500">20% random feature masking with median imputation. This checks whether the pipeline remains usable under controlled simulated loss.</p></div></div>
          <div className="mt-4 grid grid-cols-2 gap-3"><Metric label="Valid prediction rate" value={`${((report.input_stress_tests?.missing_telemetry_20pct?.valid_prediction_rate || 0) * 100).toFixed(0)}%`} /><Metric label="Mean probability shift" value={report.input_stress_tests?.missing_telemetry_20pct?.mean_absolute_probability_shift} /></div>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <div className="flex gap-3"><AlertTriangle className="h-5 w-5 shrink-0 text-rose-600" /><div><h3 className="font-bold text-slate-900">Extreme-rain input stress test</h3><p className="mt-1 text-xs leading-5 text-slate-500">Rainfall and antecedent-rainfall inputs are increased by 35%. This measures sensitivity, not forecast accuracy, because no observed labels exist for this hypothetical scenario.</p></div></div>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3"><Metric label="Mean probability change" value={report.input_stress_tests?.heavy_rain_plus_35pct?.mean_probability_change} /><Metric label="Baseline alert rate" value={`${((report.input_stress_tests?.heavy_rain_plus_35pct?.baseline_alert_rate_at_0_5 || 0) * 100).toFixed(1)}%`} /><Metric label="Stress-test alert rate" value={`${((report.input_stress_tests?.heavy_rain_plus_35pct?.alert_rate_at_0_5 || 0) * 100).toFixed(1)}%`} /></div>
        </article>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex gap-3"><Fingerprint className="h-5 w-5 shrink-0 text-indigo-600" /><div className="min-w-0"><h3 className="font-bold text-slate-900">Reproducibility record</h3><p className="mt-1 text-xs leading-5 text-slate-500">Every result can be regenerated from a fixed seed. These fingerprints detect changes to the benchmark dataset or model artifact.</p></div></div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs"><div className="rounded-lg bg-slate-50 border border-slate-200 p-3"><span className="block font-bold text-slate-500 text-[10px] uppercase">Dataset SHA-256</span><code className="mt-1 block break-all text-slate-700">{report.reproducibility?.dataset_sha256}</code></div><div className="rounded-lg bg-slate-50 border border-slate-200 p-3"><span className="block font-bold text-slate-500 text-[10px] uppercase">Model SHA-256</span><code className="mt-1 block break-all text-slate-700">{report.reproducibility?.model_sha256}</code></div></div>
      </section>
      <section className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5"><div className="flex gap-3"><LockKeyhole className="h-5 w-5 shrink-0 text-indigo-700" /><div><h3 className="font-bold text-indigo-950">Model promotion gate</h3><p className="mt-1 text-sm leading-6 text-indigo-900">This sandbox model cannot become the live model. Promotion requires independently verified Chennai impact labels, event-based holdouts, calibration on field data, and a documented approval decision.</p></div></div></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex gap-3"><CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" /><div><h3 className="font-bold text-slate-900">What this strengthens</h3><p className="mt-1 text-sm leading-6 text-slate-600">Reproducible training, time-aware model comparison, regression testing, and clear provenance. Next, validate the same pipeline against independent Chennai impact records before making accuracy claims.</p></div></div></section>
    </>}
  </div>
}
