import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCaseStore } from '../store/useCaseStore';
import { runMockAnalysis } from '../lib/mockAnalysis';

export function AnalysisProgress() {
  const navigate = useNavigate();
  const { activeCase, isAnalyzing, analysisProgress, analysisSteps } = useCaseStore();

  useEffect(() => {
    if (!activeCase) {
      navigate('/');
      return;
    }
    if (isAnalyzing) {
      runMockAnalysis().then(() => {
        setTimeout(() => navigate(`/case/${activeCase.id}/overview`), 500);
      });
    }
  }, []);

  if (!activeCase) return null;

  const stepStatusIcon = (status: string) => {
    if (status === 'complete') return { icon: 'check_circle', color: 'text-tertiary' };
    if (status === 'active') return { icon: 'pending', color: 'text-primary animate-pulse' };
    return { icon: 'radio_button_unchecked', color: 'text-outline-variant' };
  };

  return (
    <div className="min-h-screen px-3 py-6 flex flex-col gap-4">
      <div className="flex flex-col items-center gap-3">
        <div className="w-16 h-16 rounded-2xl bg-primary/15 flex items-center justify-center">
          <span className="material-symbols-outlined text-[36px] text-primary animate-pulse">radar</span>
        </div>
        <div className="text-center">
          <h2 className="font-headline-md text-on-surface font-bold">Forensic Analysis in Progress</h2>
          <p className="font-code-sm text-on-surface-variant mt-1">Case #{activeCase.id} \u2022 {activeCase.emailSubject}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-surface-container-high rounded-full h-2 overflow-hidden">
        <div
          className="bg-primary h-full rounded-full transition-all duration-300 ease-out"
          style={{ width: `${analysisProgress}%` }}
        />
      </div>
      <div className="text-center">
        <span className="font-code-sm text-primary font-bold">{analysisProgress}%</span>
        <span className="font-code-sm text-on-surface-variant ml-2">Complete</span>
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-1.5">
        {analysisSteps.map((step, i) => {
          const { icon, color } = stepStatusIcon(step.status);
          return (
            <div
              key={i}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                step.status === 'active' ? 'bg-surface-container-high' : step.status === 'complete' ? 'bg-surface-container-low' : ''
              }`}
            >
              <span className={`material-symbols-outlined text-[18px] shrink-0 ${color}`}>{icon}</span>
              <span className={`font-body-sm ${step.status === 'active' ? 'text-on-surface font-semibold' : step.status === 'complete' ? 'text-on-surface-variant' : 'text-text-muted'}`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {!isAnalyzing && analysisProgress === 100 && (
        <div className="flex flex-col items-center gap-2 mt-4 animate-fade-in">
          <span className="material-symbols-outlined text-[40px] text-tertiary">verified</span>
          <p className="font-headline-sm text-on-surface font-semibold">Analysis Complete</p>
          <p className="font-code-sm text-on-surface-variant">Loading investigation workbench...</p>
        </div>
      )}
    </div>
  );
}
