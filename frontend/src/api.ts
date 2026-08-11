import type { AgentAnalysis, FinancialReport } from './types'

const financialApi = import.meta.env.VITE_FINANCIAL_API_URL ?? 'http://localhost:8001/api/v1/financial'
const agentApi = import.meta.env.VITE_AGENTIC_API_URL ?? 'http://localhost:8002/api/v1/agentic'
const documentApi = import.meta.env.VITE_DOCUMENT_API_URL ?? 'http://localhost:8000'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Erreur API (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function extractDossier(clientId: string) {
  return request<{ message: string }>(`${documentApi}/analyze/${encodeURIComponent(clientId)}`, { method: 'POST' })
}

/** Données extraites par document-service, sans relancer l'extraction. */
export function getDocumentAudit(clientId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`${documentApi}/client/${encodeURIComponent(clientId)}`)
}

export async function getFinancialReport(clientId: string): Promise<FinancialReport> {
  const payload = await request<{ report: FinancialReport }>(`${financialApi}/evaluate/${encodeURIComponent(clientId)}`, { method: 'POST' })
  return payload.report
}

export function runAgentAnalysis(clientId: string): Promise<AgentAnalysis> {
  return request<AgentAnalysis>(`${agentApi}/analyze/${encodeURIComponent(clientId)}`, { method: 'POST' })
}
