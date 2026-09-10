import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Case } from '../types';
import { listCases, uploadEmail } from '../api/cases';
import { useApiResource } from '../api/useApiResource';

function CasesPage() {
  const navigate = useNavigate();
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { data: cases, loading, error } = useApiResource(listCases, 'cases');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setUploadError(null);
    try {
      const result = await uploadEmail(selectedFile);
      setAnalyzing(false);
      setShowUpload(false);
      setSelectedFile(null);
      navigate(`/case/${result.case_id}/analyzing`);
    } catch (err: any) {
      setUploadError(err.message ?? 'Upload failed');
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed left-0 top-0 h-full w-sidebar-width bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between pt-space-md pb-space-lg">
        <div className="flex flex-col">
          <div className="h-header-height px-space-md flex items-center justify-between">
            <div className="flex items-center gap-space-xs">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-[20px] text-on-primary">mail</span>
              </div>
              <span className="font-title-sm text-title-sm text-on-surface tracking-tight">TraceMail AI</span>
            </div>
            <span className="font-badge-label text-badge-label px-space-xs py-space-2xs rounded-full bg-surface-container-low text-primary">v2.4</span>
          </div>
          <nav className="flex flex-col gap-space-2xs px-space-xs mt-space-xs">
            <div className="flex items-center justify-between px-space-sm py-space-xs rounded-xl bg-primary-container text-on-primary font-title-sm">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-[20px]">cases</span>
                <span className="font-body-md text-body-md">Cases</span>
              </div>
              <span className="font-label-mono-sm text-label-mono-sm px-space-xs py-space-2xs rounded-full bg-on-primary/20 text-on-primary">
                {cases?.length ?? 0}
              </span>
            </div>
          </nav>
        </div>
        <div className="px-space-md">
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-space-sm w-full px-space-sm py-space-xs rounded-xl bg-primary-container text-on-primary hover:bg-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[20px]">add_circle</span>
            <span className="font-body-md text-body-md">New Investigation</span>
          </button>
        </div>
      </aside>

      <div className="ml-sidebar-width">
        <main className="p-space-xl">
          <div className="flex items-center justify-between mb-space-lg">
            <div className="flex flex-col gap-space-2xs">
              <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Investigation Cases</h1>
              <p className="font-body-sm text-body-sm text-on-surface-variant">Active forensic email investigations and triage queue</p>
            </div>
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-space-2xs px-space-md py-space-xs rounded-xl bg-primary text-on-primary hover:bg-primary-container shadow-sm font-title-sm text-body-sm transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">upload</span>
              <span>Upload .eml</span>
            </button>
          </div>

          {loading && <p className="text-on-surface-variant">Loading investigations…</p>}
          {error && <p className="text-error">Unable to load investigations: {error}</p>}
          {!loading && !error && cases?.length === 0 && <p className="text-on-surface-variant">No investigations yet. Upload an .eml to begin.</p>}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-space-md">{cases?.map((c) => <CaseCard key={c.id} caseData={c} onClick={() => navigate(`/case/${c.id}/overview`)} />)}</div>

          {showUpload && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-[4px]" onClick={() => !analyzing && setShowUpload(false)}>
              <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-lg w-full max-w-lg animate-fade-in" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-space-md">
                  <div className="flex items-center gap-space-sm">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                      <span className="material-symbols-outlined text-[24px] text-primary">upload_file</span>
                    </div>
                    <div>
                      <h2 className="font-title-sm text-title-sm text-on-surface">New Investigation</h2>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">Choose how to provide an email</p>
                    </div>
                  </div>
                </div>

                {!selectedFile ? (<>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
                    <button disabled className="p-3 rounded-xl bg-surface-container-low text-on-surface-variant text-left">Connect Gmail<br/><small>Coming soon</small></button>
                    <button disabled className="p-3 rounded-xl bg-surface-container-low text-on-surface-variant text-left">Microsoft 365<br/><small>Coming soon</small></button>
                    <button disabled className="p-3 rounded-xl bg-surface-container-low text-on-surface-variant text-left">Paste headers<br/><small>Coming soon</small></button>
                  </div>
                  <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-outline-variant rounded-xl cursor-pointer hover:border-primary hover:bg-primary/5 transition-all">
                    <span className="material-symbols-outlined text-[40px] text-outline mb-2">cloud_upload</span>
                    <span className="font-body-md text-body-md text-on-surface-variant">Drop .eml file here or click to browse</span>
                    <span className="font-body-sm text-body-sm text-outline mt-1">RFC-822 email format only</span>
                    <input type="file" className="hidden" accept=".eml" onChange={handleFileSelect} />
                  </label></>
                ) : (
                  <div className="flex flex-col gap-space-md">
                    <div className="bg-surface-container-low rounded-xl p-space-md flex items-center gap-space-md">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <span className="material-symbols-outlined text-[20px] text-primary">description</span>
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="font-title-sm text-title-sm text-on-surface truncate">{selectedFile.name}</span>
                        <div className="flex items-center gap-space-xs text-on-surface-variant font-label-mono-sm text-label-mono-sm">
                          <span>{(selectedFile.size / 1024).toFixed(1)} KB</span>
                          <span>·</span>
                          <span>SHA-256: computing...</span>
                        </div>
                      </div>
                    </div>

                    {analyzing ? (
                      <div className="flex flex-col items-center gap-space-md py-space-md">
                        <div className="w-full bg-surface-container-high h-2 rounded-full overflow-hidden">
                          <div className="bg-primary h-full rounded-full transition-all duration-1000" style={{ width: '100%' }}></div>
                        </div>
                        <div className="flex items-center gap-space-sm text-on-surface-variant font-body-sm text-body-sm">
                          <span className="material-symbols-outlined text-[18px] text-primary animate-spin">progress_activity</span>
                          <span>Analyzing email headers, authentication, and infrastructure...</span>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={startAnalysis}
                        className="w-full py-space-sm rounded-xl bg-primary text-on-primary hover:bg-primary-container font-title-sm text-title-sm shadow-sm transition-colors flex items-center justify-center gap-space-xs"
                      >
                        <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                        Start Analysis
                      </button>
                    )}
                    {uploadError && <p className="text-error text-sm">{uploadError}</p>}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function CaseCard({ caseData, onClick }: { caseData: Case; onClick: () => void }) {
  const riskColor = caseData.riskScore >= 80 ? 'error' : caseData.riskScore >= 60 ? 'secondary' : 'tertiary';
  const riskBg = caseData.riskScore >= 80 ? 'bg-error-container text-on-error-container' : caseData.riskScore >= 60 ? 'bg-secondary-fixed text-on-secondary-fixed-variant' : 'bg-tertiary-fixed text-on-tertiary-fixed';
  const statusBg = caseData.status === 'Active' ? 'bg-tertiary-fixed text-on-tertiary-fixed' : caseData.status === 'Escalated' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-high text-on-surface-variant';

  return (
    <button
      onClick={onClick}
      className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm hover:shadow-md transition-all text-left flex flex-col gap-space-md w-full"
    >
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-space-2xs">
          <div className="flex items-center gap-space-xs">
            <span className="font-label-mono-sm text-label-mono-sm text-on-surface-variant">Case #{caseData.number}</span>
            <span className={`font-badge-label text-badge-label px-space-xs py-space-2xs rounded-full ${statusBg}`}>
              {caseData.status}
            </span>
          </div>
          <span className="font-title-sm text-title-sm text-on-surface font-semibold line-clamp-1">{caseData.subject}</span>
        </div>
        <div className="relative w-12 h-12 shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle className="text-surface-container-high" cx="24" cy="24" fill="none" r="19" stroke="currentColor" strokeWidth="4"></circle>
            <circle className={`text-${riskColor} transition-all duration-1000`} cx="24" cy="24" fill="none" r="19" stroke="currentColor" strokeDasharray="119.38" strokeDashoffset={119.38 - (119.38 * caseData.riskScore / 100)} strokeLinecap="round" strokeWidth="4"></circle>
          </svg>
          <span className="absolute inset-0 flex items-center justify-center font-label-mono-sm text-label-mono-sm text-on-surface font-bold">{caseData.riskScore}</span>
        </div>
      </div>
      <div className="flex items-center gap-space-xs flex-wrap">
        <span className={`font-badge-label text-badge-label px-space-xs py-space-2xs rounded-full ${riskBg}`}>
          {caseData.threatType}
        </span>
        <span className="font-badge-label text-badge-label px-space-xs py-space-2xs rounded-full bg-surface-container text-on-surface-variant">
          {caseData.riskLevel}
        </span>
      </div>
      <div className="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
        <span className="material-symbols-outlined text-[14px]">schedule</span>
        <span>{caseData.receivedDate}</span>
      </div>
    </button>
  );
}

export default CasesPage;
