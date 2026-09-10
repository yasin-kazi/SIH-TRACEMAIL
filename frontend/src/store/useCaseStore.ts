import { create } from 'zustand';
import type { CaseData } from '../types';
import { case1042 } from '../data/mockCase1042';
import { caseList } from '../data/mockCases';

interface AnalysisStep {
  label: string;
  status: 'pending' | 'active' | 'complete';
}

interface CaseStore {
  cases: typeof caseList;
  activeCase: CaseData | null;
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisSteps: AnalysisStep[];
  frozen: boolean;
  toastMessage: string | null;

  selectCase: (id: string) => void;
  startAnalysis: () => void;
  completeAnalysis: () => void;
  updateAnalysisStep: (index: number, status: 'pending' | 'active' | 'complete') => void;
  setAnalysisProgress: (progress: number) => void;
  toggleFreeze: () => void;
  showToast: (message: string) => void;
  clearToast: () => void;
  resetToLanding: () => void;
}

const analysisSteps: AnalysisStep[] = [
  { label: 'Evidence Acquisition', status: 'pending' },
  { label: 'MIME Structure Parsing', status: 'pending' },
  { label: 'Header Canonicalization', status: 'pending' },
  { label: 'SPF / DKIM / DMARC Verification', status: 'pending' },
  { label: 'Identity Contradiction Analysis', status: 'pending' },
  { label: 'Infrastructure Fingerprinting', status: 'pending' },
  { label: 'NLP & Linguistic Analysis', status: 'pending' },
  { label: 'Campaign Correlation', status: 'pending' },
  { label: 'Risk & Confidence Scoring', status: 'pending' },
  { label: 'Evidence Vault Seal', status: 'pending' },
];

export const useCaseStore = create<CaseStore>((set, get) => ({
  cases: caseList,
  activeCase: null,
  isAnalyzing: false,
  analysisProgress: 0,
  analysisSteps: analysisSteps.map(s => ({ ...s })),
  frozen: false,
  toastMessage: null,

  selectCase: (_id: string) => {
    set({ activeCase: case1042, isAnalyzing: true, analysisProgress: 0, analysisSteps: analysisSteps.map(s => ({ ...s, status: 'pending' })) });
  },

  completeAnalysis: () => {
    set({ isAnalyzing: false, analysisProgress: 100 });
  },

  updateAnalysisStep: (index: number, status: 'pending' | 'active' | 'complete') => {
    set((state) => {
      const steps = [...state.analysisSteps];
      steps[index] = { ...steps[index], status };
      return { analysisSteps: steps };
    });
  },

  setAnalysisProgress: (progress: number) => {
    set({ analysisProgress: progress });
  },

  startAnalysis: () => {
    set({ isAnalyzing: true });
  },

  toggleFreeze: () => {
    set((state) => ({ frozen: !state.frozen }));
    const msg = get().frozen ? 'Triage Stream Resumed' : 'Triage Stream Paused for Audit';
    get().showToast(msg);
  },

  showToast: (message: string) => {
    set({ toastMessage: message });
    setTimeout(() => set({ toastMessage: null }), 2500);
  },

  clearToast: () => set({ toastMessage: null }),

  resetToLanding: () => {
    set({ activeCase: null, isAnalyzing: false, analysisProgress: 0 });
  },
}));
