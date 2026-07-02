import { Link, useLocation } from "react-router-dom";

const LABELS: Record<string, string> = {
  "": "Home",
  notes: "Notes",
  chat: "Chat",
  orchestrator: "Orchestrator",
  mcp: "MCP",
  dashboard: "Dashboard",
};

export default function Breadcrumbs() {
  const loc = useLocation();
  const parts = loc.pathname.split("/").filter(Boolean);
  if (parts.length === 0) return null;

  return (
    <nav className="flex items-center gap-1 text-xs text-text-muted mb-4">
      <Link to="/" className="hover:text-accent no-underline">Home</Link>
      {parts.map((p, i) => {
        const path = "/" + parts.slice(0, i + 1).join("/");
        const label = LABELS[p] || p;
        return (
          <span key={path} className="flex items-center gap-1">
            <span>/</span>
            {i === parts.length - 1 ? (
              <span className="text-text">{label}</span>
            ) : (
              <Link to={path} className="hover:text-accent no-underline">{label}</Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
