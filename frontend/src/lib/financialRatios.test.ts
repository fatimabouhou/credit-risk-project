import { describe, expect, it } from 'vitest'
import type { FinancialReport } from '../types'
import {
  RATIO_DEFS,
  buildExtraRatioRows,
  buildRatioRows,
  computeHealthScore,
  formatMad,
  formatRatioValue,
  hasSingleYearOnly,
  healthScoreLabel,
  normalizeSeries,
} from './financialRatios'

function report(overrides: Record<string, unknown> = {}): FinancialReport {
  return {
    annee_reference: 2023,
    ratios_financiers_n: {},
    altman_score: { model: null, score: null, zone: null, formula_used: null },
    donnees_brutes_applaties: {},
    ...overrides,
  } as FinancialReport
}

describe('formatRatioValue', () => {
  it('affiche deux décimales et le signe multiplicatif pour un ratio', () => {
    expect(formatRatioValue(1.9345, 'x')).toBe('1.93×')
  })

  it('convertit une fraction en pourcentage', () => {
    expect(formatRatioValue(0.3445, 'pct')).toBe('34.45%')
  })

  it('arrondit les délais au jour entier', () => {
    expect(formatRatioValue(542.7, 'days')).toBe('543 jours')
  })

  it('délègue le formatage monétaire à formatMad', () => {
    expect(formatRatioValue(2_500_000, 'mad')).toBe('2.50 M MAD')
  })
})

describe('formatMad', () => {
  it('passe en millions au-dessus du million', () => {
    expect(formatMad(55_600_000)).toEqual({ display: '55.60', unit: 'M MAD' })
  })

  it('passe en milliers entre mille et un million', () => {
    expect(formatMad(48_332)).toEqual({ display: '48.3', unit: 'K MAD' })
  })

  it('reste en MAD sous le millier', () => {
    expect(formatMad(750)).toEqual({ display: '750', unit: 'MAD' })
  })

  it('choisit l’unité sur la valeur absolue', () => {
    // Un montant négatif reste un montant : le seuil se juge en magnitude.
    expect(formatMad(-2_000_000)).toEqual({ display: '-2.00', unit: 'M MAD' })
  })

  it('bascule pile au seuil du million', () => {
    expect(formatMad(1_000_000).unit).toBe('M MAD')
    expect(formatMad(999_999).unit).toBe('K MAD')
  })
})

describe('buildRatioRows', () => {
  it('ne renvoie aucune ligne quand le rapport ne contient pas de ratios', () => {
    expect(buildRatioRows(report())).toEqual([])
  })

  it('ignore un ratio absent plutôt que d’afficher une valeur nulle', () => {
    const rows = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: null } } }))
    expect(rows).toEqual([])
  })

  it('ne retient que les ratios principaux', () => {
    const rows = buildRatioRows(
      report({ ratios_financiers_n: { liquidite: { current_ratio: 1.93, cash_ratio: 1.05 } } }),
    )
    expect(rows.map((r) => r.key)).toEqual(['current_ratio'])
  })

  it('renvoie les ratios secondaires à buildExtraRatioRows', () => {
    const rows = buildExtraRatioRows(
      report({ ratios_financiers_n: { liquidite: { current_ratio: 1.93, cash_ratio: 1.05 } } }),
    )
    expect(rows.map((r) => r.key)).toEqual(['cash_ratio'])
  })

  describe('verdict sur un seuil « au moins »', () => {
    it('est bon au-dessus du seuil', () => {
      const [row] = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: 1.93 } } }))
      expect(row.tone).toBe('good')
      expect(row.verdict).toBe('Bon niveau')
      expect(row.trendIcon).toBe('trendUp')
    })

    it('est bon exactement au seuil', () => {
      const [row] = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: 1.5 } } }))
      expect(row.tone).toBe('good')
    })

    it('bascule en alerte sous le seuil', () => {
      const [row] = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: 1.2 } } }))
      expect(row.tone).toBe('warn')
      expect(row.trendIcon).toBe('trendFlat')
    })
  })

  describe('verdict sur un seuil « au plus »', () => {
    it('est bon sous le seuil', () => {
      const [row] = buildRatioRows(report({ ratios_financiers_n: { activite: { dso_days: 45 } } }))
      expect(row.tone).toBe('good')
      expect(row.thresholdText).toBe('45 jours / < 60 jours')
    })

    it('bascule en alerte au-dessus du seuil', () => {
      const [row] = buildRatioRows(report({ ratios_financiers_n: { activite: { dso_days: 543 } } }))
      expect(row.tone).toBe('warn')
    })
  })

  it('utilise la sévérité forte quand le libellé d’alerte est franchement négatif', () => {
    // ebitda_margin déclare warnTone: 'bad' — « Faible » n'est pas une simple
    // vigilance, la ligne doit passer en rouge et non en ambre.
    const [row] = buildRatioRows(report({ ratios_financiers_n: { rentabilite: { ebitda_margin: 0.02 } } }))
    expect(row.tone).toBe('bad')
    expect(row.trendIcon).toBe('trendDown')
  })

  it('plafonne la barre à 100 % au-delà de la borne haute', () => {
    const [row] = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: 99 } } }))
    expect(row.trackPct).toBe(100)
  })

  it('ne descend jamais sous 0 %', () => {
    const [row] = buildRatioRows(report({ ratios_financiers_n: { rentabilite: { ebitda_margin: -0.5 } } }))
    expect(row.trackPct).toBe(0)
  })

  it('produit une graduation à trois bornes', () => {
    const [row] = buildRatioRows(report({ ratios_financiers_n: { liquidite: { current_ratio: 1.93 } } }))
    expect(row.scaleLabels).toEqual(['0', '1.5×', '3.0×'])
  })

  it('omet verdict, barre et tendance pour un ratio sans seuil de référence', () => {
    // Aucun référentiel ne couvre le fonds de roulement : la valeur brute est
    // affichée seule, sans pastille ni tendance inventées.
    const rows = buildExtraRatioRows(
      report({ ratios_financiers_n: { liquidite: { working_capital_frf: 12_000_000 } } }),
    )
    expect(rows[0].value).toBe('12.00 M MAD')
    expect(rows[0].tone).toBeUndefined()
    expect(rows[0].verdict).toBeUndefined()
    expect(rows[0].trackPct).toBeUndefined()
    expect(rows[0].trendIcon).toBeUndefined()
  })
})

