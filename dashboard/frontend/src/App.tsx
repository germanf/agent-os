import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Notes from "./pages/Notes";
import Chat from "./pages/Chat";
import McpAdmin from "./pages/McpAdmin";
import OrchestratorView from "./pages/OrchestratorView";
import JobsPage from "./pages/JobsPage";

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Landing />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="notes" element={<Notes />} />
          <Route path="chat" element={<Chat />} />
          <Route path="chat/:chatId" element={<Chat />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="orchestrator" element={<OrchestratorView />} />
          <Route path="mcp" element={<McpAdmin />} />
        </Route>
      </Routes>
    </ToastProvider>
  );
}
