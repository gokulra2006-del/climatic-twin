import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, AlertTriangle, FileCheck, CheckCircle2, XCircle, Clock, 
  Search, Filter, ExternalLink, Download, Upload, FileText, ChevronRight, 
  Layers, Database, ArrowRight, BookOpen, Hash, Copy, Check, Info, 
  HelpCircle, Sparkles, RefreshCw, X, ShieldAlert, Award
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function EvidenceReviewDashboard({ onNavigateToCatalogue }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); // ALL, HISTORICAL_REAL, UNDER_REVIEW, SYNTHETIC, REJECTED
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [orgFilter, setOrgFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [zoneFilter, setZoneFilter] = useState('');
  const [minConfidenceFilter, setMinConfidenceFilter] = useState('');

  // Modals & Drawers
  const [reviewDrawerOpen, setReviewDrawerOpen] = useState(false);
  const [evidenceCardModal, setEvidenceCardModal] = useState(false);
  const [evidenceCardData, setEvidenceCardData] = useState(null);
  const [cardCopied, setCardCopied] = useState(false);
  const [uploadModal, setUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [sourcesModal, setSourcesModal] = useState(false);
  const [sourcesList, setSourcesList] = useState([]);
  const [validationReadiness, setValidationReadiness] = useState(null);
  const [evalModal, setEvalModal] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  // Review submission state
  const [reviewerName, setReviewerName] = useState('Dr. S. Ramanathan (Senior Hydrologist)');
  const [reviewDecision, setReviewDecision] = useState('approved_historical_real');
  const [reviewNotes, setReviewNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState('');

  const fetchRecords = async () => {
    setLoading(true);
    try {
      let query = `${API_URL}/api/impacts/?`;
      if (statusFilter) query += `evidence_status=${encodeURIComponent(statusFilter)}&`;
      if (orgFilter) query += `source_org=${encodeURIComponent(orgFilter)}&`;
      if (typeFilter) query += `impact_type=${encodeURIComponent(typeFilter)}&`;
      if (yearFilter) query += `year=${encodeURIComponent(yearFilter)}&`;
      if (zoneFilter) query += `zone=${encodeURIComponent(zoneFilter)}&`;
      if (minConfidenceFilter) query += `min_confidence=${encodeURIComponent(minConfidenceFilter)}&`;

      const res = await fetch(query);
      if (res.ok) {
        setRecords(await res.json());
      }
    } catch (e) {
      console.error("Failed to load records:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchValidationReadiness = async () => {
    try {
      const res = await fetch(`${API_URL}/api/impacts/validation-readiness`);
      if (res.ok) {
        setValidationReadiness(await res.json());
      }
    } catch (e) {
      console.error("Failed to load validation readiness:", e);
    }
  };

  const fetchOfficialSources = async () => {
    try {
      const res = await fetch(`${API_URL}/api/impacts/evidence-sources`);
      if (res.ok) {
        setSourcesList(await res.json());
      }
    } catch (e) {
      console.error("Failed to load sources:", e);
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchValidationReadiness();
    fetchOfficialSources();
  }, [statusFilter, orgFilter, typeFilter, yearFilter, zoneFilter, minConfidenceFilter]);

  const handleOpenReview = (record) => {
    setSelectedRecord(record);
    setReviewDecision(record.evidence_status === 'under_review' ? 'approved_historical_real' : record.review_decision || 'under_review');
    setReviewNotes(record.review_notes || '');
    setReviewFeedback('');
    setReviewDrawerOpen(true);
  };

  const handleSubmitReview = async () => {
    if (!selectedRecord) return;
    setSubmittingReview(true);
    setReviewFeedback('');
    try {
      const res = await fetch(`${API_URL}/api/impacts/${selectedRecord.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_name: reviewerName,
          decision: reviewDecision,
          review_notes: reviewNotes
        })
      });
      const data = await res.json();
      if (res.ok) {
        setReviewFeedback('Review successfully recorded and evidence confidence recalculated.');
        setSelectedRecord(data);
        fetchRecords();
        fetchValidationReadiness();
      } else {
        setReviewFeedback(`Review rejected: ${data.detail || 'Integrity violation'}`);
      }
    } catch (e) {
      setReviewFeedback(`Network error submitting review: ${e.message}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleOpenEvidenceCard = async (record) => {
    try {
      const res = await fetch(`${API_URL}/api/impacts/${record.id}/evidence-card`);
      if (res.ok) {
        setEvidenceCardData(await res.json());
        setCardCopied(false);
        setEvidenceCardModal(true);
      }
    } catch (e) {
      console.error("Failed to fetch evidence card:", e);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedRecord) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('record_id', selectedRecord.id.toString());
      const res = await fetch(`${API_URL}/api/impacts/upload-attachment`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setUploadResult(data);
        fetchRecords();
        if (selectedRecord) {
          setSelectedRecord(prev => ({ ...prev, document_hash: data.document_hash, attachment_filename: data.filename }));
        }
      }
    } catch (e) {
      console.error("File upload failed:", e);
    } finally {
      setUploading(false);
    }
  };

  const handleRunEmpiricalEvaluation = async () => {
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
          end_time: "2026-12-31T23:59:59Z",
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

  // KPI calculations
  const verifiedCount = records.filter(r => r.evidence_status === 'historical_real').length;
  const underReviewCount = records.filter(r => r.evidence_status === 'under_review').length;
  const syntheticCount = records.filter(r => r.evidence_status === 'synthetic').length;
  const unverifiedCount = records.filter(r => r.evidence_status === 'unverified').length;
  const readyForValidation = records.filter(r => r.evidence_status === 'historical_real' && (r.observed_flood_extent_sqkm > 0 || r.observed_flood_depth_m > 0)).length;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'historical_real':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-emerald-100 text-emerald-800 border border-emerald-300"><CheckCircle2 className="h-3 w-3" /> Historical Real</span>;
      case 'under_review':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-amber-100 text-amber-900 border border-amber-300"><Clock className="h-3 w-3" /> Under Review</span>;
      case 'proxy':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-blue-100 text-blue-800 border border-blue-300"><Layers className="h-3 w-3" /> Proxy / Derived</span>;
      case 'synthetic':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-purple-100 text-purple-800 border border-purple-300"><Sparkles className="h-3 w-3" /> Synthetic Demo</span>;
      case 'rejected':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-rose-100 text-rose-800 border border-rose-300"><XCircle className="h-3 w-3" /> Rejected</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold whitespace-nowrap bg-slate-100 text-slate-700 border border-slate-300"><HelpCircle className="h-3 w-3" /> Unverified</span>;
    }
  };

  const getScoreBadge = (record) => {
    const rubric = record.rubric;
    if (!rubric || record.evidence_status === 'synthetic') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-amber-300 bg-amber-50 text-[11px] font-bold text-amber-800">
          Add verified source
        </span>
      );
    }
    const score = rubric.total_score ?? 0;
    let color = "bg-rose-50 text-rose-800 border-rose-200";
    if (score >= 80) color = "bg-emerald-50 text-emerald-800 border-emerald-300";
    else if (score >= 50) color = "bg-blue-50 text-blue-800 border-blue-300";
    else if (score >= 25) color = "bg-amber-50 text-amber-800 border-amber-300";

    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md border font-mono text-xs font-bold ${color}`}>
        <Award className="h-3 w-3" />
        {score}/100
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-16 font-sans">
      
      {/* 1. Header & Navigation Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-emerald-50 text-emerald-700 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-emerald-200">
              Research Integrity & Traceability System
            </span>
            <span className="text-xs text-slate-500 font-mono">GCC Basin Spatial Limits</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2.5">
            <ShieldCheck className="h-7 w-7 text-emerald-600" />
            Evidence Review & Confidence Dashboard
          </h1>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl">
            Audit ground-truth urban impacts against transparent 0–100 confidence rubrics. Maintain scientific provenance with official government citations, SHA-256 document hashing, and peer-reviewed empirical validation.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {onNavigateToCatalogue && (
            <button
              onClick={onNavigateToCatalogue}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition border border-slate-200 flex items-center gap-1.5 shadow-sm"
            >
              <Database className="h-4 w-4 text-indigo-600" /> Impact Catalogue
            </button>
          )}
          <button
            onClick={() => setSourcesModal(true)}
            className="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-bold transition border border-indigo-200 flex items-center gap-1.5"
          >
            <BookOpen className="h-4 w-4" /> Official Sources ({sourcesList.length})
          </button>
          <button
            onClick={() => setEvalModal(true)}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
          >
            <Award className="h-4 w-4" /> Empirical Validation
          </button>
          <a
            href={`${API_URL}/api/impacts/export/appendix`}
            className="px-3.5 py-2 bg-slate-900 hover:bg-black text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
            download
          >
            <Download className="h-4 w-4" /> Export LaTeX Table
          </a>
        </div>
      </div>

      {/* 2. Evidence Quality KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Verified Real</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{verifiedCount}</div>
          <div className="text-[11px] text-emerald-700 font-medium mt-1">Certified for paper claims</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Under Review</span>
            <Clock className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{underReviewCount}</div>
          <div className="text-[11px] text-amber-700 font-medium mt-1">Awaiting curator signoff</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Synthetic Demo</span>
            <Sparkles className="h-4 w-4 text-purple-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{syntheticCount}</div>
          <div className="text-[11px] text-purple-700 font-medium mt-1">Strictly excluded from metrics</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Hydraulic Ready</span>
            <Layers className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">{readyForValidation}</div>
          <div className="text-[11px] text-blue-700 font-medium mt-1">With extent/depth bounds</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Action Needed</span>
            <AlertTriangle className="h-4 w-4 text-rose-500" />
          </div>
          <div className="text-2xl font-black text-slate-900">{underReviewCount + unverifiedCount}</div>
          <div className="text-[11px] text-rose-700 font-medium mt-1">Pending documentation</div>
        </div>
      </div>

      {/* 3. Next Best Action & Scientific Integrity Rules Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-gradient-to-r from-emerald-50 via-teal-50 to-white p-5 rounded-2xl border border-emerald-200 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-emerald-600 text-white rounded-xl shadow-sm">
              <FileCheck className="h-5 w-5" />
            </div>
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900">Curator Next Best Actions</h3>
                <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200">
                  Publication Quality Checklist
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {underReviewCount > 0 
                  ? `There are ${underReviewCount} records awaiting curator review. Inspect source passages, check location precision, and certify as Historical Real.`
                  : "All current official records are reviewed. Prioritize importing observed satellite SAR flood extent masks (e.g. Sentinel-1 EMS) to achieve 2D hydraulic validation readiness."}
              </p>
              <div className="flex items-center gap-3 pt-1 text-xs font-semibold text-emerald-800">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> 0–100 Evidence Rubric active
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" /> Synthetic records strictly excluded from scoring
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Validation Readiness Card */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold uppercase text-slate-500">2-D Hydraulic Readiness</span>
              {validationReadiness?.hydraulic_2d_validation_ready ? (
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded text-[10px] font-bold">READY</span>
              ) : (
                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-300 rounded text-[10px] font-bold">SCENARIO ONLY</span>
              )}
            </div>
            <p className="text-xs text-slate-600 leading-normal">
              {validationReadiness?.limitation_warning || "Assessing empirical observed datasets..."}
            </p>
          </div>
          <div className="pt-2 text-[11px] font-semibold text-slate-500">
            Observed extents: {validationReadiness?.observed_extent_records_count || 0} | Depths: {validationReadiness?.observed_depth_records_count || 0}
          </div>
        </div>
      </div>

      {/* 4. Multi-Criteria Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
            <Filter className="h-4 w-4 text-indigo-600" />
            <span>Filter Evidence Records</span>
          </div>
          {(statusFilter || orgFilter || typeFilter || yearFilter || zoneFilter || minConfidenceFilter) && (
            <button
              onClick={() => {
                setStatusFilter('');
                setOrgFilter('');
                setTypeFilter('');
                setYearFilter('');
                setZoneFilter('');
                setMinConfidenceFilter('');
              }}
              className="text-xs text-rose-600 hover:text-rose-700 font-semibold"
            >
              Reset Filters
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">All Evidence Statuses</option>
            <option value="historical_real">Historical Real</option>
            <option value="under_review">Under Review</option>
            <option value="proxy">Proxy / Derived</option>
            <option value="synthetic">Synthetic Demo</option>
            <option value="unverified">Unverified</option>
            <option value="rejected">Rejected</option>
          </select>

          <select
            value={orgFilter}
            onChange={(e) => setOrgFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">All Authorities</option>
            <option value="Central Water Commission">Central Water Commission (CWC)</option>
            <option value="India Meteorological Department">India Meteorological Dept (IMD)</option>
            <option value="Greater Chennai Corporation">Greater Chennai Corp (GCC)</option>
            <option value="Tamil Nadu State Disaster Management Authority">TNSDMA</option>
            <option value="Water Resources Department">Water Resources Dept (WRD)</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">All Impact Types</option>
            <option value="flood_extent">Flood Extent</option>
            <option value="waterlogging">Waterlogging</option>
            <option value="reservoir_overflow">Reservoir Overflow</option>
            <option value="power_outage">Power Outage</option>
            <option value="road_closure">Road Closure</option>
            <option value="drainage_failure">Drainage Failure</option>
          </select>

          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">All Years</option>
            <option value="2015">2015 (Historical Extreme)</option>
            <option value="2023">2023 (Cyclone Michaung)</option>
            <option value="2024">2024</option>
          </select>

          <select
            value={zoneFilter}
            onChange={(e) => setZoneFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">All Zones</option>
            <option value="Zone 13 - Adyar">Zone 13 - Adyar</option>
            <option value="Zone 14 - Perungudi">Zone 14 - Perungudi</option>
            <option value="Zone 11 - Valasaravakkam">Zone 11 - Valasaravakkam</option>
            <option value="Zone 5 - Royapuram">Zone 5 - Royapuram</option>
            <option value="West Reservoirs">West Reservoirs</option>
          </select>

          <select
            value={minConfidenceFilter}
            onChange={(e) => setMinConfidenceFilter(e.target.value)}
            className="p-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
          >
            <option value="">Any Confidence</option>
            <option value="0.9">Score &gt;= 90/100</option>
            <option value="0.75">Score &gt;= 75/100</option>
            <option value="0.5">Score &gt;= 50/100</option>
          </select>
        </div>
      </div>

      {/* 5. Main Records Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-800">Impact Evidence Ledger</span>
            <span className="text-xs text-slate-500 font-mono">({records.length} records)</span>
          </div>
          <span className="text-[11px] text-slate-500 italic">
            Click any row to inspect rubric breakdown, citations, and curator controls.
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-indigo-600 mb-2" />
            Loading verified evidence catalogue...
          </div>
        ) : records.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No records matched the selected criteria. Adjust filters or import new evidence rows.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                  <th className="p-3 pl-4">Event ID / Date</th>
                  <th className="p-3">Zone & Location</th>
                  <th className="p-3">Impact Type</th>
                  <th className="p-3">Primary Authority</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Confidence Rubric</th>
                  <th className="p-3">Reviewer</th>
                  <th className="p-3 text-right pr-4">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {records.map((r) => (
                  <tr 
                    key={r.id || r.event_id} 
                    className="hover:bg-indigo-50/40 transition cursor-pointer group"
                    onClick={() => handleOpenReview(r)}
                  >
                    <td className="p-3 pl-4">
                      <div className="font-mono font-bold text-slate-900 group-hover:text-indigo-600 transition">
                        {r.event_id}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {r.start_time?.slice(0, 10)} {r.exact_time_verified && <span className="text-emerald-700 font-semibold">• Exact time</span>}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="font-semibold text-slate-800">{r.zone}</div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {r.latitude?.toFixed(4)}, {r.longitude?.toFixed(4)}
                        {r.location_precision_type && ` (${r.location_precision_type.replace('_', ' ')})`}
                      </div>
                    </td>
                    <td className="p-3">
                      <span className="capitalize font-medium text-slate-800">
                        {r.impact_type?.replace('_', ' ')}
                      </span>
                      <div className="text-[10px] uppercase font-bold text-slate-500 mt-0.5">
                        Severity: {r.severity}
                      </div>
                    </td>
                    <td className="p-3 max-w-[200px] truncate" title={r.source_name}>
                      <div className="font-medium text-slate-900 truncate">
                        {r.source_org || r.source_name}
                      </div>
                      {r.source_url ? (
                        <a 
                          href={r.source_url} 
                          target="_blank" 
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()} 
                          className="text-[11px] text-indigo-600 hover:underline flex items-center gap-1 mt-0.5"
                        >
                          <ExternalLink className="h-3 w-3" /> Report Link
                        </a>
                      ) : (
                        <span className="text-[10px] text-amber-700 font-medium">No source URL</span>
                      )}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {getStatusBadge(r.evidence_status)}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {getScoreBadge(r)}
                    </td>
                    <td className="p-3 text-[11px] text-slate-600">
                      {r.reviewer_name ? (
                        <div>
                          <span className="font-semibold text-slate-800">{r.reviewer_name}</span>
                          <div className="text-[10px] text-slate-400">{r.review_timestamp ? r.review_timestamp.slice(0, 10) : ''}</div>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Not reviewed</span>
                      )}
                    </td>
                    <td className="p-3 text-right pr-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleOpenEvidenceCard(r)}
                          title="View Exportable Evidence Card"
                          className="p-1.5 hover:bg-slate-200 text-slate-600 rounded-lg transition"
                        >
                          <FileText className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleOpenReview(r)}
                          className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-[11px] font-bold transition flex items-center gap-1"
                        >
                          Audit & Review <ChevronRight className="h-3 w-3" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 6. Review & Audit Drawer */}
      {reviewDrawerOpen && selectedRecord && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-2xl h-full shadow-2xl flex flex-col justify-between overflow-y-auto">
            
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded">
                    {selectedRecord.event_id}
                  </span>
                  {getStatusBadge(selectedRecord.evidence_status)}
                </div>
                <h2 className="text-lg font-black text-slate-900">
                  Evidence Audit & Confidence Breakdown
                </h2>
              </div>
              <button 
                onClick={() => setReviewDrawerOpen(false)} 
                className="p-2 hover:bg-slate-200 rounded-full transition"
              >
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="p-6 space-y-6 flex-1 text-xs">
              
              {/* Score Display Card */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Evidence Confidence Score</span>
                  {getScoreBadge(selectedRecord)}
                </div>
                <p className="text-xs text-slate-600">
                  {selectedRecord.rubric?.reason || "Calculated using transparent 5-criteria empirical confidence rubric."}
                </p>

                {/* Rubric Breakdown Grid */}
                {selectedRecord.rubric?.breakdown && (
                  <div className="space-y-2 pt-2 border-t border-slate-200">
                    <div className="text-[11px] font-bold text-slate-800 uppercase">Rubric Criteria Breakdown:</div>
                    
                    {/* Item 1 */}
                    <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                      <div>
                        <div className="font-semibold text-slate-800">1. Authoritative Primary Source (Max 25 pts)</div>
                        <div className="text-[11px] text-slate-500">{selectedRecord.rubric.breakdown.authoritative_primary_source?.evidence}</div>
                      </div>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${selectedRecord.rubric.breakdown.authoritative_primary_source?.points > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                        +{selectedRecord.rubric.breakdown.authoritative_primary_source?.points || 0} pts
                      </span>
                    </div>

                    {/* Item 2 */}
                    <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                      <div>
                        <div className="font-semibold text-slate-800">2. Exact Event Date/Time (Max 20 pts)</div>
                        <div className="text-[11px] text-slate-500">{selectedRecord.rubric.breakdown.exact_datetime?.evidence}</div>
                      </div>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${selectedRecord.rubric.breakdown.exact_datetime?.points > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                        +{selectedRecord.rubric.breakdown.exact_datetime?.points || 0} pts
                      </span>
                    </div>

                    {/* Item 3 */}
                    <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                      <div>
                        <div className="font-semibold text-slate-800">3. Precise Location / Coordinates &lt;= 500m (Max 20 pts)</div>
                        <div className="text-[11px] text-slate-500">{selectedRecord.rubric.breakdown.precise_location?.evidence}</div>
                      </div>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${selectedRecord.rubric.breakdown.precise_location?.points > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                        +{selectedRecord.rubric.breakdown.precise_location?.points || 0} pts
                      </span>
                    </div>

                    {/* Item 4 */}
                    <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                      <div>
                        <div className="font-semibold text-slate-800">4. Independent Corroborating Source (Max 20 pts)</div>
                        <div className="text-[11px] text-slate-500 truncate max-w-sm">{selectedRecord.rubric.breakdown.independent_corroborating_source?.evidence}</div>
                      </div>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${selectedRecord.rubric.breakdown.independent_corroborating_source?.points > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                        +{selectedRecord.rubric.breakdown.independent_corroborating_source?.points || 0} pts
                      </span>
                    </div>

                    {/* Item 5 */}
                    <div className="flex items-center justify-between p-2 rounded bg-white border border-slate-200">
                      <div>
                        <div className="font-semibold text-slate-800">5. Observed Physical Impact Measurement (Max 15 pts)</div>
                        <div className="text-[11px] text-slate-500">{selectedRecord.rubric.breakdown.observed_impact_measurement?.evidence}</div>
                      </div>
                      <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${selectedRecord.rubric.breakdown.observed_impact_measurement?.points > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-500'}`}>
                        +{selectedRecord.rubric.breakdown.observed_impact_measurement?.points || 0} pts
                      </span>
                    </div>
                  </div>
                )}

                {/* Missing Items */}
                {selectedRecord.rubric?.missing_items?.length > 0 && (
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-amber-900 space-y-1">
                    <div className="font-bold flex items-center gap-1.5 text-[11px]">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                      Missing Evidence Items to Reach Full Confidence:
                    </div>
                    <ul className="list-disc pl-5 text-[11px] space-y-0.5">
                      {selectedRecord.rubric.missing_items.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Source & Citation Details */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">Source Citation & Evidence Passage</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-slate-500 text-[11px]">Primary Organization:</span>
                    <div className="font-semibold text-slate-800">{selectedRecord.source_org || 'Not recorded'}</div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Access / Retrieval Date:</span>
                    <div className="font-semibold text-slate-800">{selectedRecord.access_date || 'N/A'}</div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Report Reference ID:</span>
                    <div className="font-mono text-slate-800">{selectedRecord.source_ref_id || 'N/A'}</div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px]">Page / Section Citation:</span>
                    <div className="font-semibold text-slate-800">{selectedRecord.report_page || 'N/A'}</div>
                  </div>
                </div>

                {selectedRecord.exact_passage && (
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[10px] font-bold text-slate-500 uppercase">Exact Official Source Passage:</span>
                    <p className="italic text-slate-700 mt-1">"{selectedRecord.exact_passage}"</p>
                  </div>
                )}

                {selectedRecord.source_url && (
                  <div>
                    <a
                      href={selectedRecord.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-1.5 font-semibold text-xs"
                    >
                      <ExternalLink className="h-3.5 w-3.5" /> View Primary Document ({selectedRecord.source_url})
                    </a>
                  </div>
                )}
              </div>

              {/* Document Hash & File Attachment */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                    <Hash className="h-4 w-4 text-slate-600" />
                    Cryptographic Document Hash (SHA-256)
                  </h4>
                  <label className="cursor-pointer px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 rounded text-[11px] font-bold text-slate-700 transition flex items-center gap-1">
                    <Upload className="h-3 w-3" /> Attach Source File
                    <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.png,.jpg,.jpeg" />
                  </label>
                </div>
                {uploading && <div className="text-indigo-600">Computing SHA-256 hash and uploading...</div>}
                {uploadResult && (
                  <div className="p-2 bg-emerald-50 border border-emerald-200 rounded text-emerald-800 text-[11px]">
                    Attached: {uploadResult.filename} ({uploadResult.file_size_bytes} bytes). SHA-256: {uploadResult.document_hash}
                  </div>
                )}
                {selectedRecord.document_hash ? (
                  <div className="p-2.5 bg-white rounded border border-slate-200 font-mono text-[10px] text-slate-700 break-all select-all">
                    {selectedRecord.document_hash}
                  </div>
                ) : (
                  <div className="text-slate-500 italic text-[11px]">
                    No cryptographic document hash stored. Upload supporting PDF to verify authenticity.
                  </div>
                )}
              </div>

              {/* Curator Review Decision Form */}
              <div className="p-5 bg-indigo-50/50 rounded-xl border border-indigo-200 space-y-4">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-indigo-600" />
                  Curator Decision & Research Certification
                </h4>

                {reviewFeedback && (
                  <div className={`p-3 rounded-lg border text-xs font-semibold ${reviewFeedback.includes('successfully') ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'}`}>
                    {reviewFeedback}
                  </div>
                )}

                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Reviewer Name & Role:</label>
                    <input
                      type="text"
                      value={reviewerName}
                      onChange={(e) => setReviewerName(e.target.value)}
                      className="w-full p-2 border border-slate-300 rounded-lg bg-white"
                      placeholder="e.g. Dr. S. Ramanathan (Senior Hydrologist)"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Reviewer Decision:</label>
                    <select
                      value={reviewDecision}
                      onChange={(e) => setReviewDecision(e.target.value)}
                      className="w-full p-2 border border-slate-300 rounded-lg bg-white font-medium"
                    >
                      <option value="approved_historical_real">Approve as Historical Real (Certified Evidence)</option>
                      <option value="under_review">Mark as Under Review (Needs Corroboration)</option>
                      <option value="revision_needed">Request Revision / Missing Citations</option>
                      <option value="rejected">Reject (Unverifiable or Non-Authoritative)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Audit Notes / Rationale:</label>
                    <textarea
                      rows={3}
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      className="w-full p-2 border border-slate-300 rounded-lg bg-white text-xs"
                      placeholder="Explain cross-referencing steps, gauge verification, or reason for rejection..."
                    />
                  </div>

                  <button
                    onClick={handleSubmitReview}
                    disabled={submittingReview}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition flex items-center justify-center gap-2 shadow-sm"
                  >
                    {submittingReview ? <RefreshCw className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                    Submit Curator Audit Decision
                  </button>
                </div>
              </div>

            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <button
                onClick={() => handleOpenEvidenceCard(selectedRecord)}
                className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-100 rounded-lg text-slate-700 font-semibold text-xs flex items-center gap-1.5"
              >
                <FileText className="h-4 w-4 text-slate-600" /> Export Evidence Card
              </button>
              <button
                onClick={() => setReviewDrawerOpen(false)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-bold text-xs"
              >
                Done
              </button>
            </div>

          </div>
        </div>
      )}

      {/* 7. Evidence Card Modal */}
      {evidenceCardModal && evidenceCardData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                <FileText className="h-5 w-5 text-indigo-600" />
                Paper Appendix Evidence Card: {evidenceCardData.event_id}
              </h3>
              <button onClick={() => setEvidenceCardModal(false)} className="p-1 hover:bg-slate-100 rounded">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-slate-700 mb-1">Markdown Representation:</div>
                <pre className="whitespace-pre-wrap font-mono text-[11px] text-slate-800 bg-white p-3 rounded border border-slate-200 select-all">
                  {evidenceCardData.markdown_card}
                </pre>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-slate-700 mb-1">LaTeX Table Snippet (IEEE / Journal):</div>
                <pre className="whitespace-pre-wrap font-mono text-[11px] text-slate-800 bg-white p-3 rounded border border-slate-200 select-all">
                  {evidenceCardData.latex_snippet}
                </pre>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(evidenceCardData.markdown_card);
                  setCardCopied(true);
                  setTimeout(() => setCardCopied(false), 2000);
                }}
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5"
              >
                {cardCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {cardCopied ? 'Copied to Clipboard!' : 'Copy Markdown Card'}
              </button>
              <button
                onClick={() => setEvidenceCardModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 8. Official Sources Modal */}
      {sourcesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-3xl w-full border border-slate-200 shadow-2xl p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-indigo-600" />
                  Official Evidence Source Registry
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Authorised government and municipal intake channels for Chennai Metropolitan Area.</p>
              </div>
              <button onClick={() => setSourcesModal(false)} className="p-1 hover:bg-slate-100 rounded">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            <div className="space-y-3 overflow-y-auto flex-1 text-xs">
              {sourcesList.map((src, idx) => (
                <div key={idx} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-bold text-slate-900 text-sm">{src.name}</div>
                      <div className="text-[11px] font-semibold text-emerald-800">{src.organisation}</div>
                    </div>
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-1 font-semibold text-xs"
                    >
                      <ExternalLink className="h-3.5 w-3.5" /> Official Portal
                    </a>
                  </div>
                  <p className="text-slate-700">{src.use_for}</p>
                  <div className="p-2 bg-amber-50/70 border border-amber-200/60 rounded text-[11px] text-amber-900">
                    <span className="font-bold">Record Intake Rule:</span> {src.record_rule}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setSourcesModal(false)}
                className="px-4 py-2 bg-slate-800 text-white rounded-xl text-xs font-bold"
              >
                Close Registry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 9. Real-Event Empirical Evaluation Modal */}
      {evalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl p-6 space-y-4 max-h-[90vh] flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Award className="h-5 w-5 text-emerald-600" />
                  Real-Event Model Warning Validation
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Strictly evaluates warnings against Historical Real records only. Excludes synthetic & proxy data.</p>
              </div>
              <button onClick={() => setEvalModal(false)} className="p-1 hover:bg-slate-100 rounded">
                <X className="h-5 w-5 text-slate-500" />
              </button>
            </div>

            <div className="space-y-4 overflow-y-auto flex-1 text-xs">
              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 text-xs">
                <strong>Publication Integrity Rule:</strong> Empirical performance metrics (F1, Precision, Recall, Lead Time, Brier Score) are computed exclusively against verified Historical Real events. Synthetic records are excluded.
              </div>

              <button
                onClick={handleRunEmpiricalEvaluation}
                disabled={evalLoading}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold transition flex items-center justify-center gap-2"
              >
                {evalLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                Run Strict Empirical Evaluation
              </button>

              {evalResult && (
                <div className="space-y-3 pt-2">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] text-slate-500 font-bold uppercase">Precision</div>
                      <div className="text-lg font-black text-slate-900">
                        {evalResult.precision !== null ? `${(evalResult.precision * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] text-slate-500 font-bold uppercase">Recall</div>
                      <div className="text-lg font-black text-slate-900">
                        {evalResult.recall !== null ? `${(evalResult.recall * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] text-slate-500 font-bold uppercase">F1-Score</div>
                      <div className="text-lg font-black text-slate-900">
                        {evalResult.f1_score !== null ? evalResult.f1_score.toFixed(3) : 'N/A'}
                      </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-center">
                      <div className="text-[10px] text-slate-500 font-bold uppercase">Brier Score</div>
                      <div className="text-lg font-black text-slate-900">
                        {evalResult.brier_score !== null ? evalResult.brier_score.toFixed(3) : 'N/A'}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                    <div><strong>Sample Size (N):</strong> {evalResult.sample_size_n} historical real events (Excluded {evalResult.excluded_synthetic_proxy_records} synthetic/proxy records).</div>
                    <div><strong>Mean Warning Lead Time:</strong> {evalResult.warning_lead_time_hours_mean ?? 0} hours</div>
                    <div><strong>False Alarms:</strong> {evalResult.false_alarms ?? 0}</div>
                  </div>

                  {evalResult.sample_size_warning && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-900 text-xs flex items-start gap-2">
                      <ShieldAlert className="h-4 w-4 text-rose-600 mt-0.5 shrink-0" />
                      <span>{evalResult.sample_size_warning}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setEvalModal(false)}
                className="px-4 py-2 bg-slate-800 text-white rounded-xl text-xs font-bold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
