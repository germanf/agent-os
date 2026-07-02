import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface TokenRow {
  agent_name: string;
  model: string;
  total_prompt: number;
  total_completion: number;
  grand_total: number;
}

export default function TokenChart() {
  const [data, setData] = useState<TokenRow[]>([]);
  const [range, setRange] = useState<number | undefined>(undefined);

  useEffect(() => {
    const params = range ? `?since_hours=${range}` : "";
    fetch(`/api/tokens/summary${params}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => {});
  }, [range]);

  if (data.length === 0) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div className="card-title m-0">Token Usage</div>
        <select
          className="input !w-auto !py-1 !text-[11px]"
          value={range ?? ""}
          onChange={e => setRange(e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">All time</option>
          <option value="168">7 days</option>
          <option value="720">30 days</option>
        </select>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
          <CartesianGrid stroke="#30363d" strokeDasharray="3 3" />
          <XAxis dataKey="agent_name" tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={{ stroke: "#30363d" }} />
          <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} axisLine={{ stroke: "#30363d" }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#161b22", border: "1px solid #30363d", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#c9d1d9" }}
          />
          <Bar dataKey="total_prompt" name="Prompt" fill="#7C3AED" radius={[3, 3, 0, 0]} />
          <Bar dataKey="total_completion" name="Completion" fill="#3fb950" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
