import { useLocation, useParams, Link } from "react-router-dom";
import TopNav from "../components/TopNav";
import Section from "../components/Section";
import DecisionBadge from "../components/DecisionBadge";
import Tag, { NIVEAU_RISQUE_TONE, SEVERITE_TONE, ALTMAN_ZONE_TONE } from "../components/Tag";
import RatioTable from "../components/RatioTable";
import PatternCard from "../components/PatternCard";
import { ratioLabel, splitRatioName } from "../utils/ratios";
import "./Dashboard.css";

const ALTMAN_ZONE_LABELS = {
  safe: "Zone sûre",
  grey: "Zone grise",
  distress: "Zone de détresse",
};

function EmptyState({ clientId }) {
  return (
    <div className="dashboard">
      <TopNav clientId={clientId} />
      <main className="dashboard__empty">
        <h1>Aucun résultat à afficher</h1>
        <p>
          Ce résultat n'est disponible qu'immédiatement après une analyse (il n'est pas
          re-téléchargé au rafraîchissement de la page).
        </p>
        <Link to="/nouvelle-analyse" className="dashboard__empty-link">
          Lancer une nouvelle analyse →
        </Link>
      </main>
    </div>
  );
}

export default function Dashboard() {
  const { clientId } = useParams();
  const location = useLocation();
  const result = location.state?.result;

  if (!result) {
    return <EmptyState clientId={clientId} />;
  }

  const {
    secteur,
    taille,
    taille_source,
    taille_ecart,
    ratios,
    anomalies,
    patterns,
    altman_score,
    coherence_altman,
    dscr,
    conformite_reglementaire,
    alertes_coherence,
    ratios_non_comparables,
    champs_manquants,
    conclusion,
    decision,
  } = result;

  const nonConformes = (conformite_reglementaire?.attestations_legales || []).filter(
    (a) => a.is_compliant === false
  );

  return (
    <div className="dashboard">
      <TopNav clientId={clientId} />

      <main className="dashboard__main">
        <div className="dashboard__header">
          <div>
            <p className="dashboard__client-id">Client</p>
            <h1 className="dashboard__client-name">{clientId}</h1>
            <div className="dashboard__meta">
              {secteur && <Tag tone="neutral">Secteur {secteur}</Tag>}
              {taille && <Tag tone="neutral">Taille {taille}</Tag>}
            </div>
          </div>
          <DecisionBadge decision={decision?.decision} size="lg" />
        </div>

        {taille_ecart && <p className="dashboard__notice">⚠ {taille_ecart}</p>}

        {/* --- Décision de crédit --- */}
        <Section title="Décision de crédit" subtitle="Calculée de façon déterministe, justifiée par le LLM">
          <div className="decision-block">
            {decision?.erreur ? (
              <p className="decision-block__error">{decision.erreur}</p>
            ) : (
              <>
                <div className="decision-block__score">
                  <span className="decision-block__score-value">{decision?.score ?? "—"}</span>
                  <span className="decision-block__score-label">points de risque</span>
                </div>

                <div className="decision-block__contributions">
                  {decision?.contributions?.length > 0 ? (
                    decision.contributions.map((c, i) => (
                      <div key={i} className="decision-block__contribution">
                        <span>{c.label}</span>
                        <span className="decision-block__contribution-points">+{c.points}</span>
                      </div>
                    ))
                  ) : (
                    <p className="dashboard__muted">Aucun signal de risque détecté.</p>
                  )}
                </div>

                {decision?.justification && (
                  <p className="decision-block__justification">{decision.justification}</p>
                )}
              </>
            )}
          </div>
        </Section>

        {/* --- Altman --- */}
        {altman_score && (
          <Section title="Score de défaillance Altman">
            <div className="altman-block">
              <div className="altman-block__score">
                <span className="altman-block__score-value">{altman_score.score}</span>
                <span className="altman-block__score-model">{altman_score.model}</span>
              </div>
              <div className="altman-block__details">
                <Tag tone={ALTMAN_ZONE_TONE[altman_score.zone] || "neutral"}>
                  {ALTMAN_ZONE_LABELS[altman_score.zone] || altman_score.zone}
                </Tag>
                <p className="altman-block__formula">{altman_score.formula_used}</p>
              </div>
            </div>
            {coherence_altman && (
              <p className="altman-block__coherence">
                ⚠ Divergence détectée : {coherence_altman.divergence}
              </p>
            )}
          </Section>
        )}

        {/* --- DSCR / conformité / BAM --- */}
        <div className="dashboard__grid-3">
          {dscr && (
            <Section title="DSCR">
              <p className="mini-stat">
                <span className="mini-stat__value">{dscr.dscr}</span>
                <Tag tone={dscr.is_dscr_acceptable ? "success" : "danger"}>
                  {dscr.is_dscr_acceptable ? "Acceptable" : "Insuffisant"}
                </Tag>
              </p>
            </Section>
          )}

          <Section title="Conformité réglementaire">
            {conformite_reglementaire?.attestations_legales?.length > 0 ? (
              <ul className="mini-list">
                {conformite_reglementaire.attestations_legales.map((a, i) => (
                  <li key={i}>
                    <span>{a.source}</span>
                    <Tag tone={a.is_compliant ? "success" : "danger"}>{a.statut_texte || (a.is_compliant ? "En règle" : "Non conforme")}</Tag>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="dashboard__muted">Non vérifiée pour cette analyse.</p>
            )}
          </Section>

          <Section title="Centrale des Risques (BAM)">
            {alertes_coherence?.length > 0 ? (
              <ul className="mini-list mini-list--alert">
                {alertes_coherence.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            ) : (
              <p className="dashboard__muted">Aucun incident signalé.</p>
            )}
          </Section>
        </div>

        {/* --- Anomalies --- */}
        <Section title="Anomalies détectées" subtitle={`${anomalies?.length || 0} ratio(s) hors norme`}>
          {anomalies?.length > 0 ? (
            <div className="anomaly-list">
              {anomalies.map((a, i) => {
                const { key } = splitRatioName(a.ratio_name);
                return (
                  <div key={i} className="anomaly-list__item">
                    <span className="anomaly-list__name">{ratioLabel(key)}</span>
                    <span className="anomaly-list__verdict">{a.verdict?.replaceAll("_", " ")}</span>
                    <Tag tone={SEVERITE_TONE[a.severite] || "neutral"}>{a.severite === "elevee" ? "élevée" : "à surveiller"}</Tag>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="dashboard__muted">Aucune anomalie détectée.</p>
          )}
        </Section>

        {/* --- Patterns croisés --- */}
        <Section
          title="Combinaisons de ratios (patterns)"
          subtitle={`${patterns?.length || 0} pattern(s) déclenché(s)`}
        >
          {patterns?.length > 0 ? (
            <div className="pattern-grid">
              {patterns.map((p) => (
                <PatternCard key={p.id} pattern={p} />
              ))}
            </div>
          ) : (
            <p className="dashboard__muted">Aucune combinaison significative détectée.</p>
          )}
        </Section>

        {/* --- Tous les ratios --- */}
        <Section title="Ratios financiers" subtitle="Ensemble des ratios calculés, par catégorie">
          <RatioTable ratios={ratios} />
          {(ratios_non_comparables?.length > 0 || champs_manquants?.length > 0) && (
            <div className="dashboard__gaps">
              {champs_manquants?.length > 0 && (
                <p>Champs manquants dans le dossier : {champs_manquants.join(", ")}</p>
              )}
              {ratios_non_comparables?.length > 0 && (
                <p>{ratios_non_comparables.length} ratio(s) non comparable(s) à une norme.</p>
              )}
            </div>
          )}
        </Section>

        {/* --- Conclusion --- */}
        <Section title="Conclusion de l'agent d'analyse">
          <div className="conclusion">
            {conclusion?.split("\n\n").map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </Section>

        <div className="dashboard__footer">
          <Link to={`/historique/${clientId}`}>Voir l'historique de ce client →</Link>
        </div>
      </main>
    </div>
  );
}
