import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import TopNav from "../components/TopNav";
import { getHistory } from "../api/client";
import "./History.css";

function formatTimestamp(ts) {
  if (!ts) return "Date inconnue";
  const date = new Date(ts);
  return date.toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });
}

export default function History() {
  const { clientId } = useParams();
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setEntries(null);
    setError(null);
    getHistory(clientId)
      .then((data) => setEntries(data.analyses || []))
      .catch((err) => setError(err.message));
  }, [clientId]);

  return (
    <div className="history">
      <TopNav clientId={clientId} />

      <main className="history__main">
        <p className="history__eyebrow">Client {clientId}</p>
        <h1 className="history__title">Historique des analyses</h1>

        {error && <p className="history__error">{error}</p>}
        {!error && entries === null && <p className="history__loading">Chargement…</p>}
        {entries?.length === 0 && <p className="history__empty">Aucune analyse passée pour ce client.</p>}

        <ul className="history__list">
          {entries?.map((entry) => (
            <li key={entry.thread_id} className="history__item">
              <div className="history__item-header">
                <span className="history__item-date">{formatTimestamp(entry.timestamp)}</span>
                <span className="history__item-thread">{entry.thread_id}</span>
              </div>
              <p className="history__item-conclusion">
                {entry.conclusion || "Pas de conclusion enregistrée pour ce run."}
              </p>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
