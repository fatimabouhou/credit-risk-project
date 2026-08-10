import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import Sidebar from "../components/layout/Sidebar";
import TopBar from "../components/layout/TopBar";
import RiskGauge from "../components/dashboard/RiskGauge";
import ScoreBreakdownChart from "../components/dashboard/ScoreBreakdownChart";
import CategoryStatCard from "../components/dashboard/CategoryStatCard";
import CategoryRadar from "../components/dashboard/CategoryRadar";
import Badge from "../components/ui/Badge";
import RankedListCard, { type RankedListRow } from "../components/dashboard/RankedListCard";
import RatioVerdictDonut from "../components/dashboard/RatioVerdictDonut";
import RatioCategoryCard from "../components/dashboard/RatioCategoryCard";
import AnomalyGrid from "../components/dashboard/AnomalyGrid";
import PatternGrid from "../components/dashboard/PatternGrid";
import ConclusionBlock from "../components/dashboard/ConclusionBlock";
import {
  ALTMAN_ZONE_LABELS,
  ALTMAN_ZONE_TONE,
  CATEGORY_LABELS,
  CATEGORY_ORDER,
  ratioLabel,
  splitRatioName,
} from "../lib/ratios";
import { mockAnalysis } from "../data/mockAnalysis";
import type { AnalysisResult, Ratio } from "../types/analysis";

function EmptyState({ clientId }: { clientId?: string }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return (
    <div className="flex min-h-screen bg-bg-base">
      <Sidebar clientId={clientId} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1">
        <main className="mx-auto flex max-w-lg flex-col gap-4 px-6 pt-32 text-center text-text-muted">
          <h1 className="text-2xl font-bold text-text-primary">Aucun résultat à afficher</h1>
          <p>
            Ce résultat n'est disponible qu'immédiatement après une analyse (il n'est pas
            re-téléchargé au rafraîchissement de la page).
          </p>
          <Link to="/nouvelle-analyse" className="font-semibold text-brand-light">
            Lancer une nouvelle analyse →
          </Link>
        </main>
      </div>
    </div>
  );
}

function groupByCategory(ratios: Ratio[]): { category: string; ratios: { ratio: Ratio; key: string }[] }[] {
  const groups = new Map<string, { ratio: Ratio; key: string }[]>();
  for (const ratio of ratios) {
    const { category, key } = splitRatioName(ratio.ratio_name);
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category)!.push({ ratio, key });
  }
  const ordered = CATEGORY_ORDER.filter((c) => groups.has(c)).map((c) => ({ category: c, ratios: groups.get(c)! }));
  const rest = [...groups.keys()]
    .filter((c) => !CATEGORY_ORDER.includes(c))
    .map((c) => ({ category: c, ratios: groups.get(c)! }));
  return [...ordered, ...rest];
}

export default function Dashboard() {
  const { clientId: routeClientId } = useParams<{ clientId: string }>();
  const location = useLocation();
  const state = location.state as { result?: AnalysisResult } | null;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isDemo = new URLSearchParams(location.search).get("demo") === "1";
  const result = state?.result || (isDemo ? mockAnalysis : undefined);

  if (!result) {
    return <EmptyState clientId={routeClientId} />;
  }

  const clientId = routeClientId || result.client_id;
  const categories = groupByCategory(result.ratios);

  const totalRatios = result.ratios.length;
  const anomaliesElevees = result.anomalies.filter((a) => a.severite === "elevee").length;

  // "Ratios hors norme" en liste classée (valeur actuelle en % du seuil
  // de référence cité par la fiche de norme) — remplace le graphique à
  // axes par une liste façon "Top stores by sales".
  const ratioByName = new Map(result.ratios.map((r) => [r.ratio_name, r]));
  const horsNormeRows: RankedListRow[] = result.anomalies
    .map((a) => {
      const ratio = ratioByName.get(a.ratio_name);
      const threshold = ratio?.verdict?.max ?? ratio?.verdict?.min;
      if (!threshold) return null;
      const { key } = splitRatioName(a.ratio_name);
      const pct = Math.round((a.ratio_value / threshold) * 100);
      return {
        label: ratioLabel(key),
        value: `${pct}%`,
        percent: pct,
        tone: a.severite === "elevee" ? ("danger" as const) : ("warning" as const),
      };
    })
    .filter((r): r is RankedListRow => r !== null)
    .sort((a, b) => b.percent - a.percent);

  return (
    <div className="flex min-h-screen bg-bg-base">
      <Sidebar clientId={clientId} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          clientId={clientId}
          secteur={result.secteur}
          taille={result.taille}
          decision={result.decision.decision}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <main className="flex flex-col gap-8 px-6 py-8 pb-20 lg:px-10">
          {result.taille_ecart && (
            <p className="rounded-lg border border-chart-warning/25 bg-chart-warning/8 px-5 py-4 text-sm text-chart-warning">
              ⚠ {result.taille_ecart}
            </p>
          )}

          {result.decision.erreur ? (
            <div className="rounded-xl border border-brand/35 bg-brand/8 p-6 text-[14px] text-brand-light">
              {result.decision.erreur}
            </div>
          ) : (
            <>
              {/* Row 1 : une stat card par catégorie de ratio */}
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
                {categories.map(({ category, ratios }) => (
                  <CategoryStatCard
                    key={category}
                    label={CATEGORY_LABELS[category] || category}
                    ratios={ratios}
                    extra={
                      category === "solvabilite" ? (
                        <>
                          {result.altman_score && (
                            <Badge tone={ALTMAN_ZONE_TONE[result.altman_score.zone] || "neutral"} size="sm">
                              Altman {ALTMAN_ZONE_LABELS[result.altman_score.zone]}
                            </Badge>
                          )}
                          {result.dscr && (
                            <Badge tone={result.dscr.is_dscr_acceptable ? "success" : "danger"} size="sm">
                              DSCR {result.dscr.dscr}
                            </Badge>
                          )}
                        </>
                      ) : undefined
                    }
                  />
                ))}
              </div>

              {/* Row 2 : score de risque en détail — items-start : chaque
                  card garde sa hauteur naturelle plutôt que d'être étirée
                  sur la plus haute du groupe (la jauge est bien plus
                  compacte que les 2 autres). */}
              <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-4">
                <RiskGauge score={result.decision.score ?? 0} decision={result.decision.decision} />
                <div className="xl:col-span-2">
                  <ScoreBreakdownChart contributions={result.decision.contributions} />
                </div>
                <RatioVerdictDonut ratios={result.ratios} nonComparablesCount={result.ratios_non_comparables.length} />
              </div>
            </>
          )}

          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
            <CategoryRadar
              categories={categories.map((c) => ({ ...c, label: CATEGORY_LABELS[c.category] || c.category }))}
            />
            <RankedListCard
              title="Ratios hors norme vs seuil de référence"
              subtitle="Valeur actuelle en % du seuil cité par la fiche de norme"
              rows={horsNormeRows}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">
            {categories.map(({ category, ratios }) => (
              <RatioCategoryCard key={category} category={category} ratios={ratios} />
            ))}
          </div>

          <AnomalyGrid anomalies={result.anomalies} />

          <PatternGrid patterns={result.patterns} />

          <ConclusionBlock conclusion={result.conclusion} />

          <div className="pt-4 text-center">
            <Link to={`/historique/${clientId}`} className="text-sm font-semibold text-brand-light">
              Voir l'historique de ce client →
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
