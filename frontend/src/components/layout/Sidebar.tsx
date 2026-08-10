import { Link, useLocation } from "react-router-dom";
import { HomeIcon, ClockIcon } from "./icons";

interface SidebarProps {
  clientId?: string;
  open: boolean;
  onClose: () => void;
}

// Barre latérale fixe, façon "Value Analytics" — logo, nav fonctionnelle
// uniquement (pas de Paramètres/Aide/Déconnexion factices : rien dans ce
// projet ne mène à ces pages, mieux vaut un menu plus court mais honnête).
export default function Sidebar({ clientId, open, onClose }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { to: "/nouvelle-analyse", label: "Nouvelle analyse", icon: HomeIcon, match: "/nouvelle-analyse" },
    ...(clientId
      ? [{ to: `/historique/${clientId}`, label: "Historique", icon: ClockIcon, match: "/historique" }]
      : []),
  ];

  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 flex-col border-r border-white/8 bg-bg-raised transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Link to="/nouvelle-analyse" className="flex items-center gap-2.5 px-6 py-6">
          <span className="flex text-brand">
            <svg viewBox="0 0 24 24" width="22" height="22">
              <polygon points="12,1.5 22,6.5 22,17.5 12,22.5 2,17.5 2,6.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
              <path d="M7 12.5 L10.5 16 L17 8.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="text-base font-extrabold text-text-primary">Credit Risk Intelligence</span>
        </Link>

        <nav className="mt-4 flex flex-col gap-1 px-4">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.match);
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-colors ${
                  isActive
                    ? "bg-accent-purple text-white shadow-lg shadow-accent-purple/30"
                    : "text-text-muted hover:bg-white/5 hover:text-text-primary"
                }`}
              >
                <Icon />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto px-6 py-6">
          <p className="text-xs font-bold tracking-widest text-text-faint uppercase">Devoteam Africa</p>
        </div>
      </aside>
    </>
  );
}
