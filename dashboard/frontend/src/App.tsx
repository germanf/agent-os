import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Notes from "./pages/Notes";
import Chat from "./pages/Chat";
import McpAdmin from "./pages/McpAdmin";
import OrchestratorView from "./pages/OrchestratorView";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Landing />} />
        <Route path="notes" element={<Notes />} />
        <Route path="chat" element={<Chat />} />
        <Route path="chat/:chatId" element={<Chat />} />
        <Route path="orchestrator" element={<OrchestratorView />} />
        <Route path="mcp" element={<McpAdmin />} />
      </Route>
    </Routes>
  );
}
