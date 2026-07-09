import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { SkeletonCard } from "../components/Skeleton";
import TokenChart from "../components/TokenChart";
import JobTimeline from "../components/JobTimeline";
import HealthChart from "../components/HealthChart";

interface JobSummary {
  id: string;
  tool: string;
  status: string;
  created_at: string;
}

interface AlertItem {
  id: string;
  component: string;
  severity: string;
  message: string;
  details: Record<string, unknown> | null;
  created_at: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
}

export default function Dashboard() {
  const [health, setHealth] = useState<Record<string, any> | null>(null);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/health").then(r => { try { return r.json() } catch { return null } }),
      fetch("/api/jobs?limit=10").then(r => { try { return r.json() } catch { return null } }),
    ])
      .then(([h, j]) => {
        setHealth(h);
        setJobs(Array.isArray(j) ? j : []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const poll = () => {
      fetch("/api/alerts?limit=20")
        .then(r => r.ok ? r.json() : [])
        .then(a => setAlerts(Array.isArray(a) ? a : []))
        .catch(() => {});
    };
    poll();
    const t = setInterval(poll, 15000);
    return () => clearInterval(t);
  }, []);

  if (loading) return <><SkeletonCard lines={2} /><SkeletonCard lines={3} /></>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <HealthWidget health={health} />
        <StatusWidget />
        <QuickActions />
      </div>
      <ActiveAlerts alerts={alerts} setAlerts={setAlerts} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TokenChart />
        <JobTimeline />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <HealthChart />
      </div>
      <RecentJobs jobs={jobs} />
    </div>
  );
}

function HealthWidget({ health }: { health: Record<string, any> | null }) {
  const status = health?.status || "unknown";
  const isHealthy = status === "healthy";
  return (
    <div className="card">
      <div className="card-title">System Health</div>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${isHealthy ? "bg-success" : "bg-danger"}`} />
        <span className="text-sm font-medium capitalize">{status}</span>
      </div>
      {health?.checks && (
        <div className="space-y-1 text-xs text-text-muted">
          {Object.entries(health.checks).slice(0, 5).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span>{k}</span>
              <span className={String(v) === "ok" ? "text-success" : "text-danger"}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusWidget() {
  const now = new Date().toISOString().slice(0, 19).replace("T", " ");
  return (
    <div className="card">
      <div className="card-title">Server Status</div>
      <div className="flex items-center gap-2 mb-2">
        <span className="w-2 h-2 rounded-full bg-success" />
        <span className="text-sm font-medium">Online</span>
      </div>
      <div className="text-xs text-text-muted">
        <div className="flex justify-between py-0.5"><span>Uptime</span><span className="font-mono">TBD</span></div>
        <div className="flex justify-between py-0.5"><span>Time</span><span className="font-mono text-[10px]">{now}</span></div>
        <div className="flex justify-between py-0.5"><span>DB</span><span className="text-success">SQLite</span></div>
      </div>
    </div>
  );
}

function QuickActions() {
  const links = [
    { to: "/orchestrator", label: "Orchestrator", desc: "Run multi-agent workflows" },
    { to: "/mcp", label: "MCP Admin", desc: "Manage MCP tool servers" },
    { to: "/chat", label: "Chat", desc: "Talk to Claude" },
    { to: "/notes", label: "Notes", desc: "Browse Obsidian vault" },
  ];
  return (
    <div className="card">
      <div className="card-title">Quick Actions</div>
      <div className="space-y-1.5">
        {links.map(l => (
          <Link key={l.to} to={l.to} className="flex items-center justify-between bg-surface2 border border-border rounded-md px-3 py-2 no-underline text-text hover:border-accent transition-colors">
            <div>
              <div className="text-[13px] font-medium">{l.label}</div>
              <div className="text-[11px] text-text-muted">{l.desc}</div>
            </div>
            <span className="text-text-muted text-sm">→</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function ActiveAlerts({ alerts, setAlerts }: { alerts: AlertItem[]; setAlerts: (a: AlertItem[]) => void }) {
  const unacked = alerts.filter(a => !a.acknowledged);

  const severityDot = (s: string) => {
    switch (s) {
      case "critical": return "bg-danger";
      case "warning": return "bg-warning";
      default: return "bg-accent";
    }
  };

  const ackOne = async (id: string) => {
    try {
      const res = await fetch(`/api/alerts/${id}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ by: "ui" }),
      });
      if (!res.ok) return;
      setAlerts(alerts.map(a => a.id === id ? { ...a, acknowledged: true, acknowledged_by: "ui" } : a));
    } catch { /* ignore — next poll will sync */ }
  };

  const ackAll = async () => {
    try {
      const res = await fetch("/api/alerts/acknowledge-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ by: "ui" }),
      });
      if (!res.ok) return;
      setAlerts(alerts.map(a => ({ ...a, acknowledged: true, acknowledged_by: "ui" })));
    } catch { /* ignore — next poll will sync */ }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="card-title m-0">Active Alerts</div>
        {unacked.length > 0 && (
          <button className="btn-ghost text-xs" onClick={ackAll}>Acknowledge all ({unacked.length})</button>
        )}
      </div>
      {alerts.length === 0 ? (
        <div className="text-xs text-text-muted italic">No alerts</div>
      ) : (
        <div className="space-y-1.5 max-h-60 overflow-y-auto">
          {alerts.slice(0, 20).map(a => (
            <div key={a.id} className={`flex items-center justify-between px-3 py-2 rounded-md text-xs ${a.acknowledged ? "opacity-40" : "bg-surface2"}`}>
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className={`w-2 h-2 rounded-full shrink-0 ${severityDot(a.severity)}`} />
                <span className="font-medium truncate">{a.component}</span>
                <span className="text-text-muted truncate">{a.message}</span>
                <span className="text-text-muted shrink-0">{new Date(a.created_at).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                {a.severity === "critical" && !a.acknowledged && (
                  <span className="text-danger font-semibold text-[10px] uppercase">Critical</span>
                )}
                {!a.acknowledged && (
                  <button className="btn-ghost text-[11px] px-2 py-0.5" onClick={() => ackOne(a.id)}>Ack</button>
                )}
                {a.acknowledged && (
                  <span className="text-text-muted text-[10px]">by {a.acknowledged_by}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RecentJobs({ jobs }: { jobs: JobSummary[] }) {
  const badgeClass = (s: string) => {
    switch (s) {
      case "running": return "badge-running";
      case "done": return "badge-done";
      case "failed": return "badge-failed";
      case "cancelled": return "badge-cancelled";
      default: return "badge-queued";
    }
  };
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="card-title m-0">Recent Jobs</div>
        <Link to="/orchestrator" className="text-xs text-accent no-underline hover:underline">View all</Link>
      </div>
      {jobs.length === 0 ? (
        <div className="text-xs text-text-muted italic">No jobs yet</div>
      ) : (
        <table>
          <thead>
            <tr><th>Tool</th><th>Status</th><th>ID</th></tr>
          </thead>
          <tbody>
            {jobs.slice(0, 8).map(j => (
              <tr key={j.id}>
                <td className="font-medium">{j.tool}</td>
                <td><span className={`badge ${badgeClass(j.status)}`}>{j.status}</span></td>
                <td className="font-mono text-[11px] text-text-muted">{j.id.slice(0, 12)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
