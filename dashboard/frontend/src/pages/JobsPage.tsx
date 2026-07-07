import { useState, useEffect, useRef, useCallback } from "react";
import { getJSON } from "../lib/api";

interface JobSummary {
  id: string;
  tool: string;
  status: string;
  exit_code: number | null;
  started_at: number | null;
  ended_at: number | null;
  line_count: number;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const sseRef = useRef<EventSource | null>(null);
  const linesEndRef = useRef<HTMLDivElement>(null);

  const fetchJob = useCallback((id: string) => {
    fetch(`/api/jobs/${id}`)
      .then(r => r.ok ? r.json() : null)
      .then(j => setJobStatus(j?.status ?? null))
      .catch(() => setJobStatus(null));
  }, []);

  const closeSSE = useCallback(() => {
    sseRef.current?.close();
    sseRef.current = null;
  }, []);

  const connectSSE = useCallback((id: string) => {
    setSelected(id);
    setLines([]);
    closeSSE();
    fetchJob(id);

    const sse = new EventSource(`/api/jobs/${id}/stream`);
    sseRef.current = sse;
    sse.onmessage = e => {
      try {
        const line = JSON.parse(e.data) as string;
        setLines(prev => [...prev, line]);
      } catch { /* skip malformed */ }
    };
    sse.addEventListener("done", () => {
      closeSSE();
      fetchJob(id);
    });
    sse.onerror = () => closeSSE();
  }, [closeSSE, fetchJob]);

  const viewLogs = useCallback((id: string) => {
    setSelected(id);
    setLines([]);
    closeSSE();
    setJobStatus("loading");
    Promise.all([
      fetch(`/api/jobs/${id}/logs`).then(r => r.ok ? r.json() : []),
      fetch(`/api/jobs/${id}`).then(r => r.ok ? r.json() : null),
    ]).then(([logs, job]) => {
      setLines(Array.isArray(logs) ? logs : []);
      setJobStatus(job?.status ?? null);
      if (job?.status === "running" || job?.status === "queued") connectSSE(id);
    }).catch(() => setJobStatus(null));
  }, [closeSSE, connectSSE]);

  const cancelJob = useCallback(async () => {
    if (!selected) return;
    try {
      const res = await fetch(`/api/jobs/${selected}/cancel`, { method: "POST" });
      if (!res.ok) return;
    } catch { return; }
    closeSSE();
    setJobStatus("cancelled");
  }, [selected, closeSSE]);

  useEffect(() => {
    getJSON<JobSummary[]>("/api/jobs")
      .then(setJobs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    linesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  useEffect(() => () => sseRef.current?.close(), []);

  const badgeClass = (s: string) => {
    switch (s) {
      case "running": return "badge-running";
      case "done": return "badge-done";
      case "failed": return "badge-failed";
      case "cancelled": return "badge-cancelled";
      default: return "badge-queued";
    }
  };

  if (loading) return <div className="card"><div className="text-text-muted text-sm">Loading jobs…</div></div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <div className="lg:col-span-2 card">
        <div className="card-title">Jobs</div>
        {jobs.length === 0 ? (
          <div className="text-xs text-text-muted italic">No jobs</div>
        ) : (
          <table>
            <thead>
              <tr><th>Tool</th><th>Status</th><th>ID</th></tr>
            </thead>
            <tbody>
              {jobs.map(j => (
                <tr
                  key={j.id}
                  className={`cursor-pointer ${selected === j.id ? "ring-1 ring-accent" : ""}`}
                  onClick={() => viewLogs(j.id)}
                >
                  <td className="font-medium">{j.tool}</td>
                  <td><span className={`badge ${badgeClass(j.status)}`}>{j.status}</span></td>
                  <td className="font-mono text-[11px] text-text-muted">{j.id.slice(0, 12)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="lg:col-span-3 card">
        <div className="flex items-center justify-between mb-3">
          <div className="card-title m-0">
            {selected ? <>Job <span className="font-mono text-accent">{selected.slice(0, 12)}</span></> : "Job Detail"}
          </div>
          {jobStatus && (
            <div className="flex items-center gap-2">
              <span className={`badge ${badgeClass(jobStatus)}`}>{jobStatus}</span>
              {(jobStatus === "running" || jobStatus === "queued") && (
                <button className="btn btn-danger" onClick={cancelJob}>Cancel</button>
              )}
            </div>
          )}
        </div>
        {!selected ? (
          <div className="text-xs text-text-muted italic">Select a job to view logs</div>
        ) : (
          <>
            <div className="log-console">
              {lines.length === 0 && jobStatus === "queued" ? (
                <div className="log-empty">Queued — waiting to start…</div>
              ) : lines.length === 0 && jobStatus === "running" ? (
                <div className="log-empty">Waiting for output…</div>
              ) : lines.length === 0 && jobStatus !== "loading" ? (
                <div className="log-empty">No output</div>
              ) : jobStatus === "loading" ? (
                <div className="log-empty">Loading…</div>
              ) : (
                lines.map((line, i) => (
                  <div key={i} className={`log-line ${line.startsWith("[ERROR]") || line.startsWith("Error") ? "err" : ""}`}>{line}</div>
                ))
              )}
              <div ref={linesEndRef} />
            </div>
            {lines.length > 0 && (
              <div className="text-[11px] text-text-muted mt-2">{lines.length} lines</div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
