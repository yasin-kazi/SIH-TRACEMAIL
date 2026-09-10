import { useNavigate } from 'react-router-dom';
import { useCaseStore } from '../store/useCaseStore';
import { useState } from 'react';

export function LandingPage() {
  const navigate = useNavigate();
  const { cases, selectCase } = useCaseStore();
  const [uploadHover, setUploadHover] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleCaseClick = (id: string) => {
    selectCase(id);
    navigate(`/case/${id}/analyzing`);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    selectCase('1042');
    navigate('/case/1042/analyzing');
  };

  const riskColor = (score: number) => {
    if (score >= 80) return 'text-error';
    if (score >= 50) return 'text-[#f59e0b]';
    return 'text-tertiary';
  };

  const threatBadge = (tc: string) => {
    const map: Record<string, string> = {
      BEC: 'bg-error-container text-on-error-container',
      PHISHING: 'bg-[#f59e0b]/20 text-[#f59e0b]',
      FRAUD: 'bg-[#f59e0b]/20 text-[#f59e0b]',
    };
    return map[tc] || 'bg-surface-container-highest text-on-surface-variant';
  };

  return (
    <div className="min-h-screen px-3 py-4 flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-[24px] text-primary">shield</span>
          </div>
          <div>
            <h1 className="font-headline-md text-on-surface font-bold">TraceMail</h1>
            <p className="font-code-sm text-on-surface-variant">SIH26106 \u2022 Email Forensic Intelligence</p>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-3 transition-all cursor-pointer min-h-[140px] ${
          dragActive
            ? 'border-primary bg-primary/10'
            : uploadHover
            ? 'border-outline-variant bg-surface-container-low'
            : 'border-outline-variant bg-surface-container-lowest'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleFileDrop}
        onClick={() => { selectCase('1042'); navigate('/case/1042/analyzing'); }}
        onMouseEnter={() => setUploadHover(true)}
        onMouseLeave={() => setUploadHover(false)}
      >
        <div className="w-12 h-12 rounded-full bg-primary/15 flex items-center justify-center">
          <span className="material-symbols-outlined text-[28px] text-primary">upload_file</span>
        </div>
        <div className="text-center">
          <p className="font-body-sm text-on-surface font-semibold">Upload .EML for Forensic Analysis</p>
          <p className="font-code-sm text-on-surface-variant mt-0.5">Drag & drop or tap to select \u2022 SHA-256 auto-sealed</p>
        </div>
      </div>

      {/* Case List */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between px-1">
          <span className="font-label-caps text-outline tracking-wider">INVESTIGATION CASES</span>
          <span className="font-code-sm text-primary">{cases.length} Active</span>
        </div>

        {cases.map((c) => (
          <button
            key={c.id}
            onClick={() => handleCaseClick(c.id)}
            className="w-full bg-surface-container rounded-xl p-3 text-left flex flex-col gap-2 active:scale-[0.98] transition-all shadow-sm hover:bg-surface-container-high"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-code-sm text-primary font-bold">#{c.id}</span>
                  <span className={`font-label-caps px-1.5 py-0.5 rounded ${threatBadge(c.threatClass)}`}>{c.threatClass}</span>
                </div>
                <p className="font-body-sm text-on-surface font-semibold mt-1 truncate">{c.subject}</p>
                <p className="font-code-sm text-on-surface-variant truncate">{c.from}</p>
              </div>
              <div className="flex flex-col items-end shrink-0">
                <span className="font-label-caps text-outline">RISK</span>
                <span className={`font-headline-md font-bold ${riskColor(c.riskScore)}`}>{c.riskScore}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-code-sm text-on-surface-variant">{c.date}</span>
              <span className="font-code-sm text-on-surface-variant flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px] text-tertiary">check_circle</span>
                Analyzed
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
