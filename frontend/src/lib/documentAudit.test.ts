import { describe, expect, it } from 'vitest'
import type { DocumentAudit } from '../types'
import { buildDocumentRows, conformityRate, extractionQuality } from './documentAudit'

/** Dossier vide : chaque test n'ajoute que le bloc qu'il vérifie. */
function audit(overrides: Partial<DocumentAudit> = {}): DocumentAudit {
  return {
    profil_administratif: {},
    conformite_reglementaire: {},
    historique_financier: {},
    comportement_bancaire: {},
    ...overrides,
  } as DocumentAudit
}

const champ = (value: unknown) => ({ value, source: 'doc.pdf', page: 1 })

describe('buildDocumentRows', () => {
  it('ne produit aucune ligne pour un dossier vide', () => {
    // Une ligne par pièce RÉELLEMENT traitée : pas de gabarit pré-rempli qui
    // ferait croire à des documents attendus mais absents.
    expect(buildDocumentRows(audit())).toEqual([])
  })

  it('compte les champs réellement extraits de la fiche', () => {
    const rows = buildDocumentRows(
      audit({
        profil_administratif: {
          fiche_renseignements: { raison_sociale: 'ABHS SARL', capital_social: '1 000 000', secteur: null, creation: null },
        },
      }),
    )
    expect(rows).toHaveLength(1)
    expect(rows[0].data).toBe('2 champs extraits')
    expect(rows[0].status).toBe('Vérifié')
    expect(rows[0].tone).toBe('ok')
  })

  it('marque la fiche incomplète quand aucun champ ne sort', () => {
    const rows = buildDocumentRows(
      audit({
        profil_administratif: {
          fiche_renseignements: { raison_sociale: null, capital_social: null, secteur: null, creation: null },
        },
      }),
    )
    expect(rows[0].status).toBe('Incomplet')
    expect(rows[0].tone).toBe('warn')
  })

  it('traite la chaîne vide comme un champ absent', () => {
    const rows = buildDocumentRows(
      audit({
        profil_administratif: {
          fiche_renseignements: { raison_sociale: '', capital_social: 'X', secteur: null, creation: null },
        },
      }),
    )
    expect(rows[0].data).toBe('1 champs extraits')
  })

  it('signale une demande de crédit sans montant détecté', () => {
    const rows = buildDocumentRows(
      audit({ profil_administratif: { demande_credit: { montant_demande: null, duree: null, objet: null, apport: null } } }),
    )
    expect(rows[0].data).toBe('Montant non détecté')
    expect(rows[0].status).toBe('Incomplet')
    expect(rows[0].tone).toBe('warn')
  })

  it('reprend le montant de la demande quand il est présent', () => {
    const rows = buildDocumentRows(
      audit({
        profil_administratif: {
          demande_credit: { montant_demande: '2 500 000,00 MAD', duree: '60 mois', objet: null, apport: null },
        },
      }),
    )
    expect(rows[0].data).toBe('Montant : 2 500 000,00 MAD')
    expect(rows[0].icon).toBe('database')
  })

  it('classe une attestation non conforme en anomalie', () => {
    const rows = buildDocumentRows(
      audit({
        conformite_reglementaire: {
          attestations_legales: [
            { source: 'DGI', ice: null, is_compliant: true, statut_texte: 'En règle' },
            { source: 'CNSS', ice: null, is_compliant: false, statut_texte: 'Dette constatée' },
          ],
        },
      }),
    )
    expect(rows.map((r) => r.status)).toEqual(['Conforme', 'Anomalie'])
    expect(rows.map((r) => r.tone)).toEqual(['ok', 'bad'])
  })

  it('compte les indicateurs non nuls de chaque bilan, sans compter l’année', () => {
    const rows = buildDocumentRows(
      audit({
        historique_financier: {
          historique_financier: [
            { annee: 2023, chiffre_affaires: champ(55_000_000), ebitda: champ(null), resultat_net: champ(3_000_000) },
          ],
        },
      }),
    )
    expect(rows[0].name).toBe('Bilan & CPC 2023')
    expect(rows[0].data).toBe('2 indicateurs')
  })

  it('accorde le pluriel au nombre de comptes bancaires', () => {
    const un = buildDocumentRows(audit({ comportement_bancaire: { comptes_bancaires: [{}] as never } }))
    const deux = buildDocumentRows(audit({ comportement_bancaire: { comptes_bancaires: [{}, {}] as never } }))
    expect(un[0].data).toBe('1 compte détecté')
    expect(deux[0].data).toBe('2 comptes détectés')
  })

  it('passe la centrale des risques en alerte sur incident déclaré', () => {
    const rows = buildDocumentRows(
      audit({
        comportement_bancaire: {
          centrale_risques: {
            incidents: { incidents_definis: champ(true), statut_incidents: champ('Incident constaté') },
          },
        } as never,
      }),
    )
    expect(rows[0].status).toBe('Alerte')
    expect(rows[0].tone).toBe('warn')
    expect(rows[0].icon).toBe('shield')
  })

  it('garde l’ordre logique du dossier', () => {
    const rows = buildDocumentRows(
      audit({
        profil_administratif: {
          fiche_renseignements: { raison_sociale: 'A', capital_social: null, secteur: null, creation: null },
          demande_credit: { montant_demande: '1', duree: null, objet: null, apport: null },
        },
        conformite_reglementaire: {
          attestations_legales: [{ source: 'DGI', ice: null, is_compliant: true, statut_texte: 'OK' }],
        },
        comportement_bancaire: { comptes_bancaires: [{}] as never },
      }),
    )
    expect(rows.map((r) => r.category)).toEqual(['Administratif', 'Administratif', 'Conformité', 'Bancaire'])
  })
})

