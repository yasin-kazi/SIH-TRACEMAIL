import { useCaseStore } from '../store/useCaseStore';

export async function runMockAnalysis(): Promise<void> {
  const store = useCaseStore.getState();

  const stepCount = store.analysisSteps.length;
  const progressPerStep = 100 / stepCount;

  for (let i = 0; i < stepCount; i++) {
    store.updateAnalysisStep(i, 'active');
    store.setAnalysisProgress(Math.round(progressPerStep * i));

    const delay = 200 + Math.random() * 400;
    await new Promise(resolve => setTimeout(resolve, delay));

    store.updateAnalysisStep(i, 'complete');
    store.setAnalysisProgress(Math.round(progressPerStep * (i + 1)));
  }

  store.setAnalysisProgress(100);
  store.completeAnalysis();
}