describe('RATIO_DEFS', () => {
  it('n’a aucune clé dupliquée', () => {
    const keys = RATIO_DEFS.map((d) => d.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('déclare six indicateurs principaux', () => {
    // Le guide affiche ce compte : il doit rester dérivé, pas figé ailleurs.
    expect(RATIO_DEFS.filter((d) => d.primary)).toHaveLength(6)
  })

  it('accompagne tout seuil d’une direction, d’une borne haute et de deux libellés', () => {
    for (const def of RATIO_DEFS) {
      if (def.threshold === undefined) continue
      expect(def.direction, def.key).toBeDefined()
      expect(def.scaleMax, def.key).toBeDefined()
      expect(def.goodLabel, def.key).toBeTruthy()
      expect(def.warnLabel, def.key).toBeTruthy()
    }
  })

  it('place toujours le seuil sous la borne haute de la barre', () => {
    for (const def of RATIO_DEFS) {
      if (def.threshold === undefined || def.scaleMax === undefined) continue
      expect(def.threshold, def.key).toBeLessThanOrEqual(def.scaleMax)
    }
  })
})

describe('computeHealthScore', () => {
  it('reste null sans score Altman', () => {
    expect(computeHealthScore({ model: null, score: null, zone: null, formula_used: null })).toBeNull()
  })

  it('reste null sur une zone inconnue', () => {
    expect(computeHealthScore({ model: 'Z', score: 3, zone: 'inconnue', formula_used: null } as never)).toBeNull()
  })

  it('mappe la zone safe sur l’intervalle 70-100', () => {
    const score = computeHealthScore({ model: "Z''", score: 3.52, zone: 'safe', formula_used: null } as never)
    expect(score).toBeGreaterThanOrEqual(70)
    expect(score).toBeLessThanOrEqual(100)
  })

  it('mappe la zone grey sur l’intervalle 40-70', () => {
    const score = computeHealthScore({ model: "Z''", score: 1.8, zone: 'grey', formula_used: null } as never)
    expect(score).toBeGreaterThanOrEqual(40)
    expect(score).toBeLessThanOrEqual(70)
  })

  it('reste croissant à l’intérieur d’une zone', () => {
    const bas = computeHealthScore({ model: "Z''", score: 2.7, zone: 'safe', formula_used: null } as never)!
    const haut = computeHealthScore({ model: "Z''", score: 5, zone: 'safe', formula_used: null } as never)!
    expect(haut).toBeGreaterThan(bas)
  })

  it('plafonne un score hors borne haute', () => {
    const score = computeHealthScore({ model: "Z''", score: 999, zone: 'safe', formula_used: null } as never)
    expect(score).toBe(100)
  })
})

describe('healthScoreLabel', () => {
  it.each([
    ['safe', 'Risque maîtrisé'],
    ['grey', 'Risque à surveiller'],
    ['distress', 'Risque élevé'],
  ])('libelle la zone %s', (zone, titre) => {
    expect(healthScoreLabel(zone as never).title).toBe(titre)
  })

  it('retombe sur « Non évalué » pour une zone absente', () => {
    expect(healthScoreLabel(null as never).title).toBe('Non évalué')
  })
})

describe('normalizeSeries', () => {
  it('ramène le maximum à 100', () => {
    expect(normalizeSeries([25_000_000, 50_000_000, 100_000_000])).toEqual([25, 50, 100])
  })

  it('renvoie une série nulle quand tout vaut zéro', () => {
    // Évite la division par zéro : la courbe reste à plat plutôt que NaN.
    expect(normalizeSeries([0, 0, 0])).toEqual([0, 0, 0])
  })

  it('écrase les valeurs négatives à zéro', () => {
    // Le graphe attend 0-100 : une valeur négative sortirait du cadre.
    expect(normalizeSeries([-10, 50, 100])).toEqual([0, 50, 100])
  })

  it('reste dans les bornes 0-100', () => {
    for (const v of normalizeSeries([3, 999, -50, 12])) {
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThanOrEqual(100)
    }
  })
})

describe('hasSingleYearOnly', () => {
  it('considère un rapport absent comme mono-exercice', () => {
    expect(hasSingleYearOnly(null)).toBe(true)
  })

  it('est vrai avec un seul exercice', () => {
    expect(hasSingleYearOnly(report({ donnees_brutes_applaties: { '2023': {} } }))).toBe(true)
  })

  it('est faux dès deux exercices', () => {
    expect(hasSingleYearOnly(report({ donnees_brutes_applaties: { '2022': {}, '2023': {} } }))).toBe(false)
  })
})