describe('extractionQuality', () => {
  it('reste null quand aucun champ tracé n’existe', () => {
    // null, pas 0 : « aucune donnée » n'est pas « extraction ratée à 100 % ».
    expect(extractionQuality(audit())).toBeNull()
  })

  it('mesure la part de champs réellement remplis', () => {
    const result = extractionQuality(
      audit({
        historique_financier: {
          historique_financier: [
            { annee: 2023, a: champ(1), b: champ(null), c: champ(3), d: champ(4) } as never,
          ],
        },
      }),
    )
    expect(result).toBe(75)
  })

  it('arrondit à une décimale', () => {
    const result = extractionQuality(
      audit({
        historique_financier: {
          historique_financier: [{ annee: 2023, a: champ(1), b: champ(2), c: champ(null) } as never],
        },
      }),
    )
    expect(result).toBe(66.7)
  })

  it('descend dans les structures imbriquées et les tableaux', () => {
    const result = extractionQuality(
      audit({
        comportement_bancaire: {
          comptes_bancaires: [
            { banque: 'CIH', comportement: { nombre_rejets: champ(0), decouvert_max_detecte: champ(null) } },
          ],
        } as never,
      }),
    )
    expect(result).toBe(50)
  })

  it('ne compte pas les champs du profil administratif', () => {
    // La qualité ne porte que sur l'historique financier et le comportement
    // bancaire : ajouter un bloc administratif ne doit pas la diluer.
    const sans = extractionQuality(
      audit({ historique_financier: { historique_financier: [{ annee: 2023, a: champ(1) } as never] } }),
    )
    const avec = extractionQuality(
      audit({
        profil_administratif: { fiche_renseignements: { raison_sociale: null, capital_social: null, secteur: null, creation: null } },
        historique_financier: { historique_financier: [{ annee: 2023, a: champ(1) } as never] },
      }),
    )
    expect(avec).toBe(sans)
  })
})

describe('conformityRate', () => {
  it('reste null sans aucune attestation', () => {
    expect(conformityRate(audit())).toBeNull()
  })

  it('calcule le pourcentage d’attestations conformes', () => {
    const result = conformityRate(
      audit({
        conformite_reglementaire: {
          attestations_legales: [
            { source: 'DGI', ice: null, is_compliant: true, statut_texte: '' },
            { source: 'CNSS', ice: null, is_compliant: false, statut_texte: '' },
          ],
        },
      }),
    )
    expect(result).toBe(50)
  })

  it('renvoie 100 quand toutes sont conformes', () => {
    const result = conformityRate(
      audit({
        conformite_reglementaire: {
          attestations_legales: [{ source: 'DGI', ice: null, is_compliant: true, statut_texte: '' }],
        },
      }),
    )
    expect(result).toBe(100)
  })
})
