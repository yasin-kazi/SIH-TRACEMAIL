import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getCase } from '../api/cases';
import { useApiResource } from '../api/useApiResource';

export default function AnalysisProgress() {
  const { caseId = '' } = useParams(); const navigate = useNavigate();
  const { data: investigation, loading, error } = useApiResource(() => getCase(caseId), caseId);
  useEffect(() => { if (investigation?.analysisStatus === 'completed') { const timer = setTimeout(() => navigate(`/case/${caseId}/overview`), 700); return () => clearTimeout(timer); } }, [investigation, caseId, navigate]);
  const stages = ['Receiving evidence', 'Parsing email', 'Analyzing authentication', 'Analyzing identity', 'Analyzing infrastructure', 'Calculating risk', 'Preparing investigation'];
  return <div className="min-h-screen px-6 py-12 max-w-xl mx-auto"><h1 className="font-headline-lg text-on-surface">Preparing Investigation</h1><p className="text-on-surface-variant mt-2">{loading ? 'Checking completed analysis…' : error ? `Unable to open the investigation: ${error}` : `Analysis completed for Case #${investigation?.number}. Opening workspace…`}</p><div className="mt-8 space-y-3">{stages.map((stage) => <div key={stage} className="flex gap-3 text-on-surface-variant"><span className="material-symbols-outlined text-tertiary">check_circle</span>{stage}</div>)}</div></div>;
}
