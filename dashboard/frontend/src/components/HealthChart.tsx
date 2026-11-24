import { useState, useEffect } from "react";
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";

interface HealthHistoryPoint {
  timestamp: number;
  overall: string;
  components: Array<{ name: string; status: string }>;
}

export default function HealthChart() {
  const [history, setHistory] = useState<HealthHistoryPoint[]>([]);

  useEffect(() => {
    fetch("/api/health/history?limit=50")
      .then(r => r.json())
      .then(setHistory)
      .catch(() => {});
  }, []);

  if (history.length < 2) return null;

  const total = history[0]?.components.length ?? 1;
  const lineData = history.map(h => ({
    time: new Date(h.timestamp * 1000).toLocaleTimeString(),
    healthy: h.components.filter(c => c.status === "healthy").length,
    degraded: h.components.filter(c => c.status === "degraded").length,
    unavailable: h.components.filter(c => c.status === "unavailable").length,
    total,
  }));

  const last = lineData[lineData.length - 1];
  const pct = last ? Math.round(last.healthy / last.total * 100) : 100;

  return (
    <div className="card">
      <div className="card-title">Health Timeline</div>
      <div className="flex items-center gap-3 mb-2 text-xs">
        <span><span className="inline-block w-2 h-2 rounded-full bg-success mr-1" />Healthy {last?.healthy ?? 0}/{total}</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-warning mr-1" />Degraded {last?.degraded ?? 0}/{total}</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-danger mr-1" />Unavailable {last?.unavailable ?? 0}/{total}</span>
        <span className="text-text-muted">{pct}% uptime</span>
      </div>
      <ResponsiveContainer width="100%" height={100}>
        <LineChart data={lineData} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <CartesianGrid stroke="#30363d" strokeDasharray="3 3" />
          <XAxis dataKey="time" tick={{ fill: "#8b949e", fontSize: 9 }} axisLine={{ stroke: "#30363d" }} />
          <YAxis domain={[0, total]} tick={{ fill: "#8b949e", fontSize: 9 }} axisLine={{ stroke: "#30363d" }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: 6, fontSize: 11 }}
            labelStyle={{ color: "#c9d1d9" }}
          />
          <Line type="monotone" dataKey="healthy" name="Healthy" stroke="#3fb950" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="degraded" name="Degraded" stroke="#d29922" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="unavailable" name="Unavailable" stroke="#f85149" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
