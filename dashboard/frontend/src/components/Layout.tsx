import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { IconMenu } from "./icons";

const NAV_ITEMS = [
  { to: "/", label: "Inicio" },
  { to: "/notes", label: "Notes" },
  { to: "/chat", label: "Chat" },
  { to: "/orchestrator", label: "Orchestrator" },
];

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const [lastPathname, setLastPathname] = useState(location.pathname);

  if (location.pathname !== lastPathname) {
    setLastPathname(location.pathname);
    setMenuOpen(false);
  }

  const isChatRoute = location.pathname.startsWith("/chat");

  return (
    <>
      <header className="bg-surface border-b border-border px-3 sm:px-6 py-3 flex items-center gap-3">
        <button
          className="mobile-nav-toggle"
          onClick={() => setMenuOpen(o => !o)}
          aria-label={menuOpen ? "Cerrar menú" : "Abrir menú"}
          aria-expanded={menuOpen}
        >
          <IconMenu />
        </button>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--color-accent)">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <h1 className="text-sm sm:text-base font-semibold truncate">Agentic Software Boutique</h1>
        <span className="hidden sm:inline-block text-[11px] bg-accent text-white rounded px-1.5 py-0.5">VPN-only</span>
      </header>
      <nav
        className={`${menuOpen ? "flex" : "hidden"} md:flex flex-col sm:flex-row gap-0 sm:gap-1 px-3 sm:px-6 py-2 bg-surface border-b border-border overflow-x-auto flex-nowrap`}
      >
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `text-[12px] sm:text-[13px] px-2 sm:px-3 py-1.5 rounded-md no-underline ${
                isActive ? "text-accent bg-surface2" : "text-text-muted hover:text-text hover:bg-surface2"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main
        className={`max-w-[1100px] mx-auto p-3 sm:p-6 flex-1 min-h-0 ${
          isChatRoute ? "overflow-hidden" : "overflow-y-auto"
        }`}
      >
        <Outlet />
      </main>
    </>
  );
}
