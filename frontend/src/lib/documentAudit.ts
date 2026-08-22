import type { IconName } from '../Icon'
import type { DocumentAudit, TracedField } from '../types'

/** Tonalité visuelle de la ligne : accent normal, vigilance, anomalie bloquante. */
export type DocumentTone = 'ok' | 'warn' | 'bad'

export interface DocumentRow {
  name: string
  category: string
  status: string
  data: string
  /** Icône illustrant la donnée extraite (colonne « Données »). */
  icon: IconName
  tone: DocumentTone
}

function nonEmpty(value: unknown): boolean {
  return value !== null && value !== undefined && value !== ''
}

/** Reconstruit la liste des pièces du dossier à partir des blocs extraits (une ligne par document réellement traité). */
export function buildDocumentRows(audit: DocumentAudit): DocumentRow[] {
  const rows: DocumentRow[] = []

  const fiche = audit.profil_administratif?.fiche_renseignements
  if (fiche) {
    const champs = [fiche.raison_sociale, fiche.capital_social, fiche.secteur, fiche.creation].filter(nonEmpty).length
    rows.push({ name: 'Fiche de renseignements', category: 'Administratif', status: champs > 0 ? 'Vérifié' : 'Incomplet', data: `${champs} champs extraits`, icon: 'list', tone: champs > 0 ? 'ok' : 'warn' })
  }

  const demande = audit.profil_administratif?.demande_credit
  if (demande) {
    rows.push({ name: 'Demande de crédit', category: 'Administratif', status: nonEmpty(demande.montant_demande) ? 'Vérifié' : 'Incomplet', data: demande.montant_demande ? `Montant : ${demande.montant_demande}` : 'Montant non détecté', icon: 'database', tone: nonEmpty(demande.montant_demande) ? 'ok' : 'warn' })
  }

  for (const attestation of audit.conformite_reglementaire?.attestations_legales ?? []) {
    rows.push({
      name: `Attestation ${attestation.source} 2023`,
      category: 'Conformité',
      status: attestation.is_compliant ? 'Conforme' : 'Anomalie',
      data: attestation.statut_texte,
      icon: 'clipboard',
      tone: attestation.is_compliant ? 'ok' : 'bad',
    })
  }

  for (const bilan of audit.historique_financier?.historique_financier ?? []) {
    const indicateurs = Object.entries(bilan).filter(([key, val]) => key !== 'annee' && val !== null && (val as TracedField)?.value !== null).length
    rows.push({ name: `Bilan & CPC ${bilan.annee}`, category: 'Financier', status: 'Analysé', data: `${indicateurs} indicateurs`, icon: 'bars', tone: 'ok' })
  }

  const comptes = audit.comportement_bancaire?.comptes_bancaires ?? []
  if (comptes.length > 0) {
    rows.push({ name: 'Relevés bancaires', category: 'Bancaire', status: 'Analysé', data: `${comptes.length} compte${comptes.length > 1 ? 's' : ''} détecté${comptes.length > 1 ? 's' : ''}`, icon: 'bank', tone: 'ok' })
  }

  const centrale = audit.comportement_bancaire?.centrale_risques
  if (centrale) {
    const hasIncident = centrale.incidents?.incidents_definis?.value
    rows.push({ name: 'Central des risques', category: 'Bancaire', status: hasIncident ? 'Alerte' : 'Vérifié', data: centrale.incidents?.statut_incidents?.value ?? 'Statut inconnu', icon: 'shield', tone: hasIncident ? 'warn' : 'ok' })
  }

  return rows
}

/** Marche récursive sur les champs tracés {value, source, page} : % de champs réellement extraits (non null). */
export function extractionQuality(audit: DocumentAudit): number | null {
  const entries: TracedField[] = []
  const walk = (node: unknown) => {
    if (node === null || typeof node !== 'object') return
    if (Array.isArray(node)) return node.forEach(walk)
    const obj = node as Record<string, unknown>
    if ('value' in obj && 'source' in obj && 'page' in obj) {
      entries.push(obj as unknown as TracedField)
      return
    }
    Object.values(obj).forEach(walk)
  }
  walk(audit.historique_financier)
  walk(audit.comportement_bancaire)
  if (entries.length === 0) return null
  const filled = entries.filter((e) => e.value !== null && e.value !== undefined).length
  return Math.round((filled / entries.length) * 1000) / 10
}

export function conformityRate(audit: DocumentAudit): number | null {
  const attestations = audit.conformite_reglementaire?.attestations_legales ?? []
  if (attestations.length === 0) return null
  const compliant = attestations.filter((a) => a.is_compliant).length
  return Math.round((compliant / attestations.length) * 100)
}
