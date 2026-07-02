import { useEffect, useState, useRef } from "react";
import { getJSON, postJSON } from "../lib/api";

interface AgentProfile {
  type: string;
  capabilities: string[];
  available: boolean;
  health: { status: string };
}

interface SubTaskView {
  id: string;
  description: string;
  agent_type: string;
  status: string;
  depends_on: string[];
  result: string | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

interface TaskView {
  id: string;
  root_task: string;
  status: string;
  subtasks: SubTaskView[];
  summary: Record<string, number>;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "text-yellow-400",
  running: "text-blue-400",
  completed: "text-green-400",
  failed: "text-red-400",
  cancelled: "text-gray-500",
};

export default function OrchestratorView() {
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [tasks, setTasks] = useState<TaskView[]>([]);
  const [rootTask, setRootTask] = useState("");
  const [subtaskInput, setSubtaskInput] = useState("");
  const [selectedTask, setSelectedTask] = useState<TaskView | null>(null);
  const [sseStatus, setSseStatus] = useState<string>("");
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    getJSON<AgentProfile[]>("/api/orchestrator/agents").then(setAgents).catch(() => {});
    loadTasks();
  }, []);

  function loadTasks() {
    getJSON<TaskView[]>("/api/orchestrator/tasks").then(setTasks).catch(() => {});
  }

  async function handleCreate() {
    const subtasks = subtaskInput
      .split("\n")
      .map(s => s.trim())
      .filter(Boolean)
      .map(s => {
        const parts = s.split("||");
        return {
          description: parts[0].trim(),
          agent_type: parts[1]?.trim() || agents.find(a => a.available)?.type || "claude",
        };
      });

    const body: Record<string, unknown> = {};
    if (subtasks.length > 0) {
      body.subtasks = subtasks;
    } else if (rootTask.trim()) {
      body.root_task = rootTask.trim();
    } else {
      return;
    }

    const result = await postJSON<{ task_id: string }>("/api/orchestrator/tasks", body);
    setRootTask("");
    setSubtaskInput("");
    loadTasks();
    setSelectedTask(null);

    if (result?.task_id) {
      connectSSE(result.task_id);
    }
  }

  function connectSSE(taskId: string) {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const es = new EventSource(`/api/orchestrator/tasks/${taskId}/stream`);
    eventSourceRef.current = es;

    es.addEventListener("subtask_started", (e) => {
      const d = JSON.parse(e.data);
      setSseStatus(`Running: ${d.description}`);
    });
    es.addEventListener("subtask_completed", () => {
      setSseStatus("Subtask completed");
      loadTasks();
    });
    es.addEventListener("subtask_failed", (e) => {
      const d = JSON.parse(e.data);
      setSseStatus(`Failed: ${d.error}`);
      loadTasks();
    });
    es.addEventListener("subtask_retrying", (e) => {
      const d = JSON.parse(e.data);
      setSseStatus(`Retry ${d.attempt}: ${d.error}`);
    });
    es.addEventListener("task_completed", () => {
      setSseStatus("Task completed");
      es.close();
      loadTasks();
    });
    es.addEventListener("task_cancelled", () => {
      setSseStatus("Task cancelled");
      es.close();
      loadTasks();
    });
    es.onerror = () => {
      es.close();
      loadTasks();
    };
  }

  async function handleCancel(taskId: string) {
    await fetch(`/api/orchestrator/tasks/${taskId}`, { method: "DELETE" });
    loadTasks();
  }

  async function viewTask(taskId: string) {
    const task = await getJSON<TaskView>(`/api/orchestrator/tasks/${taskId}`);
    setSelectedTask(task);
  }

  const color = (status: string) => STATUS_COLORS[status] || "text-gray-400";

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Multi-Agent Orchestrator</h2>

      <div className="card p-4 space-y-3">
        <h3 className="font-semibold">New Task</h3>
        <div>
          <label className="text-xs text-text-muted block mb-1">Root task (auto-decompose)</label>
          <input
            className="input w-full"
            placeholder="e.g. Analyze the codebase and write tests"
            value={rootTask}
            onChange={e => setRootTask(e.target.value)}
          />
        </div>
        <div className="text-center text-xs text-text-muted">— or —</div>
        <div>
          <label className="text-xs text-text-muted block mb-1">Subtasks (one per line, format: description || agent_type)</label>
          <textarea
            className="input w-full h-24"
            placeholder="Fix login bug || claude&#10;Write unit tests || opencode"
            value={subtaskInput}
            onChange={e => setSubtaskInput(e.target.value)}
          />
        </div>
        <button className="btn-primary" onClick={handleCreate}>
          Create Task
        </button>
      </div>

      {sseStatus && (
        <div className="text-sm text-accent animate-pulse">{sseStatus}</div>
      )}

      <div className="card p-4">
        <h3 className="font-semibold mb-3">Available Agents</h3>
        <div className="flex flex-wrap gap-3">
          {agents.map(a => (
            <span key={a.type} className={`badge-${a.available ? "success" : "muted"} text-xs px-2 py-1 rounded`}>
              {a.type} {a.available ? "●" : "○"}
            </span>
          ))}
        </div>
        <button className="btn-ghost text-xs mt-2" onClick={() => getJSON<AgentProfile[]>("/api/orchestrator/agents").then(setAgents)}>
          Refresh
        </button>
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold">Tasks</h3>
        {tasks.length === 0 && <p className="text-text-muted text-sm">No tasks yet</p>}
        {tasks.map(t => (
          <div key={t.id} className="card p-3 flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${color(t.status)}`}>●</span>
                <span className="text-sm truncate">{t.root_task || t.id}</span>
                <span className="text-xs text-text-muted">{t.status}</span>
              </div>
              <div className="text-xs text-text-muted mt-1">
                {Object.entries(t.summary).map(([k, v]) => `${k}: ${v}`).join(" | ")}
              </div>
            </div>
            <div className="flex gap-2 shrink-0">
              <button className="btn-ghost text-xs" onClick={() => viewTask(t.id)}>View</button>
              {t.status === "running" || t.status === "pending" ? (
                <button className="btn-danger text-xs" onClick={() => handleCancel(t.id)}>Cancel</button>
              ) : null}
            </div>
          </div>
        ))}
        <button className="btn-ghost text-xs" onClick={loadTasks}>Refresh</button>
      </div>

      {selectedTask && (
        <div className="fixed inset-0 bg-black/60 flex items-start justify-center p-4 z-50 overflow-y-auto" onClick={() => setSelectedTask(null)}>
          <div className="bg-surface rounded-lg p-6 max-w-2xl w-full mt-10 space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="font-bold text-lg">{selectedTask.root_task || "Task Detail"}</h3>
            <p className="text-xs text-text-muted">ID: {selectedTask.id} | Status: <span className={color(selectedTask.status)}>{selectedTask.status}</span></p>

            <div className="space-y-3">
              {selectedTask.subtasks.map(st => (
                <div key={st.id} className="border border-border rounded p-3 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`${color(st.status)}`}>●</span>
                    <span className="font-medium text-sm">{st.description}</span>
                    <span className="badge-muted text-xs px-1.5 py-0.5 rounded">{st.agent_type}</span>
                  </div>
                  <div className="text-xs text-text-muted">
                    Status: {st.status}
                    {st.started_at && ` | Started: ${new Date(st.started_at).toLocaleTimeString()}`}
                    {st.completed_at && ` | Done: ${new Date(st.completed_at).toLocaleTimeString()}`}
                  </div>
                  {st.error && <div className="text-xs text-red-400">Error: {st.error}</div>}
                  {st.result && (
                    <details>
                      <summary className="text-xs text-accent cursor-pointer">Result</summary>
                      <pre className="text-xs mt-1 bg-bg p-2 rounded max-h-40 overflow-y-auto">{st.result}</pre>
                    </details>
                  )}
                </div>
              ))}
            </div>

            <button className="btn-primary text-sm" onClick={() => setSelectedTask(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
