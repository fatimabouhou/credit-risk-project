import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MenuIcon, SearchIcon } from "./icons";
import type { DecisionValue } from "../../types/analysis";

interface TopBarProps {
  clientId: string;
  secteur: string | null;
  taille: string | null;
  decision: DecisionValue;
  onOpenSidebar: () => void;
}

const DECISION_LABEL: Record<string, string> = {
  accord: "Accord",
  a_surveiller: "À surveiller",
  refus: "Refus",
};

const DECISION_CLASSES: Record<string, string> = {
  accord: "text-chart-good bg-chart-good/10 border-chart-good/30",
  a_surveiller: "text-chart-warning bg-chart-warning/10 border-chart-warning/30",
  refus: "text-brand-light bg-brand/10 border-brand/35",
};

export default function TopBar({ clientId, secteur, taille, decision, onOpenSidebar }: TopBarProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const decisionClass = decision ? DECISION_CLASSES[decision] : "text-text-muted bg-white/5 border-white/15";
  const decisionLabel = decision ? DECISION_LABEL[decision] : "Non déterminée";

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/nouvelle-analyse?client=${encodeURIComponent(query.trim())}`);
  }

  return (
    <header className="flex flex-wrap items-center gap-4 border-b border-white/8 bg-bg-base/80 px-6 py-4 backdrop-blur lg:px-10">
      <button
        type="button"
        onClick={onOpenSidebar}
        className="rounded-lg p-2 text-text-muted hover:bg-white/5 hover:text-text-primary lg:hidden"
        aria-label="Ouvrir le menu"
      >
        <MenuIcon />
      </button>

      <div className="flex items-center gap-3">
        <h1 className="text-xl font-extrabold text-text-primary">Dashboard</h1>
        <span className="rounded-full border border-white/12 bg-white/5 px-3.5 py-1.5 text-sm font-semibold text-text-muted">
          Client {clientId}
          {secteur && ` · ${secteur}`}
          {taille && ` · ${taille}`}
        </span>
      </div>

      <form onSubmit={handleSearch} className="ml-auto flex min-w-[220px] flex-1 items-center gap-2 rounded-full border border-white/10 bg-bg-raised px-4 py-2.5 sm:flex-none sm:w-72">
        <SearchIcon />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Rechercher un client…"
          className="w-full bg-transparent text-sm text-text-primary placeholder-text-faint outline-none"
        />
      </form>

      <span className={`inline-flex items-center gap-2 rounded-full border px-5 py-2.5 text-sm font-bold ${decisionClass}`}>
        <span className="h-2 w-2 rounded-full bg-current" />
        {decisionLabel}
      </span>

      <div className="flex items-center gap-2.5 rounded-full border border-white/10 bg-bg-raised py-1.5 pr-4 pl-1.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-accent-purple to-accent-pink text-xs font-bold text-white">
          DA
        </span>
        <span className="hidden text-sm font-semibold text-text-primary sm:inline">Devoteam Africa</span>
      </div>
    </header>
  );
}
