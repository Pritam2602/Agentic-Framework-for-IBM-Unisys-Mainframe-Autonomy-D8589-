import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ExecutionPage from "./pages/ExecutionPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/execution" replace />} />
        <Route path="/execution" element={<ExecutionPage />} />
        <Route path="*" element={<Navigate to="/execution" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
