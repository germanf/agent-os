import { Link } from "react-router-dom";

const SECTIONS = [
  {
    to: "/notes",
    title: "Notes",
    desc: "Navegá el vault de Obsidian con preview de Markdown renderizado.",
  },
  {
    to: "/chat",
    title: "Chat",
    desc: "Hablá con Claude manteniendo el mismo contexto y memoria.",
  },
];

export default function Landing() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {SECTIONS.map(s => (
        <Link key={s.to} to={s.to} className="card no-underline text-text hover:border-accent transition-colors">
          <div className="card-title">{s.title}</div>
          <p className="text-text-muted text-[13px]">{s.desc}</p>
        </Link>
      ))}
    </div>
  );
}
