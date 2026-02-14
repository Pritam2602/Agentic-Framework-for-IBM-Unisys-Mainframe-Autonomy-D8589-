import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import CatalogPage from './pages/CatalogPage';
import CommandsPage from './pages/CommandsPage';
import JobsPage from './pages/JobsPage';
import WorkflowsPage from './pages/WorkflowsPage';
import DatasetsPage from './pages/DatasetsPage';
import ReasoningLogsPage from './pages/ReasoningLogsPage';
import ExecutionPage from './pages/ExecutionPage';
import IBMAgentPage from './pages/IBMAgentPage';
import UnisysAgentPage from './pages/UnisysAgentPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirect root to catalog */}
        <Route path="/" element={<Navigate to="/catalog" replace />} />
        
        {/* Catalog routes */}
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/catalog/commands" element={<CommandsPage />} />
        <Route path="/catalog/jobs" element={<JobsPage />} />
        <Route path="/catalog/workflows" element={<WorkflowsPage />} />
        <Route path="/catalog/datasets" element={<DatasetsPage />} />
        
        {/* Other main routes */}
        <Route path="/reasoning-logs" element={<ReasoningLogsPage />} />
        <Route path="/execution" element={<ExecutionPage />} />
        <Route path="/ibm-agent" element={<IBMAgentPage />} />
        <Route path="/unisys-agent" element={<UnisysAgentPage />} />
        
        {/* Catch all */}
        <Route path="*" element={<Navigate to="/catalog" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
