import { Link } from "react-router-dom";

const FEATURES = [
  {
    to: "/dashboard",
    title: "Dashboard",
    desc: "Health, tokens, jobs — all in one view.",
  },
  {
    to: "/notes",
    title: "Notes",
    desc: "Browse your Obsidian vault with Markdown preview.",
  },
  {
    to: "/chat",
    title: "Chat",
    desc: "Talk to Claude with persistent context and memory.",
  },
  {
    to: "/orchestrator",
    title: "Orchestrator",
    desc: "Run multi-agent DAG workflows with SSE streaming.",
  },
  {
    to: "/mcp",
    title: "MCP Admin",
    desc: "Manage in-process MCP tool servers.",
  },
];

export default function Landing() {
  return (
    <div className="space-y-6">
      <div className="text-center py-6">
        <h2 className="text-xl font-semibold mb-2">Agentic Software Boutique</h2>
        <p className="text-sm text-text-muted max-w-md mx-auto">
          AI-powered development platform with multi-agent orchestration, MCP ecosystem, chat, and knowledge management.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {FEATURES.map(f => (
          <Link key={f.to} to={f.to} className="card no-underline text-text hover:border-accent transition-colors">
            <div className="card-title">{f.title}</div>
            <p className="text-text-muted text-[13px]">{f.desc}</p>
          </Link>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Stack</div>
        <div className="flex flex-wrap gap-2 text-xs">
          {["Python 3.11+", "FastAPI", "React 19", "TypeScript", "Tailwind v4", "SQLite", "Docker"].map(s => (
            <span key={s} className="bg-surface2 border border-border rounded-md px-2 py-1 text-text-muted">{s}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
