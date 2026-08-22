import { describe, expect, it } from 'vitest'
import type { BenchmarkRatio, Finding } from '../types'
import { RADAR_AXES, buildRadarScores, radarPoint } from './sectorRadar'

const ratio = (name: string) => ({ ratio_name: name }) as BenchmarkRatio
const anomalie = (name: string) => ({ ratio_name: name }) as Finding

describe('RADAR_AXES', () => {
  it('décrit les quatre catégories réellement benchmarkées', () => {
    // Un 5e axe « trésorerie » avait existé sans jamais avoir de données
    // derrière : le radar affichait une branche systématiquement vide.
    expect(RADAR_AXES.map((a) => a.key)).toEqual(['liquidite', 'rentabilite', 'activite', 'solvabilite'])
  })
})

describe('radarPoint', () => {
  const centre: [number, number] = [150, 130]

  it('place l’angle 0 en haut du radar', () => {
    const [x, y] = radarPoint(centre, 100, 0, 100)
    expect(x).toBeCloseTo(150)
    expect(y).toBeCloseTo(30)
  })

  it('tourne dans le sens horaire', () => {
    const [x, y] = radarPoint(centre, 100, 90, 100)
    expect(x).toBeCloseTo(250)
    expect(y).toBeCloseTo(130)
  })

  it('ramène un score nul au centre', () => {
    expect(radarPoint(centre, 100, 45, 0)).toEqual(centre)
  })

  it('place un score de 50 % à mi-rayon', () => {
    const [, y] = radarPoint(centre, 100, 0, 50)
    expect(y).toBeCloseTo(80)
  })

  it('reste dans le disque du rayon maximal', () => {
    for (const angle of [0, 37, 90, 180, 271, 359]) {
      const [x, y] = radarPoint(centre, 100, angle, 100)
      const distance = Math.hypot(x - centre[0], y - centre[1])
      expect(distance).toBeCloseTo(100)
    }
  })
})

describe('buildRadarScores', () => {
  it('renvoie un axe par catégorie, même sans aucune donnée', () => {
    const scores = buildRadarScores([], [])
    expect(scores).toHaveLength(RADAR_AXES.length)
    expect(scores.map((s) => s.label)).toEqual(RADAR_AXES.map((a) => a.label))
  })

  it('laisse un axe à null quand aucun ratio de la catégorie n’a été comparé', () => {
    // null, pas 0 : « pas comparé » n'est pas « tout est en anomalie ».
    const scores = buildRadarScores([], [])
    expect(scores.every((s) => s.pct === null)).toBe(true)
  })

  it('donne 100 quand aucun ratio comparé n’est en anomalie', () => {
    const scores = buildRadarScores([ratio('liquidite.current_ratio'), ratio('liquidite.quick_ratio')], [])
    expect(scores.find((s) => s.label === 'Liquidité')?.pct).toBe(100)
  })

  it('donne 0 quand tous les ratios comparés sont en anomalie', () => {
    const scores = buildRadarScores(
      [ratio('liquidite.current_ratio')],
      [anomalie('liquidite.current_ratio')],
    )
    expect(scores.find((s) => s.label === 'Liquidité')?.pct).toBe(0)
  })

  it('calcule la part de ratios sains dans la catégorie', () => {
    const scores = buildRadarScores(
      [ratio('activite.dso_days'), ratio('activite.dpo_days'), ratio('activite.asset_turnover'), ratio('activite.cycle_exploitation_days')],
      [anomalie('activite.dso_days')],
    )
    expect(scores.find((s) => s.label === 'Activité')?.pct).toBe(75)
  })

  it('n’impute une anomalie qu’à sa propre catégorie', () => {
    const scores = buildRadarScores(
      [ratio('liquidite.current_ratio'), ratio('solvabilite.autonomie_financiere')],
      [anomalie('liquidite.current_ratio')],
    )
    expect(scores.find((s) => s.label === 'Liquidité')?.pct).toBe(0)
    expect(scores.find((s) => s.label === 'Solvabilité')?.pct).toBe(100)
  })

  it('ignore un ratio dont le préfixe ne correspond à aucun axe', () => {
    const scores = buildRadarScores([ratio('cash_flow.cfo_to_total_debt')], [])
    expect(scores.every((s) => s.pct === null)).toBe(true)
  })

  it('n’est pas trompé par un préfixe partiel', () => {
    // « liquidites.x » ne doit pas alimenter l'axe « liquidite ».
    const scores = buildRadarScores([ratio('liquidites.autre')], [])
    expect(scores.find((s) => s.label === 'Liquidité')?.pct).toBeNull()
  })

  it('arrondit le pourcentage à l’entier', () => {
    const scores = buildRadarScores(
      [ratio('liquidite.a'), ratio('liquidite.b'), ratio('liquidite.c')],
      [anomalie('liquidite.a')],
    )
    expect(scores.find((s) => s.label === 'Liquidité')?.pct).toBe(67)
  })
})
