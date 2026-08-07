import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopNav from "../components/TopNav";
import { analyzeClient, extractDossier } from "../api/client";
import "./Landing.css";

const STEPS = [
  "Récupération du dossier client",
  "Calcul des ratios financiers et du score Altman",
  "Détection des combinaisons de ratios (patterns)",
  "Décision de crédit",
];

export default function Landing() {
  const navigate = useNavigate();
  const [clientId, setClientId] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  const [extracting, setExtracting] = useState(false);
  const [extractMessage, setExtractMessage] = useState(null);

  async function handleAnalyze(e) {
    e.preventDefault();
    if (!clientId.trim() || loading) return;

    setLoading(true);
    setError(null);
    setStep(0);

    // Progression indicative : l'agent ne renvoie rien avant la fin, ces
    // paliers ne reflètent pas un vrai statut serveur, juste une attente
    // moins opaque (le run complet prend plusieurs dizaines de secondes).
    const stepTimer = setInterval(() => {
      setStep((s) => Math.min(s + 1, STEPS.length - 1));
    }, 3500);

    try {
      const result = await analyzeClient(clientId.trim());
      navigate(`/resultat/${encodeURIComponent(clientId.trim())}`, { state: { result } });
    } catch (err) {
      setError(err.message);
    } finally {
      clearInterval(stepTimer);
      setLoading(false);
    }
  }

  async function handleExtract() {
    if (!clientId.trim() || extracting) return;
    setExtracting(true);
    setExtractMessage(null);
    try {
      const res = await extractDossier(clientId.trim());
      setExtractMessage({ ok: true, text: res.message || "Dossier extrait avec succès." });
    } catch (err) {
      setExtractMessage({ ok: false, text: err.message });
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="landing">
      <TopNav />

      <main className="landing__main">
        <div className="landing__intro">
          <h1 className="landing__title">Nouvelle analyse</h1>
          <p className="landing__subtitle">
            Renseigne l'identifiant d'un client déjà extrait pour lancer l'analyse financière et
            la décision de crédit.
          </p>
        </div>

        <form className="landing__card" onSubmit={handleAnalyze}>
          <label className="landing__label" htmlFor="clientId">
            Identifiant client
          </label>
          <input
            id="clientId"
            className="landing__input"
            type="text"
            placeholder="ex. data"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            disabled={loading}
            autoFocus
          />

          {error && <p className="landing__error">{error}</p>}

          <button type="submit" className="landing__submit" disabled={!clientId.trim() || loading}>
            {loading ? "Analyse en cours…" : "Lancer l'analyse"}
            {!loading && <span>→</span>}
          </button>

          {loading && (
            <ul className="landing__steps">
              {STEPS.map((label, i) => (
                <li key={label} className={`landing__step ${i <= step ? "landing__step--active" : ""}`}>
                  <span className="landing__step-dot" />
                  {label}
                </li>
              ))}
            </ul>
          )}

          <div className="landing__divider" />

          <div className="landing__extract">
            <div>
              <p className="landing__extract-title">Dossier pas encore extrait ?</p>
              <p className="landing__extract-help">
                Déclenche l'extraction des documents côté document-service (le dossier doit déjà
                exister sur le serveur).
              </p>
            </div>
            <button
              type="button"
              className="landing__extract-btn"
              onClick={handleExtract}
              disabled={!clientId.trim() || extracting}
            >
              {extracting ? "Extraction…" : "Extraire le dossier"}
            </button>
          </div>

          {extractMessage && (
            <p className={`landing__extract-message ${extractMessage.ok ? "" : "landing__extract-message--error"}`}>
              {extractMessage.text}
            </p>
          )}
        </form>
      </main>
    </div>
  );
}
