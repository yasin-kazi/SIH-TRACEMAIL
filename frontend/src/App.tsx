import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { LandingPage } from './pages/LandingPage';
import { AnalysisProgress } from './pages/AnalysisProgress';
import { OverviewPage } from './pages/OverviewPage';
import { IdentityPage } from './pages/IdentityPage';
import { GraphPage } from './pages/GraphPage';
import { CampaignPage } from './pages/CampaignPage';
import { ReportPage } from './pages/ReportPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/case/:id/analyzing" element={<AnalysisProgress />} />
          <Route path="/case/:id/overview" element={<OverviewPage />} />
          <Route path="/case/:id/identity" element={<IdentityPage />} />
          <Route path="/case/:id/graph" element={<GraphPage />} />
          <Route path="/case/:id/campaign" element={<CampaignPage />} />
          <Route path="/case/:id/report" element={<ReportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
