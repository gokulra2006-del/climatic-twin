import React, { useState, useEffect } from 'react';
import { 
  Database, AlertTriangle, ShieldCheck, Filter, Download, 
  MapPin, Clock, ExternalLink, RefreshCw, Info, ChevronRight, X, FileText, Upload, BookOpen, CheckCircle2
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function ImpactCatalogue() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  
  // Filters
  const [zoneFilter, setZoneFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Evaluation modal state
  const [evalModal, setEvalModal] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalResult, setEvalResult] = useState(null);
  const [importMessage, setImportMessage] = useState('');
  const [warningCount, setWarningCount] = useState(0);
  const [evidenceGuideOpen, setEvidenceGuideOpen] = useState(false);
  const [officialSources, setOfficialSources] = useState([]);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      let query = `${API_URL}/api/impacts/?`;
      if (zoneFilter) query += `zone=${encodeURIComponent(zoneFilter)}&`;
      if (typeFilter) query += `impact_type=${encodeURIComponent(typeFilter)}&`;
      if (statusFilter) query += `evidence_status=${encodeURIComponent(statusFilter)}&`;
      if (severityFilter) query += `severity=${encodeURIComponent(severityFilter)}&`;

      const res = await fetch(query);
      if (res.ok) {
        setRecords(await res.json());
      }
    } catch (e) {
      console.error("Failed to fetch impact records:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchWarnings = async () => {
    try {
      const res = await fetch(`${API_URL}/api/impacts/warnings`);
      if (res.ok) setWarningCount((await res.json()).length);
    } catch (_) {
      setWarningCount(0);
    }
  };

  const fetchOfficialSources = async () => {
    try {
      const res = await fetch(`${API_URL}/api/impacts/evidence-sources`);
      if (res.ok) setOfficialSources(await res.json());
    } catch (_) {
      setOfficialSources([]);
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchWarnings();
    fetchOfficialSources();
  }, [zoneFilter, typeFilter, statusFilter, severityFilter]);

  const handleCsvImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setImportMessage('Importing and validating rows…');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_URL}/api/impacts/import/csv`, { method: 'POST', body: formData });
      const result = await res.json();
      setImportMessage(result.status === 'SUCCESS'
        ? `${result.imported_records_count} records imported. Verify every source before using them as evidence.`
        : `Import needs correction: ${(result.validation_errors || []).join(' ')}`);
      if (result.status === 'SUCCESS') fetchRecords();
    } catch (_) {
      setImportMessage('Could not import the file. Confirm the API is running and use the catalogue CSV template.');
    }
    event.target.value = '';
  };

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    setEvalResult(null);
    try {
      const warningRes = await fetch(`${API_URL}/api/impacts/warnings`);
      const warnings = warningRes.ok ? await warningRes.json() : [];
      const res = await fetch(`${API_URL}/api/impacts/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: "2015-01-01T00:00:00Z",
          end_time: "2025-12-31T23:59:59Z",
          spatial_radius_km: 5.0,
          target_zone: zoneFilter || null,
          target_impact_type: typeFilter || null,
          warnings
        })
      });
      if (res.ok) {
        setEvalResult(await res.json());
      }
    } catch (e) {
      console.error("Evaluation failed", e);
    } finally {
      setEvalLoading(false);
    }
  };

  const getEvidenceBadge = (status) => {
    switch (status) {
      case 'historical_real':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">HISTORICAL REAL</span>;
      case 'proxy':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-800 border border-blue-300">PROXY / DERIVED</span>;
      case 'synthetic':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800 border border-amber-300">SYNTHETIC TEST</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-300">UNVERIFIED</span>;
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'critical':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-100 text-red-800 border border-red-200">CRITICAL</span>;
      case 'high':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-orange-100 text-orange-800 border border-orange-200">HIGH</span>;
      case 'moderate':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-yellow-100 text-yellow-800 border border-yellow-200">MODERATE</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">LOW</span>;
    }
  };

  const getConfidenceDisplay = (record, detailed = false) => {
    if (record.evidence_status === 'synthetic') {
      return detailed
        ? <span className="font-semibold text-amber-800">Source needed — add a traceable official record</span>
        : <span title="Add a traceable source before assigning evidence confidence." className="inline-flex rounded border border-amber-300 bg-amber-50 px-2 py-0.5 font-sans text-[10px] font-bold uppercase text-amber-800">Add source</span>;
    }
    if (record.confidence === null || record.confidence === undefined) {
      return <span className="text-slate-500">Not assessed</span>;
    }
    return `${(record.confidence * 100).toFixed(detailed ? 1 : 0)}%`;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fadeIn pb-12 font-sans">
      
      {/* 1. Header Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-indigo-200">
              Phase 1 — Impact Provenance Engine
            </span>
            <span className="text-xs text-slate-500 font-mono">Greater Chennai Corporation Limits</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Database className="h-6 w-6 text-indigo-600" />
            Historical Urban Impact Catalogue
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Curate traceable impact evidence, inspect source provenance, and validate exported warnings against verified historical records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setEvidenceGuideOpen(true)}
            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
          >
            <BookOpen className="h-4 w-4" /> Add real evidence
          </button>
          <button
            onClick={() => setEvalModal(true)}
            className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
          >
            <ShieldCheck className="h-4 w-4" />
            Warning Impact Validation
          </button>
          
          <a
            href={`${API_URL}/api/research-operations/templates/impact_catalogue`}
            download
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition border border-slate-200 flex items-center gap-1.5"
          >
            <Download className="h-4 w-4" /> CSV template
          </a>

          <label className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition border border-slate-200 flex items-center gap-1.5 cursor-pointer">
            <Upload className="h-4 w-4" /> Import evidence CSV
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={handleCsvImport} />
          </label>

          <button
            onClick={fetchRecords}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition border border-slate-200"
            title="Refresh records"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </div>

      {importMessage && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-xs text-indigo-900">
          {importMessage}
        </div>
      )}

      {/* 2. Scientific Disclaimer Banner */}
      <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex items-start gap-3 text-xs text-blue-900">
        <Info className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Evidence confidence is source-based: </span>
          A percentage is shown only after a curator links an event to a traceable record. Use <strong className="text-emerald-700">Add real evidence</strong> to start from official source channels. Demonstration scenarios stay separate from historical evidence.
        </div>
      </div>

      {/* 3. Filters Ribbon */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div>
          <label className="block text-slate-500 font-bold mb-1">Impact Type</label>
          <select 
            value={typeFilter} 
            onChange={e => setTypeFilter(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800"
          >
            <option value="">All Impact Types</option>
            <option value="waterlogging">Waterlogging</option>
            <option value="road_closure">Road Closure</option>
            <option value="flood_extent">Flood Extent</option>
            <option value="reservoir_overflow">Reservoir Overflow</option>
            <option value="power_outage">Power Outage</option>
            <option value="hospital_access_disruption">Hospital Access Disruption</option>
            <option value="drainage_failure">Drainage Failure</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-500 font-bold mb-1">Evidence Status</label>
          <select 
            value={statusFilter} 
            onChange={e => setStatusFilter(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800"
          >
            <option value="">All Evidence Classes</option>
            <option value="historical_real">Historical Real</option>
            <option value="proxy">Proxy / Derived</option>
            <option value="synthetic">Synthetic Test</option>
            <option value="unverified">Unverified</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-500 font-bold mb-1">Severity</label>
          <select 
            value={severityFilter} 
            onChange={e => setSeverityFilter(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="moderate">Moderate</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-500 font-bold mb-1">Zone Filter</label>
          <input 
            type="text" 
            placeholder="e.g. Zone 13 or Adyar" 
            value={zoneFilter}
            onChange={e => setZoneFilter(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800"
          />
        </div>
      </div>

      {/* 4. Catalogue Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center text-xs font-semibold text-slate-600">
          <span>Displaying <strong>{records.length}</strong> Catalogue records</span>
          <span className="text-slate-400 font-normal">Click any record to inspect verifiable source provenance</span>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
            <RefreshCw className="h-6 w-6 text-indigo-500 animate-spin" />
            <span className="text-xs font-bold">Querying municipal impact records...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="text-[10px] font-bold text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-5 py-3.5">Event ID</th>
                  <th className="px-5 py-3.5">Start Timestamp</th>
                  <th className="px-5 py-3.5">Zone & Coordinates</th>
                  <th className="px-5 py-3.5">Impact Category</th>
                  <th className="px-5 py-3.5">Severity</th>
                  <th className="px-5 py-3.5">Evidence Status</th>
                  <th className="px-5 py-3.5">Evidence Confidence</th>
                  <th className="px-5 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans text-xs">
                {records.length > 0 ? (
                  records.map((r) => (
                    <tr 
                      key={r.id || r.event_id} 
                      onClick={() => setSelectedRecord(r)}
                      className="hover:bg-slate-50/80 cursor-pointer transition"
                    >
                      <td className="px-5 py-3.5 font-bold font-mono text-indigo-700">{r.event_id}</td>
                      <td className="px-5 py-3.5 text-slate-600">
                        {new Date(r.start_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="font-bold text-slate-800 block">{r.zone}</span>
                        <span className="text-[10px] font-mono text-slate-400">{r.latitude.toFixed(4)}°N, {r.longitude.toFixed(4)}°E</span>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-slate-700 capitalize">
                        {r.impact_type.replace(/_/g, ' ')}
                      </td>
                      <td className="px-5 py-3.5">{getSeverityBadge(r.severity)}</td>
                      <td className="px-5 py-3.5">{getEvidenceBadge(r.evidence_status)}</td>
                      <td className="px-5 py-3.5 font-mono font-bold text-slate-700">{getConfidenceDisplay(r)}</td>
                      <td className="px-5 py-3.5 text-right">
                        <span className="text-indigo-600 font-bold hover:underline inline-flex items-center gap-1">
                          Inspect <ChevronRight className="h-3 w-3" />
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-slate-400">
                      No documented impact events matched the selected filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {evidenceGuideOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] border border-slate-200 shadow-2xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-start gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Evidence intake workflow</div>
                <h3 className="font-bold text-lg text-slate-900 mt-1">Turn a source into defensible evidence</h3>
                <p className="text-xs text-slate-500 mt-1">This workflow prevents a source link, a model result, or a demonstration scenario from being mistaken for a verified impact observation.</p>
              </div>
              <button onClick={() => setEvidenceGuideOpen(false)} className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 overflow-y-auto space-y-5 text-xs">
              <ol className="grid sm:grid-cols-2 gap-3">
                {[
                  ['1', 'Choose an official source', 'Start with a report or authorised record; retain its permanent URL and access date.'],
                  ['2', 'Extract the exact observation', 'Record the event date, location, impact type, severity evidence and report page or reference ID.'],
                  ['3', 'Corroborate when possible', 'Pair impact evidence with IMD/CWC drivers or a second independent authorised source.'],
                  ['4', 'Import and review', 'Use the CSV template, assign confidence only after review, then run warning-impact validation.'],
                ].map(([number, title, description]) => (
                  <li key={number} className="rounded-xl border border-slate-200 bg-slate-50 p-3 flex gap-3">
                    <span className="h-6 w-6 shrink-0 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center font-black">{number}</span>
                    <div><div className="font-bold text-slate-800">{title}</div><p className="text-slate-500 mt-0.5 leading-relaxed">{description}</p></div>
                  </li>
                ))}
              </ol>
              <div>
                <div className="flex items-center gap-2 font-bold text-slate-800 mb-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Official source starting points</div>
                <div className="space-y-2">
                  {officialSources.length ? officialSources.map((source) => (
                    <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer" className="block rounded-xl border border-slate-200 p-3 hover:border-indigo-300 hover:bg-indigo-50/40 transition">
                      <div className="font-bold text-indigo-700 flex items-center justify-between gap-3">{source.name}<ExternalLink className="h-3.5 w-3.5 shrink-0" /></div>
                      <div className="text-[10px] text-slate-500 mt-1">{source.organisation} · {source.use_for}</div>
                      <div className="text-[10px] text-amber-800 mt-1.5">Curator rule: {source.record_rule}</div>
                    </a>
                  )) : <p className="text-slate-500">Source directory is unavailable. Check that the local API is running, then refresh this page.</p>}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                <a href={`${API_URL}/api/research-operations/templates/impact_catalogue`} download className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition inline-flex items-center gap-1.5"><Download className="h-4 w-4" /> Download CSV template</a>
                <label className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold transition border border-slate-200 inline-flex items-center gap-1.5 cursor-pointer"><Upload className="h-4 w-4" /> Import reviewed evidence<input type="file" accept=".csv,text/csv" className="hidden" onChange={handleCsvImport} /></label>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. Detail Drawer Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
              <div>
                <span className="text-[10px] font-bold text-indigo-700 font-mono uppercase">{selectedRecord.event_id}</span>
                <h3 className="font-bold text-base text-slate-900 capitalize mt-0.5">
                  {selectedRecord.impact_type.replace(/_/g, ' ')} Incident
                </h3>
              </div>
              <button 
                onClick={() => setSelectedRecord(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Administrative Zone</span>
                  <span className="font-bold text-slate-800">{selectedRecord.zone}</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Evidence Status</span>
                  <div>{getEvidenceBadge(selectedRecord.evidence_status)}</div>
                </div>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Onset Time:</span>
                  <span className="font-mono text-slate-800">{new Date(selectedRecord.start_time).toUTCString()}</span>
                </div>
                {selectedRecord.end_time && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolved Time:</span>
                    <span className="font-mono text-slate-800">{new Date(selectedRecord.end_time).toUTCString()}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-500">GPS Coordinates:</span>
                  <span className="font-mono text-slate-800">{selectedRecord.latitude}°N, {selectedRecord.longitude}°E</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Evidence Confidence:</span>
                  <span className="font-mono font-bold text-indigo-700">{getConfidenceDisplay(selectedRecord, true)}</span>
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Event Field Notes:</span>
                <p className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-slate-600 leading-relaxed">
                  {selectedRecord.notes || "No additional engineering commentary provided."}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="font-bold text-slate-700 block mb-1">Verifiable Citation / Provenance:</span>
                <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="font-semibold text-slate-800">{selectedRecord.source_name}</span>
                  {selectedRecord.source_url && (
                    <a 
                      href={selectedRecord.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1"
                    >
                      Source Document <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. Evaluation Modal */}
      {evalModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-indigo-600" />
                  Warning vs Ground-Truth Impact Alignment Test
                </h3>
                <p className="text-xs text-slate-500">Evaluates empirical lead time, false alarm rate, and F1-score</p>
              </div>
              <button 
                onClick={() => setEvalModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <p className="text-slate-600 leading-relaxed">
                This utility evaluates exported model-run warnings against curated impact labels. There are currently <strong>{warningCount}</strong> warnings in the local ledger. Only <strong>HISTORICAL REAL</strong> records with a traceable source can contribute to empirical scores.
              </p>

              <button
                onClick={handleRunEvaluation}
                disabled={evalLoading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-sm transition flex items-center justify-center gap-2"
              >
                {evalLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                {evalLoading ? "Matching Spatiotemporal Windows..." : "Execute Alignment Evaluation"}
              </button>

              {evalResult && (
                <div className="mt-4 p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                    <span className="font-bold text-slate-800">Status: {evalResult.status}</span>
                    <span className="text-[10px] font-mono text-slate-500">{evalResult.provenance}</span>
                  </div>

                  {evalResult.status === "EVALUATED" ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono">
                      <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                        <span className="text-[9px] text-slate-500 block uppercase font-sans">Detection</span>
                        <span className="text-base font-black text-emerald-600">{(evalResult.event_detection_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                        <span className="text-[9px] text-slate-500 block uppercase font-sans">Mean Lead Time</span>
                        <span className="text-base font-black text-indigo-600">{evalResult.warning_lead_time_hours_mean}h</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                        <span className="text-[9px] text-slate-500 block uppercase font-sans">Precision</span>
                        <span className="text-base font-black text-slate-800">{evalResult.precision}</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                        <span className="text-[9px] text-slate-500 block uppercase font-sans">F1-Score</span>
                        <span className="text-base font-black text-slate-800">{evalResult.f1_score}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-amber-50 text-amber-800 rounded-lg text-xs">
                      {evalResult.evidence_note}
                    </div>
                  )}

                  <p className="text-[10px] text-slate-500 italic mt-2">
                    {evalResult.evidence_note}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
