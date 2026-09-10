import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import CasesPage from './pages/CasesPage';
import OverviewPage from './pages/OverviewPage';
import IdentityPage from './pages/IdentityPage';
import EvidencePage from './pages/EvidencePage';
import InfrastructurePage from './pages/InfrastructurePage';
import GraphPage from './pages/GraphPage';
import CampaignPage from './pages/CampaignPage';
import TimelinePage from './pages/TimelinePage';
import CopilotPage from './pages/CopilotPage';
import ReportPage from './pages/ReportPage';
import AnalysisProgress from './pages/AnalysisProgress';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CasesPage />} />
          <Route path="/case/:caseId" element={<Layout />}>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="identity" element={<IdentityPage />} />
          <Route path="evidence" element={<EvidencePage />} />
          <Route path="infrastructure" element={<InfrastructurePage />} />
          <Route path="graph" element={<GraphPage />} />
          <Route path="campaign" element={<CampaignPage />} />
          <Route path="timeline" element={<TimelinePage />} />
          <Route path="copilot" element={<CopilotPage />} />
          <Route path="report" element={<ReportPage />} />
          </Route>
          <Route path="/case/:caseId/analyzing" element={<AnalysisProgress />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
