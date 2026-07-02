import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface JobRow {
  id: string;
  tool: string;
  status: string;
  started_at: number;
}

const STATUS_COLORS: Record<string, string> = {
  done: "#3fb950",
  running: "#58a6ff",
  failed: "#f85149",
  cancelled: "#d29922",
  queued: "#8b949e",
};

export default function JobTimeline() {
  const [data, setData] = useState<JobRow[]>([]);
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    fetch(`/api/jobs?limit=${limit}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => {});
  }, [limit]);

  if (data.length === 0) return null;

  const chartData = [...data].reverse().map(j => ({
    id: j.id.slice(0, 8),
    tool: j.tool,
    status: j.status,
    value: 1,
  }));

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div className="card-title m-0">Recent Jobs</div>
        <select
          className="input !w-auto !py-1 !text-[11px]"
          value={limit}
          onChange={e => setLimit(Number(e.target.value))}
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 4 }} layout="vertical">
          <CartesianGrid stroke="#30363d" strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" hide />
          <YAxis dataKey="id" type="category" tick={{ fill: "#8b949e", fontSize: 10 }} width={60} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#c9d1d9" }}
            formatter={(_: any, __: any, props: any) => [props.payload.tool, props.payload.status]}
          />
          <Bar dataKey="value" name="Jobs" fill="#7C3AED" radius={[0, 3, 3, 0]}
            shape={(props: any) => {
              const color = STATUS_COLORS[props.payload.status] || "#8b949e";
              return <rect x={props.x} y={props.y} width={props.width} height={props.height} fill={color} rx={3} />;
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
