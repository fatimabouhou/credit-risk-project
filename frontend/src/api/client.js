// Client API minimal — pas de lib HTTP (axios etc.), juste fetch : peu
// d'appels, tous simples (POST sans body ou GET), pas besoin d'intercepteurs.

const AGENTIC_URL = import.meta.env.VITE_AGENTIC_URL || "http://localhost:8002";
const DOCUMENT_URL = import.meta.env.VITE_DOCUMENT_URL || "http://localhost:8000";

async function parseErrorOrThrow(res) {
  if (res.ok) return res.json();
  const body = await res.json().catch(() => null);
  throw new Error(body?.detail || `Erreur ${res.status}`);
}

// Lance l'agent d'analyse + l'agent de décision (agentic-service) sur un
// client déjà extrait (voir extractDossier). Peut prendre plusieurs
// dizaines de secondes — l'agent 1 fait plusieurs appels d'outils/LLM
// en interne avant de conclure.
export function analyzeClient(clientId) {
  return fetch(`${AGENTIC_URL}/api/v1/agentic/analyze/${encodeURIComponent(clientId)}`, {
    method: "POST",
  }).then(parseErrorOrThrow);
}

// Historique des runs passés d'un client (thread_id, date, conclusion
// uniquement — voir db/history.py, pas le diagnostic complet).
export function getHistory(clientId) {
  return fetch(`${AGENTIC_URL}/api/v1/agentic/history/${encodeURIComponent(clientId)}`).then(
    parseErrorOrThrow
  );
}

// Déclenche l'extraction des documents d'un client (document-service) —
// nécessite qu'un dossier simulators/{client_id}/ existe déjà côté
// serveur (pas un upload de fichier depuis le navigateur, voir main.py
// de document-service : aucune route d'upload n'existe aujourd'hui).
export function extractDossier(clientId) {
  return fetch(`${DOCUMENT_URL}/analyze/${encodeURIComponent(clientId)}`, {
    method: "POST",
  }).then(parseErrorOrThrow);
}
