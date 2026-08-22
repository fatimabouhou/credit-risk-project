import type { AgentAnalysis, DocumentAudit, FinancialReport } from './types'

const financialApi = import.meta.env.VITE_FINANCIAL_API_URL ?? 'http://localhost:8001/api/v1/financial'
const agentApi = import.meta.env.VITE_AGENTIC_API_URL ?? 'http://localhost:8002/api/v1/agentic'
const documentApi = import.meta.env.VITE_DOCUMENT_API_URL ?? 'http://localhost:8000'
const reportApi = import.meta.env.VITE_REPORT_API_URL ?? 'http://localhost:8003/api/v1/report'

/** Porte le status HTTP jusqu'aux appelants (ex: 404 = extraction jamais lancée pour ce client). */
export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.detail ?? `Erreur API (${response.status})`, response.status)
  }
  return response.json() as Promise<T>
}

export function extractDossier(clientId: string) {
  return request<{ message: string }>(`${documentApi}/analyze/${encodeURIComponent(clientId)}`, { method: 'POST' })
}

/**
 * Un fichier sélectionné dans la page d'upload, avec sa catégorie (voir
 * document-service/app/services/upload_service.py, _CATEGORY_TO_SUBFOLDER
 * — ces valeurs doivent rester synchronisées avec celles côté backend).
 * `year` uniquement pour "bilan" (AAAA), vide pour les autres catégories.
 */
export interface UploadEntry {
  file: File
  category: 'fiche_renseignements' | 'demande_credit' | 'attestation_dgi' | 'attestation_cnss' | 'bilan' | 'releve_attijariwafa' | 'releve_cih' | 'amortissement' | 'centrale_risques' | 'garanties'
  year: string
}

/** Dépose les PDF du dossier client sur document-service, avant extraction (voir ensureDocumentAudit). */
export function uploadDocuments(clientId: string, entries: UploadEntry[]) {
  const body = new FormData()
  for (const entry of entries) {
    body.append('files', entry.file)
    body.append('categories', entry.category)
    body.append('years', entry.year)
  }
  return request<{ status: string; documents_recus: Record<string, string[]> }>(
    `${documentApi}/upload/${encodeURIComponent(clientId)}`,
    { method: 'POST', body },
  )
}

/** Données extraites par document-service, sans relancer l'extraction. */
export function getDocumentAudit(clientId: string): Promise<DocumentAudit> {
  return request<DocumentAudit>(`${documentApi}/client/${encodeURIComponent(clientId)}`)
}

/** Relance l'extraction si besoin (404 = jamais analysé), puis retourne l'audit. */
export async function ensureDocumentAudit(clientId: string): Promise<DocumentAudit> {
  try {
    return await getDocumentAudit(clientId)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      await extractDossier(clientId)
      return await getDocumentAudit(clientId)
    }
    throw error
  }
}

export async function getFinancialReport(clientId: string): Promise<FinancialReport> {
  const payload = await request<{ report: FinancialReport }>(`${financialApi}/evaluate/${encodeURIComponent(clientId)}`, { method: 'POST' })
  return payload.report
}

export function runAgentAnalysis(clientId: string): Promise<AgentAnalysis> {
  return request<AgentAnalysis>(`${agentApi}/analyze/${encodeURIComponent(clientId)}`, { method: 'POST' })
}

/** URL du rapport HTML complet (report-service) — ouverte directement dans un nouvel onglet, pas un appel fetch. */
export function reportPreviewUrl(clientId: string): string {
  return `${reportApi}/${encodeURIComponent(clientId)}/preview`
}

/**
 * Traduit une erreur technique (souvent le "detail" brut d'une HTTPException
 * FastAPI, qui peut lui-même embarquer le message d'erreur intégral d'un
 * fournisseur externe — ex. le JSON complet renvoyé par l'API Groq en cas de
 * quota dépassé) en message compréhensible côté utilisateur final. Utilisé
 * par useClientData (voir hooks.ts) : sans ça, ce texte technique brut
 * remonte tel quel jusque dans l'UI (voir App.tsx, {error && ...}).
 */
export function humanizeError(error: unknown): string {
  if (!(error instanceof Error)) return 'Erreur inconnue.'
  const raw = error.message

  if (error instanceof ApiError && error.status === 404) {
    return "Aucune donnée trouvée pour ce client — l'extraction du dossier n'a peut-être pas encore été lancée."
  }

  // Quota LLM épuisé (ex. Groq) : remonté par agentic-service comme une 500
  // "Erreur interne..." qui embarque le message brut du fournisseur, pas
  // comme un vrai 429 côté frontend — on le détecte donc dans le texte.
  if (/rate_limit_exceeded|rate limit reached/i.test(raw)) {
    const wait = raw.match(/try again in ([\dhms]+)/i)?.[1]
    return `Quota de l'agent d'analyse atteint pour aujourd'hui${wait ? ` — réessayez dans ${wait}` : ', réessayez plus tard'}.`
  }

  if (error instanceof ApiError && error.status >= 500) {
    return 'Service temporairement indisponible. Réessayez dans quelques instants.'
  }

  if (/Failed to fetch|NetworkError|Load failed/i.test(raw)) {
    return 'Impossible de joindre le service — vérifiez que les conteneurs Docker sont bien lancés.'
  }

  return raw
}
