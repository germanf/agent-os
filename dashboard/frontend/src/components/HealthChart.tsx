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

  const lineData = history.map(h => ({
    time: new Date(h.timestamp * 1000).toLocaleTimeString(),
    healthy: h.components.filter(c => c.status === "healthy").length,
    total: h.components.length,
  }));

  return (
    <div className="card">
      <div className="card-title">Health History</div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={lineData} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <CartesianGrid stroke="#30363d" strokeDasharray="3 3" />
          <XAxis dataKey="time" tick={{ fill: "#8b949e", fontSize: 9 }} axisLine={{ stroke: "#30363d" }} />
          <YAxis domain={[0, "dataMax"]} tick={{ fill: "#8b949e", fontSize: 9 }} axisLine={{ stroke: "#30363d" }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: 6, fontSize: 11 }}
            labelStyle={{ color: "#c9d1d9" }}
          />
          <Line type="monotone" dataKey="healthy" name="Healthy components" stroke="#3fb950" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
