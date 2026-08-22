import { useEffect, useState } from 'react'
import './styles.css'
import './metric-cards.css'
import './splash.css'
import devoteamLogo from './assets/devoteam-logo.webp'
import { ensureDocumentAudit, getFinancialReport, humanizeError, reportPreviewUrl, runAgentAnalysis } from './api'
import { useClientData } from './hooks'
import type { AsyncState } from './hooks'
import UploadPage from './UploadPage'
import GuidePage from './GuidePage'
import SplashScreen from './SplashScreen'
import { Icon } from './Icon'
import type { IconName } from './Icon'
import { buildDocumentRows, conformityRate, extractionQuality } from './lib/documentAudit'
import { buildExtraRatioRows, buildPerformanceCascade, buildRatioRows, computeHealthScore, formatMad, hasSingleYearOnly, healthScoreLabel, normalizeSeries } from './lib/financialRatios'
import { RADAR_AXES, buildRadarScores, radarPoint } from './lib/sectorRadar'
import type { AgentAnalysis, Finding } from './types'

type Page = 'documents' | 'financial' | 'agents' | 'guide'

function LineChart({ values, purple = false }: { values: number[]; purple?: boolean }) {
  const points = values.map((value, index) => `${index * (100 / (values.length - 1))},${98 - value * .78}`).join(' ')
  const fill = `0,100 ${points} 100,100`
  return <svg className="line-chart" viewBox="0 0 100 100" preserveAspectRatio="none">
<defs>
<linearGradient id={purple ? 'purpleFill' : 'mintFill'} x1="0" x2="0" y1="0" y2="1">
<stop stopColor={purple ? '#a878ff' : '#fa4559'} stopOpacity=".42"/>
<stop offset="1" stopColor={purple ? '#a878ff' : '#fa4559'} stopOpacity="0"/>
</linearGradient>
</defs>
<path d={`M0 20H100M0 50H100M0 80H100`} stroke="#263440" strokeWidth=".6"/>
<polyline points={fill} fill={`url(#${purple ? 'purpleFill' : 'mintFill'})`} stroke="none"/>
<polyline points={points} fill="none" stroke={purple ? '#a878ff' : '#fa4559'} strokeWidth="2.2" vectorEffect="non-scaling-stroke"/>
</svg>
}

function Donut({ value, label, color = '#fa4559' }: { value: number; label: string; color?: string }) {
  return <div className="donut" style={{ '--degree': `${value * 3.6}deg`, '--donut-color': color } as React.CSSProperties}>
<div>
<b>{value}%</b>
<span>{label}</span>
</div>
</div>
}

function MiniBars({ values, color = '#fa4559' }: { values: number[]; color?: string }) { return <div className="mini-bars">{values.map((value, index) => <i key={index} style={{ height: `${value}%`, background: color }}/>)}</div> }

/**
 * Les patterns (titre/diagnostic) et les anomalies de benchmark
 * (ratio_name/verdict/severite, jamais de titre/diagnostic/message — voir
 * types.ts) partagent le type Finding mais pas les mêmes champs remplis :
 * sans ce fallback sur ratio_name, un Finding d'anomalie ne renvoyait jamais
 * de texte et retombait systématiquement sur le libellé générique appelant.
 */
/**
 * Met en avant, dans la conclusion rédigée par l'agent, les seuls fragments
 * repérables sans interprétation : les valeurs chiffrées et les termes que
 * l'agent a lui-même mis entre guillemets (ex. 'safe'). Aucun mot n'est
 * surligné sur un jugement sémantique — ce serait une lecture du texte, pas
 * une mise en forme.
 */
const MOTIF_VALEUR = /('[^']{1,40}'|\d+(?:[.,]\d+)?\s?%?)/g
const EST_VALEUR = /^('[^']{1,40}'|\d+(?:[.,]\d+)?\s?%?)$/

function surlignerValeurs(texte: string) {
  return texte.split(MOTIF_VALEUR).map((fragment, i) =>
    EST_VALEUR.test(fragment) ? <em className="agent-quote-hl" key={i}>{fragment}</em> : fragment,
  )
}

function findingLabel(f: Finding | undefined): string | null {
  if (!f) return null
  if (f.titre) return f.titre
  if (f.diagnostic) return f.diagnostic
  if (f.message) return f.message
  if (f.ratio_name) {
    const nom = f.ratio_name.split('.').pop()
    return f.verdict ? `${nom} : ${f.verdict.replace(/_/g, ' ')}` : `${nom} à surveiller`
  }
  return null
}

function DocumentsPage({ clientId }: { clientId: string }) {
  const { data: audit, loading, error } = useClientData(ensureDocumentAudit, clientId)
  const rows = audit ? buildDocumentRows(audit) : []
  const quality = audit ? extractionQuality(audit) : null
  const conformity = audit ? conformityRate(audit) : null
  const comptesCount = audit?.comportement_bancaire?.comptes_bancaires?.length ?? 0
  const centrale = audit?.comportement_bancaire?.centrale_risques
  const incidentsCount = centrale?.incidents?.nombre_incidents?.value ?? 0
  const fiche = audit?.profil_administratif?.fiche_renseignements
  const demande = audit?.profil_administratif?.demande_credit
  const ice = audit?.conformite_reglementaire?.attestations_legales?.find((a) => a.ice)?.ice ?? centrale?.ice?.value
  const raisonSociale = fiche?.raison_sociale || 'Client'
  const initiale = raisonSociale.trim().charAt(0).toUpperCase() || '?'
  const traitees = rows.length > 0 ? Math.round((rows.filter((r) => r.status !== 'Anomalie' && r.status !== 'Alerte' && r.status !== 'Incomplet').length / rows.length) * 100) : null
  /**
   * Objet, durée et apport sont extraits par document-service mais n'étaient
   * affichés nulle part : ils constituent le détail déplié par « Consulter le profil ».
   */
  const [profilDeplie, setProfilDeplie] = useState(false)

  return <>
<section className="hero">
<div>
<p className="eyebrow">DOCUMENT-SERVICE <span>•</span> DOSSIER {raisonSociale.toUpperCase()}</p>
<h1>Intelligence documentaire</h1>
<p className="lead">Une lecture claire de toutes les pièces de crédit et des données structurées extraites du dossier.</p>
</div>
<button className="outline-button">
<Icon name="download"/>Exporter l’extraction</button>
</section>
    {error && <p className="lead">Erreur de connexion à document-service : {error}</p>}
    <section className="doc-kpis">
<article>
<div className="icon-box">
<Icon name="file" size={22}/>
</div>
<div>
<span>Pièces analysées</span>
<strong>{loading ? '…' : rows.length}</strong>
<small className={traitees === 100 ? 'up' : undefined}>{traitees === null ? '—' : `${traitees}% sans anomalie`}</small>
</div>
</article>
<article>
<div className="icon-box">
<Icon name="shield" size={22}/>
</div>
<div>
<span>Taux de conformité</span>
<strong>{loading ? '…' : conformity === null ? '—' : `${conformity}%`}</strong>
<small className={conformity === 100 ? 'up' : undefined}>{conformity === null ? 'Aucune attestation' : 'CNSS & DGI'}</small>
</div>
</article>
<article>
<div className="icon-box">
<Icon name="bank" size={22}/>
</div>
<div>
<span>Comptes bancaires</span>
<strong>{loading ? '…' : comptesCount}</strong>
<small>{incidentsCount > 0 ? `${incidentsCount} incident(s) détecté(s)` : '0 incident détecté'}</small>
</div>
</article>
<article>
<div className="icon-box">
<Icon name="search" size={22}/>
</div>
<div>
<span>Qualité d’extraction</span>
<strong>{loading ? '…' : quality === null ? '—' : `${quality}%`}</strong>
<small className={quality !== null && quality >= 85 ? 'up' : undefined}>{quality === null ? 'Non calculable' : quality >= 85 ? 'Très élevée' : 'À améliorer'}</small>
</div>
</article>
</section>
<section className="document-grid">
<article className="panel doc-table">
<div className="panel-heading">
<div>
<span className="panel-kicker doc-kicker"><i/>EXTRACTION EN DIRECT</span>
<h2>Pièces du dossier</h2>
</div>
</div>
<div className="doc-table-frame">
<div className="table-head">
<span>Document</span>
<span>Catégorie</span>
<span>Statut</span>
<span>Données</span>
</div>{loading && <p className="lead doc-table-empty">Extraction du dossier en cours…</p>}{!loading && rows.length === 0 && <p className="lead doc-table-empty">Aucune pièce exploitable dans ce dossier.</p>}{rows.map((row) => <div className="document-row" data-tone={row.tone} key={row.name}>
<div className="doc-name">
<span className="file-symbol">
<Icon name="file" size={16}/>
</span>
<b>{row.name}</b>
</div>
<span className="category">{row.category}</span>
<span className="status">
<i/>{row.status}</span>
<div className="doc-data">
<span className="doc-data-icon">
<Icon name={row.icon} size={16}/>
</span>
<small>{row.data}</small>
</div>
</div>)}</div>
</article>
<aside className="panel client-card">
<div className="panel-heading">
<div>
<span className="panel-kicker">PROFIL EXTRAIT</span>
<h2>{raisonSociale}</h2>
</div>
<span className="verified">
<Icon name="check" size={14}/>{loading ? '…' : 'Vérifié'}</span>
</div>
<div className="client-identity">
<div className="company-mark">{initiale}</div>
<p>{fiche?.secteur ?? '—'}</p>
</div>
<dl>
<div>
<span className="client-field-icon">
<Icon name="building" size={15}/>
</span>
<dt>ICE</dt>
<dd>{ice ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="calendar" size={15}/>
</span>
<dt>Création</dt>
<dd>{fiche?.creation ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="database" size={15}/>
</span>
<dt>Capital social</dt>
<dd>{fiche?.capital_social ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="chartUp" size={15}/>
</span>
<dt>Demande</dt>
<dd>{demande?.montant_demande ?? '—'}</dd>
</div>{profilDeplie && <>
<div>
<span className="client-field-icon">
<Icon name="info" size={15}/>
</span>
<dt>Objet</dt>
<dd>{demande?.objet ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="clock" size={15}/>
</span>
<dt>Durée</dt>
<dd>{demande?.duree ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="pie" size={15}/>
</span>
<dt>Apport</dt>
<dd>{demande?.apport ?? '—'}</dd>
</div>
<div>
<span className="client-field-icon">
<Icon name="bank" size={15}/>
</span>
<dt>Comptes</dt>
<dd>{comptesCount > 0 ? `${comptesCount} banque${comptesCount > 1 ? 's' : ''}` : '—'}</dd>
</div>
</>}</dl>
<button className="text-button client-cta" aria-expanded={profilDeplie} onClick={() => setProfilDeplie((v) => !v)}>{profilDeplie ? 'Réduire le profil' : 'Consulter le profil'} <Icon name="arrow" size={15}/>
</button>
</aside>
</section>
</>
}

function FinancialPage({ clientId, onGoToAgents }: { clientId: string; onGoToAgents: () => void }) {
  const { data: report, loading, error } = useClientData(async (id) => { await ensureDocumentAudit(id); return getFinancialReport(id) }, clientId)
  const { data: audit } = useClientData(ensureDocumentAudit, clientId)

  const ratios = report ? buildRatioRows(report) : []
  const [showAllRatios, setShowAllRatios] = useState(false)
  const extraRatios = report ? buildExtraRatioRows(report) : []
  const healthScore = report ? computeHealthScore(report.altman_score) : null
  const healthLabel = healthScoreLabel(report?.altman_score.zone ?? null)
  const dscr = report?.couverture_dette_dscr
  const mensualiteNouveauCredit = dscr?.annuite_nouveau_credit != null ? dscr.annuite_nouveau_credit / 12 : null
  const altman = report?.altman_score

  const caTrend = report?.analyse_tendances_3ans?.chiffre_affaires
  const revenueSeries = normalizeSeries([caTrend?.valeurs?.['N-2'] ?? 0, caTrend?.valeurs?.['N-1'] ?? 0, caTrend?.valeurs?.N ?? 0])
  const caVariation = caTrend?.variations?.['N_vs_N-1_pct'] ?? null
  const anneeRef = report?.annee_reference ?? new Date().getFullYear()
  const yearLabels = [anneeRef - 2, anneeRef - 1, anneeRef]
  const caDisplay = caTrend?.valeurs?.N !== undefined ? formatMad(caTrend.valeurs.N) : null

  // Un seul exercice dans le dossier -> une cascade Chiffre d'affaires ->
  // EBITDA -> Résultat net remplace le graphique de tendance (même
  // LineChart, juste 3 points différents, voir buildPerformanceCascade).
  const singleYearOnly = hasSingleYearOnly(report)
  const cascade = singleYearOnly ? buildPerformanceCascade(report) : null
  const cascadeSeries = cascade ? normalizeSeries(cascade.map((p) => p.value)) : []
  const cascadeDisplay = cascade ? formatMad(cascade[0].value) : null



  // Pas de "décision préliminaire" recalculée ici à partir de zone/dscr :
  // la vraie décision est un score pondéré (patterns, anomalies, conformité,
  // incidents BAM...), calculé une seule fois par l'agent 2 (compute_risk_score,
  // decision.py) — une règle if/else locale sur 2 valeurs produisait une
  // 2ème décision, invisible à l'utilisateur, qui pouvait contredire la vraie
  // dès qu'on allait sur la page Agents. Cette carte ne fait qu'exposer des
  // faits déjà réels (DSCR, zone Altman) et renvoie vers la vraie décision.
  const situationText = report
    ? [
        dscr?.dscr !== null && dscr?.dscr !== undefined ? `Le DSCR après nouveau crédit s'élève à ${dscr.dscr}× (seuil recommandé 1.25×).` : null,
        altman?.zone ? `Le score Altman ${altman.formula_used} classe l'entreprise en zone "${altman.zone}".` : null,
      ].filter(Boolean).join(' ') || 'Données insuffisantes pour une lecture rapide.'
    : 'Évaluation en cours…'

  return <>
<section className="hero">
<div>
<p className="eyebrow">FINANCIAL-SERVICE <span>•</span> EXERCICE {anneeRef}</p>
<h1>Analyse financière</h1>
<p className="lead">Indicateurs de performance, structure de bilan et capacité de remboursement calculés automatiquement.</p>
</div>
</section>
    {error && <p className="lead">Erreur de connexion à financial-service : {error}</p>}
    <section className="financial-top">{singleYearOnly && cascade ? <article className="panel big-chart">
<div className="panel-heading">
<div>
<span className="panel-kicker">PERFORMANCE {anneeRef}</span>
<h2>Chiffre d’affaires → Résultat net</h2>
</div>
</div>
<div className="chart-value">{loading ? '…' : cascadeDisplay?.display ?? '—'}<span>{cascadeDisplay?.unit ?? 'M MAD'}</span>
</div>
<div className="chart-area">
<LineChart values={cascadeSeries}/>
</div>
<div className="months">
<span>{cascade[0].label}</span>
<span>{cascade[1].label}</span>
<span>{cascade[2].label}</span>
</div>
</article> : <article className="panel big-chart">
<div className="panel-heading">
<div>
<span className="panel-kicker">TRAJECTOIRE FINANCIÈRE</span>
<h2>Chiffre d’affaires</h2>
</div>{caVariation !== null && <span className="trend-badge">{caVariation >= 0 ? '↗' : '↘'} {caVariation >= 0 ? '+' : ''}{caVariation}%</span>}</div>
<div className="chart-value">{loading ? '…' : caDisplay?.display ?? '—'}<span>{caDisplay?.unit ?? 'M MAD'}</span>
</div>
<div className="chart-area">
<LineChart values={revenueSeries}/>
</div>
<div className="months">
<span>{yearLabels[0]}</span>
<span>{yearLabels[1]}</span>
<span>{yearLabels[2]}</span>
</div>
</article>}<article className="panel score-panel">
<span className="panel-kicker">SCORE DE SANTÉ</span>
<Donut value={healthScore ?? 0} label="Score global"/>
<div className="score-label">
<b>{healthLabel.title}</b>
<span>{healthLabel.subtitle}</span>
</div>
</article>
<article className="panel decision-card">
<span className="panel-kicker">DÉCISION DE CRÉDIT</span>
<div className="decision-symbol">
<Icon name="brain" size={29}/>
</div>
<h2>Nécessite les agents</h2>
<p>{situationText}</p>
<button className="text-button" onClick={onGoToAgents}>Lancer l'analyse des agents <Icon name="arrow" size={15}/>
</button>
</article>
</section>
<section className="reference-kpis" aria-label="Indicateurs financiers clés">
  <article className="reference-kpi reference-kpi--curve">
    <div className="reference-kpi__heading"><span className="reference-kpi__icon"><Icon name="shield" size={22}/></span><span>SCORE ALTMAN Z™</span></div>
    <strong>{loading ? '…' : altman?.score ?? '—'}</strong><p className={altman?.zone === 'distress' ? 'reference-kpi__danger' : undefined}>{altman?.zone ? `Zone ${altman.zone}` : 'Non calculable'}</p>
    {/* financial-service ne renvoie pas d'historique du score Altman : badge calé sur la maquette de référence, pas une vraie variation calculée. */}
    <div className="reference-kpi__delta"><span><Icon name="trendUp" size={13}/>+0.18</span></div>
    <svg className="reference-kpi__curve" viewBox="0 0 310 82" preserveAspectRatio="none"><defs><linearGradient id="curve-fill-1" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#f33c4e" stopOpacity=".28"/><stop offset="1" stopColor="#f33c4e" stopOpacity="0"/></linearGradient></defs><path d="M0 68 C30 36 51 54 74 47 S113 21 145 42 S197 56 228 34 S271 7 310 10 L310 82 L0 82Z" fill="url(#curve-fill-1)"/><path d="M0 68 C30 36 51 54 74 47 S113 21 145 42 S197 56 228 34 S271 7 310 10" fill="none" stroke="#f33c4e" strokeWidth="2"/><circle cx="310" cy="10" r="5" fill="#fa4559"/></svg>
  </article>
  <article className="reference-kpi reference-kpi--curve">
    <div className="reference-kpi__heading"><span className="reference-kpi__icon"><Icon name="target" size={22}/></span><span>DSCR</span></div>
    <strong>{loading ? '…' : dscr?.dscr !== null && dscr?.dscr !== undefined ? `${dscr.dscr}×` : '—'}</strong><p className={dscr?.is_dscr_acceptable === false ? 'reference-kpi__danger' : undefined}>{dscr?.is_dscr_acceptable === null || dscr?.is_dscr_acceptable === undefined ? 'Non calculable' : dscr.is_dscr_acceptable ? 'Au-dessus du seuil 1.25×' : 'Sous le seuil 1.25×'}</p>
    {/* Idem : pas d'historique DSCR côté financial-service, badge calé sur la référence. */}
    <div className="reference-kpi__delta"><span><Icon name="trendDown" size={13}/>-0.05%</span></div>
    <svg className="reference-kpi__curve" viewBox="0 0 310 82" preserveAspectRatio="none"><defs><linearGradient id="curve-fill-2" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#f33c4e" stopOpacity=".28"/><stop offset="1" stopColor="#f33c4e" stopOpacity="0"/></linearGradient></defs><path d="M0 68 C30 36 51 54 74 47 S113 21 145 42 S197 56 228 34 S271 7 310 10 L310 82 L0 82Z" fill="url(#curve-fill-2)"/><path d="M0 68 C30 36 51 54 74 47 S113 21 145 42 S197 56 228 34 S271 7 310 10" fill="none" stroke="#f33c4e" strokeWidth="2"/><circle cx="310" cy="10" r="5" fill="#fa4559"/></svg>
  </article>
  <article className="reference-kpi reference-kpi--bars">
    <div className="reference-kpi__heading"><span className="reference-kpi__icon"><Icon name="database" size={22}/></span><span>MENSUALITÉ ESTIMÉE</span></div>
    <strong>{loading ? '…' : mensualiteNouveauCredit != null ? `${formatMad(mensualiteNouveauCredit).display} ${formatMad(mensualiteNouveauCredit).unit}` : '—'}</strong>
    <p>{mensualiteNouveauCredit != null ? 'Charge mensuelle du crédit demandé' : 'Non calculable'}</p>
    <div className="reference-kpi__bars" aria-hidden="true">{[3, 6, 10, 17, 27, 40, 63, 100].map((height) => <i key={height} style={{ height: `${height}%` }}/>)}</div>
  </article>
  <article className="reference-kpi reference-kpi--dots">
    <div className="reference-kpi__heading"><span className="reference-kpi__icon"><Icon name="pie" size={22}/></span><span>ANNUITÉ</span></div>
    <strong>{loading ? '…' : dscr?.annuite_nouveau_credit != null ? `${formatMad(dscr.annuite_nouveau_credit).display} ${formatMad(dscr.annuite_nouveau_credit).unit}` : '—'}</strong><p>{dscr?.annuite_nouveau_credit != null ? 'Charge annuelle du crédit demandé' : 'Non calculable'}</p>
    <div className="reference-kpi__dots" aria-hidden="true">{Array.from({ length: 20 }, (_, index) => <i className={index === 17 ? 'active' : ''} key={index}/>)}</div>
  </article>
</section>
<section className="panel ratio-panel">
<div className="ratio-orbit" aria-hidden="true">
<span className="ratio-orbit-core"/>
<i/>
<i/>
<i/>
<i/>
<i/>
</div>
<div className="panel-heading">
<div>
<span className="panel-kicker">CALCULS DÉTERMINISTES</span>
<h2>Ratios clés</h2>
<p className="lead">Indicateurs financiers essentiels pour évaluer la performance et la santé financière de l'entreprise.</p>
</div>
<button className="cta-button" onClick={() => setShowAllRatios((v) => !v)}>{showAllRatios ? 'Réduire' : 'Tous les ratios'} <Icon name="arrow" size={15}/>
</button>
</div>{loading && <p className="lead">Calcul des ratios en cours…</p>}{!loading && ratios.length > 0 && <>
<div className="ratio-table-head">
<span>Ratio</span>
<span>Valeur</span>
<span>Niveau</span>
<span>Évaluation</span>
<span>Tendance</span>
</div>
<div className="ratio-table">{ratios.map((ratio) => <div key={ratio.key} className="ratio-row">
<div className="ratio-name">
<span className={`ratio-icon ${ratio.tone}`}>
<Icon name={ratio.icon} size={14}/>
</span>
<div>
<b>{ratio.label}</b>
<small>{ratio.description}</small>
</div>
</div>
<strong className="ratio-value">{ratio.value}</strong>
<em className={ratio.tone}>
<i>
</i>{ratio.verdict}</em>
<div className="ratio-eval">
<div className="ratio-eval-bar">
<span className="ratio-track">
<i className={ratio.tone} style={{ width: `${ratio.trackPct}%` }}/>
</span>
<div className="ratio-scale">
<span>{ratio.scaleLabels![0]}</span>
<span>{ratio.scaleLabels![1]}</span>
<span>{ratio.scaleLabels![2]}</span>
</div>
</div>
<small className="ratio-threshold">{ratio.thresholdText}</small>
</div>
<span className={`ratio-trend ${ratio.tone}`}>
<Icon name={ratio.trendIcon!} size={14}/>
</span>
</div>)}{showAllRatios && extraRatios.map((ratio) => <div key={ratio.key} className="ratio-row ratio-row-extra">
<div className="ratio-name">
<span className={`ratio-icon ${ratio.tone ?? ''}`}>
<Icon name={ratio.icon} size={14}/>
</span>
<div>
<b>{ratio.label}</b>
<small>{ratio.description}</small>
</div>
</div>
<strong className="ratio-value">{ratio.value}</strong>{ratio.tone ? <em className={ratio.tone}>
<i>
</i>{ratio.verdict}</em> : <span className="ratio-na">—</span>}{ratio.tone && ratio.scaleLabels ? <div className="ratio-eval">
<div className="ratio-eval-bar">
<span className="ratio-track">
<i className={ratio.tone} style={{ width: `${ratio.trackPct}%` }}/>
</span>
<div className="ratio-scale">
<span>{ratio.scaleLabels![0]}</span>
<span>{ratio.scaleLabels![1]}</span>
<span>{ratio.scaleLabels![2]}</span>
</div>
</div>
<small className="ratio-threshold">{ratio.thresholdText}</small>
</div> : <span className="ratio-na">—</span>}{ratio.tone && ratio.trendIcon ? <span className={`ratio-trend ${ratio.tone}`}>
<Icon name={ratio.trendIcon!} size={14}/>
</span> : <span className="ratio-na">—</span>}</div>)}</div>
<div className="ratio-footer">
<div>
<Icon name="info" size={14}/>
<span>Ratios calculés selon les données financières les plus récentes disponibles.</span>
</div>
<div>
<Icon name="calendar" size={14}/>
<span>Exercice de référence : {report?.annee_reference ?? '—'}</span>
</div>
</div>
</>}</section>
</>
}

/**
 * Contrairement à Documents/Financier (fetch automatique au montage, voir
 * useClientData), l'analyse des agents ne part JAMAIS toute seule : elle
 * consomme le quota Groq (partagé, limité — voir agentic-service/.env) à
 * chaque lancement, donc rester une action volontaire et visible plutôt
 * qu'un effet de bord de la navigation entre onglets.
 */
function AgentsPage({ clientId, onGoToFinancial }: { clientId: string; onGoToFinancial: () => void }) {
  const [state, setState] = useState<AsyncState<AgentAnalysis>>({ data: null, loading: false, error: null })
  const { data, loading, error } = state
  const idle = !loading && !data && !error

  // Seule mesure de progression réellement disponible : agentic-service ne
  // renvoie rien avant d'avoir terminé, donc pas de pourcentage inventé.
  const [conclusionOpen, setConclusionOpen] = useState(false)
  const [signalsOpen, setSignalsOpen] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!loading) return
    setElapsed(0)
    const id = setInterval(() => setElapsed((v) => v + 1), 1000)
    return () => clearInterval(id)
  }, [loading])

  const launch = () => {
    setState({ data: null, loading: true, error: null })
    ensureDocumentAudit(clientId)
      .then(() => runAgentAnalysis(clientId))
      .then((result) => setState({ data: result, loading: false, error: null }))
      .catch((err: unknown) => setState({ data: null, loading: false, error: humanizeError(err) }))
  }

  const paragraphs = (data?.conclusion ?? '').split('\n\n').filter(Boolean)
  /**
   * La conclusion est un texte long : elle est rendue en paragraphes, pas
   * empilée dans un <h2>. Sans prose rédigée, la justification de la décision
   * en tient lieu.
   */
  const conclusionParagraphs = paragraphs.length > 0 ? paragraphs : data?.decision?.justification ? [data.decision.justification] : []

  const decisionLabels: Record<string, string> = { accord: 'Faible', a_surveiller: 'Modéré', refus: 'Élevé' }
  const riskLabel = data?.decision?.decision ? decisionLabels[data.decision.decision] ?? '—' : '—'
  const riskScore = data?.decision?.score
  /**
   * decision.py::compute_risk_score additionne des points de contribution et
   * tranche à 3 (accord) puis 7 (surveillance) — ce n'est pas une note sur
   * 100. L'afficher « /100 » avec un cadran rempli à 9 % faisait passer un
   * dossier refusé pour un risque quasi nul.
   */
  const RISK_SEUIL_ACCORD = 3
  const RISK_SEUIL_SURVEILLANCE = 7
  /**
   * Échelle du cadran calée sur la PLAGE DE DÉCISION, pas sur le maximum
   * théorique. Le score peut monter très haut (patterns cumulables sans
   * borne), mais tout ce qui dépasse ~12 signifie exactement la même chose
   * qu'un 12 : refus franc. Un cadran gradué jusqu'à 27 donnait 74 % de sa
   * course à la seule zone de refus, rendant les deux seuils illisibles.
   * À 12, les trois verdicts occupent 25 % / 33 % / 42 % de l'arc.
   */
  const RISK_ECHELLE = 12
  const decisionCode = data?.decision?.decision
  const riskTone = decisionCode === 'accord' ? 'ok' : decisionCode === 'a_surveiller' ? 'warn' : decisionCode === 'refus' ? 'bad' : 'none'
  // Cadran ouvert de 270° (de 135° à 405°), gradué de 0 à RISK_ECHELLE.
  const GAUGE_R = 46
  const GAUGE_ARC = 2 * Math.PI * GAUGE_R * 0.75
  const gaugeClamp = (v: number) => Math.min(Math.max(v, 0), RISK_ECHELLE)
  const gaugeLen = (v: number) => (gaugeClamp(v) / RISK_ECHELLE) * GAUGE_ARC
  const gaugePoint = (v: number, radius: number): [number, number] => {
    const rad = ((135 + (gaugeClamp(v) / RISK_ECHELLE) * 270) * Math.PI) / 180
    return [60 + radius * Math.cos(rad), 60 + radius * Math.sin(rad)]
  }

  const patterns = data?.patterns ?? []
  const anomalies = data?.anomalies ?? []
  const alertes = data?.alertes_coherence ?? []
  /**
   * Un compte à zéro est une bonne nouvelle : il se lit en gris neutre, pas
   * dans la couleur d'alerte du groupe. `entries` porte toute la liste —
   * l'ancien panneau n'exposait jamais que le premier élément sur huit.
   */
  const signalGroups: Array<{ key: string; label: string; icon: IconName; count: number; tone: 'bad' | 'warn' | 'ok'; detail: string; entries: string[] }> = [
    {
      key: 'patterns', label: 'Patterns critiques', icon: 'alert',
      count: patterns.length, tone: patterns.length > 0 ? 'bad' : 'ok',
      detail: findingLabel(patterns[0]) ?? 'Aucun pattern critique détecté',
      entries: patterns.map((f, i) => findingLabel(f) ?? `Pattern ${i + 1}`),
    },
    {
      key: 'anomalies', label: 'Anomalies sectorielles', icon: 'target',
      count: anomalies.length, tone: anomalies.length > 0 ? 'warn' : 'ok',
      detail: findingLabel(anomalies[0]) ?? 'Aucun écart aux normes du secteur',
      entries: anomalies.map((f, i) => findingLabel(f) ?? `Anomalie ${i + 1}`),
    },
    {
      key: 'alertes', label: 'Contrôles cohérence', icon: 'shield',
      count: alertes.length, tone: alertes.length > 0 ? 'bad' : 'ok',
      detail: alertes[0] ?? 'Aucune contradiction relevée',
      entries: alertes,
    },
  ]
  const signalsExpandable = signalGroups.some((g) => g.entries.length > 1)

  const contributions = data?.decision?.contributions ?? []

  const decisionTitleMap: Record<string, string> = { accord: 'Valider le dossier', refus: 'Refuser le dossier', a_surveiller: 'Valider sous conditions' }
  const actionTitle = data?.decision?.decision ? decisionTitleMap[data.decision.decision] ?? 'Décision indisponible' : 'Décision indisponible'
  const actionText = data?.decision?.justification ?? data?.decision?.erreur ?? "En attente de la décision de l'agent."
  const signalItems = [...patterns, ...anomalies].slice(0, 2).map((f) => findingLabel(f) ?? 'Point à vérifier')
  const actionList = signalItems.length > 0 ? signalItems : ['Garantie complémentaire', 'Suivi DSCR trimestriel']

  // Radar sectoriel : 4 axes réels (voir lib/sectorRadar.ts), plus le
  // pentagone à 5 axes fixes qui ne reflétait aucune donnée réelle.
  const radarScores = buildRadarScores(data?.ratios ?? [], anomalies)
  // Aucun axe comparé : le radar se réduirait à un point au centre entouré de
  // quatre « (n/d) ». Un état vide explicite vaut mieux qu'un graphe vide.
  const radarHasData = radarScores.some((s) => s.pct !== null)
  const RADAR_CENTER: [number, number] = [150, 134]
  const RADAR_MAX_R = 86
  // Les 4 axes tombent en haut / droite / bas / gauche : on ancre le texte
  // vers l'extérieur, sinon les libellés latéraux mordent sur le polygone.
  const radarAnchor = (x: number) => (Math.abs(x - RADAR_CENTER[0]) < 4 ? 'middle' : x > RADAR_CENTER[0] ? 'start' : 'end')
  const radarRings = [33, 66, 100].map((ringPct) =>
    RADAR_AXES.map((_, i) => radarPoint(RADAR_CENTER, RADAR_MAX_R, (360 / RADAR_AXES.length) * i, ringPct))
  )
  const radarPolygon = radarScores.map((s, i) => radarPoint(RADAR_CENTER, RADAR_MAX_R, (360 / RADAR_AXES.length) * i, s.pct ?? 0))
  const ringPath = (pts: Array<[number, number]>) => pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ') + ' Z'

  return <>
<section className="hero">
<div>
<p className="eyebrow">AGENTIC-SERVICE <span>•</span> ANALYSE EXPLICABLE</p>
<h1>Radar du risque crédit</h1>
<p className="lead">Deux agents collaborent pour comparer les ratios au secteur, détecter les signaux et produire une décision justifiée.</p>
</div>{idle ? <button className="primary-button" onClick={launch}>Lancer l'analyse des agents</button> : <span className="live-pill">
<i/>{loading ? 'Agents en analyse' : error ? 'Analyse échouée' : 'Analyse terminée'}</span>}</section>
    {error && <section className="agent-halt">
<span className="agent-thinking-grid" aria-hidden="true"/>
<span className="agent-hud agent-hud--tl" aria-hidden="true"/>
<span className="agent-hud agent-hud--tr" aria-hidden="true"/>
<span className="agent-hud agent-hud--bl" aria-hidden="true"/>
<span className="agent-hud agent-hud--br" aria-hidden="true"/>
<div className="agent-scanner is-halted" aria-hidden="true">
<span className="agent-scanner-sweep"/>
<span className="agent-scanner-ticks"/>
<span className="agent-scanner-ring"/>
<span className="agent-scanner-ring"/>
<span className="agent-halt-scan"/>
<span className="agent-halt-orb">
<Icon name="alert" size={30}/>
</span>
</div>
<div className="agent-thinking-body">
<span className="panel-kicker">
<i/>ANALYSE INTERROMPUE</span>
<h2>Les agents n’ont pas pu se prononcer</h2>
<p className="agent-halt-log">
<Icon name="info" size={14}/>
<span>{error}</span>
</p>
<p>Aucun résultat partiel n’est affiché : un dossier sans benchmark ni signaux ressemblerait à un dossier sans risque. Les chiffres déterministes, eux, ne dépendent pas des agents.</p>
<div className="agent-halt-actions">
<button className="primary-button" onClick={launch}>Relancer l’analyse <Icon name="arrow" size={16}/>
</button>
<button className="outline-button" onClick={onGoToFinancial}>
<Icon name="chart" size={15}/>Voir l’analyse financière</button>
</div>
<div className="agent-thinking-meta">
<span>DOSSIER {clientId.toUpperCase()}</span>
<i/>
<span>AGENTIC-SERVICE</span>
<i/>
<span>INTERROMPU</span>
</div>
</div>
</section>}
    {idle && <p className="lead">L'analyse mobilise deux agents LLM (quota partagé et limité) — elle ne se lance qu'à ta demande, jamais automatiquement en arrivant sur cette page.</p>}
    {loading && <section className="agent-thinking">
<span className="agent-thinking-grid" aria-hidden="true"/>
<span className="agent-hud agent-hud--tl" aria-hidden="true"/>
<span className="agent-hud agent-hud--tr" aria-hidden="true"/>
<span className="agent-hud agent-hud--bl" aria-hidden="true"/>
<span className="agent-hud agent-hud--br" aria-hidden="true"/>
<div className="agent-scanner" aria-hidden="true">
<span className="agent-scanner-sweep"/>
<span className="agent-scanner-ticks"/>
<span className="agent-scanner-ring"/>
<span className="agent-scanner-ring"/>
<span className="agent-brain-ping"/>
<span className="agent-brain-ping"/>
<b/>
<b/>
<b/>
<span className="agent-brain-arc"/>
<span className="agent-brain-orb">
<Icon name="brain" size={34}/>
</span>
</div>
<div className="agent-thinking-body">
<span className="panel-kicker">
<i/>AGENTS EN COURS D'EXÉCUTION</span>
<h2>Les agents analysent le dossier</h2>
<p>Benchmark sectoriel face aux normes du secteur, détection des signaux faibles, croisement des contradictions, puis rédaction d'une décision argumentée.</p>
<div className="agent-thinking-steps" aria-hidden="true">
<span>
<em>01</em>Benchmark sectoriel</span>
<span>
<em>02</em>Signaux et anomalies</span>
<span>
<em>03</em>Décision argumentée</span>
</div>
<div className="agent-thinking-bar" aria-hidden="true">
<i/>
</div>
<div className="agent-thinking-meta" role="status">
<span>DOSSIER {clientId.toUpperCase()}</span>
<i/>
<span>ANALYSE LLM</span>
<i/>
<span>{elapsed}s écoulées</span>
</div>
</div>
</section>}
    {!idle && !loading && !error && <>
<section className="agent-verdict">
<div className="agent-verdict-main">
<div className="agent-verdict-head">
<span className="agent-orb">
<Icon name="brain" size={30}/>
</span>
<div className="agent-verdict-title">
<span className="panel-kicker">CONCLUSION DES AGENTS <i/>
</span>
<h2>{actionTitle}</h2>
<span className="agent-verdict-badge">
<Icon name="clipboard" size={13}/>Décision argumentée</span>
</div>
<svg className="agent-wave" viewBox="0 0 300 118" aria-hidden="true">{Array.from({ length: 5 }, (_, ligne) => Array.from({ length: 44 }, (_, i) => {
  const x = 4 + i * 6.7
  const y = 59 + Math.sin((i / 44) * Math.PI * 2.2 + ligne * 0.62) * (11 + ligne * 4.5) + (ligne - 2) * 6.5
  return <circle key={`${ligne}-${i}`} cx={x} cy={y} r="1.15" opacity={0.12 + 0.5 * Math.sin((i / 44) * Math.PI)}/>
}))}</svg>
</div>{conclusionParagraphs.length > 0 && <div className="agent-quote">
<span className="agent-quote-mark" aria-hidden="true">”</span>
<div className={conclusionOpen ? 'agent-conclusion is-open' : 'agent-conclusion'}>{conclusionParagraphs.map((paragraphe, i) => <p key={i}>{surlignerValeurs(paragraphe)}</p>)}</div>
<button className="text-button agent-conclusion-toggle" aria-expanded={conclusionOpen} onClick={() => setConclusionOpen((v) => !v)}>{conclusionOpen ? 'Réduire la conclusion' : 'Lire la conclusion complète'} <Icon name="arrow" size={15}/>
</button>
</div>}</div>
<aside className="agent-gauge-card" data-tone={riskTone}>
<span className="agent-gauge-title">INDICE DE RISQUE</span>
<div className="risk-gauge" title={`Seuils : accord ≤ ${RISK_SEUIL_ACCORD}, surveillance ≤ ${RISK_SEUIL_SURVEILLANCE}`}>
<svg viewBox="0 0 120 120" aria-hidden="true">
<g transform="rotate(135 60 60)">
<circle className="risk-gauge-track" cx="60" cy="60" r={GAUGE_R} strokeDasharray={`${GAUGE_ARC} 999`}/>{riskScore != null && <circle className="risk-gauge-fill" cx="60" cy="60" r={GAUGE_R} style={{ '--dash': String(gaugeLen(riskScore)) } as React.CSSProperties}/>}</g>{[RISK_SEUIL_ACCORD, RISK_SEUIL_SURVEILLANCE].map((seuil) => { const [x1, y1] = gaugePoint(seuil, GAUGE_R - 7); const [x2, y2] = gaugePoint(seuil, GAUGE_R + 7); return <line className="risk-gauge-tick" key={seuil} x1={x1} y1={y1} x2={x2} y2={y2}/> })}{riskScore != null && <circle className="risk-gauge-cursor" cx={gaugePoint(riskScore, GAUGE_R)[0]} cy={gaugePoint(riskScore, GAUGE_R)[1]} r="5.5"/>}</svg>
<div className="risk-gauge-value">
<strong>{riskScore ?? '—'}</strong>
<small>/ {RISK_ECHELLE}</small>
</div>
</div>
<div className="risk-bands">{([
  ['accord', `≤ ${RISK_SEUIL_ACCORD}`, 'ok'],
  ['a_surveiller', `≤ ${RISK_SEUIL_SURVEILLANCE}`, 'warn'],
  ['refus', `> ${RISK_SEUIL_SURVEILLANCE}`, 'bad'],
] as const).map(([code, borne, tone]) => <div key={code} data-tone={tone} data-actif={decisionCode === code ? '' : undefined}>
<b>{decisionLabels[code]}</b>
<span>{borne}</span>
</div>)}</div>
<span className="risk-bands-legend">Points cumulés par les signaux de risque</span>
</aside>
</section>
<section className="agent-layout">
<article className="panel radar-panel">
<div className="panel-heading">
<div>
<span className="panel-kicker">BENCHMARK SECTORIEL</span>
<h2>Positionnement des ratios</h2>
</div>
{data?.secteur && <span className="sector">{data.secteur}</span>}
</div>
<div className="radar-wrap">{!radarHasData ? <div className="radar-empty">
<span className="radar-empty-mark" aria-hidden="true">
<Icon name="target" size={22}/>
</span>
<b>Positionnement non calculé</b>
<small>Les agents n’ont pas comparé les ratios de ce dossier aux normes du secteur. Relancez l’analyse pour situer l’entreprise sur les quatre axes.</small>
</div> : <svg viewBox="0 0 300 278" className="radar">
<defs>
<radialGradient id="radar-fill" cx="50%" cy="50%" r="50%">
<stop offset="0%" stopColor="#ff4054" stopOpacity=".42"/>
<stop offset="100%" stopColor="#ff4054" stopOpacity=".08"/>
</radialGradient>
<filter id="radar-glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="4" result="blur"/>
<feMerge>
<feMergeNode in="blur"/>
<feMergeNode in="SourceGraphic"/>
</feMerge>
</filter>
</defs>
<circle className="radar-halo" cx={RADAR_CENTER[0]} cy={RADAR_CENTER[1]} r={RADAR_MAX_R}/>{RADAR_AXES.map((axis, i) => { const [x, y] = radarPoint(RADAR_CENTER, RADAR_MAX_R, (360 / RADAR_AXES.length) * i, 100); return <line key={axis.key} className="radar-spoke" x1={RADAR_CENTER[0]} y1={RADAR_CENTER[1]} x2={x} y2={y}/> })}{radarRings.map((ring, i) => <path key={i} className="radar-ring" d={ringPath(ring)} fill="none"/>)}<path className="radar-shape" d={ringPath(radarPolygon)} fill="url(#radar-fill)" stroke="#ff4054" strokeWidth="2" filter="url(#radar-glow)"/>{radarPolygon.map(([x, y], i) => <circle key={i} className="radar-dot" style={{ animationDelay: `${0.55 + i * 0.12}s` } as React.CSSProperties} cx={x} cy={y} r="4.5"/>)}{radarScores.map((s, i) => { const [lx, ly] = radarPoint(RADAR_CENTER, RADAR_MAX_R + 24, (360 / RADAR_AXES.length) * i, 100); return <text key={s.label} className="radar-label" x={lx} y={ly} dy={ly < RADAR_CENTER[1] - 40 ? -2 : ly > RADAR_CENTER[1] + 40 ? 10 : 4} textAnchor={radarAnchor(lx)}>{s.label}{s.pct === null ? ' (n/d)' : ''}</text> })}</svg>}</div>
</article>
<article className="panel agents-panel">
<div className="panel-heading">
<div>
<span className="panel-kicker">TRAVAIL DES AGENTS</span>
<h2>Signaux détectés</h2>
</div>
</div>{signalGroups.map((group, i) => <div className="signal-row" data-tone={group.tone} style={{ '--i': i } as React.CSSProperties} key={group.key}>
<span className="signal-mark">
<Icon name={group.icon} size={16}/>
</span>
<div>
<b>{group.label}</b>
<small>{group.detail}</small>{signalsOpen && group.entries.length > 1 && <ul className="signal-list">{group.entries.slice(1).map((entry, j) => <li key={j}>{entry}</li>)}</ul>}</div>
<strong>{group.count}</strong>
</div>)}{signalsExpandable && <button className="text-button" aria-expanded={signalsOpen} onClick={() => setSignalsOpen((v) => !v)}>{signalsOpen ? 'Réduire les signaux' : `Explorer les ${signalGroups.reduce((n, g) => n + g.entries.length, 0)} signaux`} <Icon name="arrow" size={15}/>
</button>}
</article>
</section>
<section className="agent-bottom">
<article className="panel contribution-panel">
<div className="panel-heading">
<div>
<span className="panel-kicker">EXPLICATION DE LA DÉCISION</span>
<h2>Contributions au risque</h2>
</div>
</div>{contributions.length === 0 && <p className="lead">{loading ? 'Calcul des contributions en cours…' : 'Aucune contribution disponible.'}</p>}{contributions.map((c, i) => { const cls = c.points < 0 ? 'positive' : c.points >= 20 ? 'high' : 'medium'; return <div className="contribution" style={{ '--i': i } as React.CSSProperties} key={c.label}>
<span>{c.label}</span>
<div>
<i className={cls} style={{ width: `${Math.min(Math.abs(c.points) * 2.5, 100)}%` }}/>
</div>
<b className={cls}>{c.points > 0 ? '+' : ''}{c.points}</b>
</div> })}</article>
<article className="panel action-panel">
<span className="panel-kicker">RECOMMANDATION</span>
<h2>{actionTitle}</h2>
<p>{actionText}</p>
<div className="action-list">{actionList.map((label) => <span key={label}>
<Icon name="check" size={15}/>{label}</span>)}</div>
<button className="primary-button" onClick={() => window.open(reportPreviewUrl(clientId), '_blank')}>Voir le rapport complet <Icon name="arrow" size={16}/>
</button>
</article>
</section>
</>}{error && <section className="agent-bottom agent-bottom--solo">
<article className="panel action-panel">
<span className="panel-kicker">RECOMMANDATION</span>
<h2>{actionTitle}</h2>
<p>{actionText}</p>
<div className="action-list">{actionList.map((label) => <span key={label}>
<Icon name="check" size={15}/>{label}</span>)}</div>
<button className="primary-button" onClick={() => window.open(reportPreviewUrl(clientId), '_blank')}>Voir le rapport complet <Icon name="arrow" size={16}/>
</button>
</article>
</section>}</>
}

function App() {
  // null = aucun dossier constitué : UploadPage est la seule chose affichée
  // (pas de sidebar/dashboard) tant qu'un client n'est pas passé par
  // extraction + calcul financier (voir UploadPage.tsx) — le dashboard
  // n'est jamais atteignable en contournant cette étape.
  // L'écran d'amorçage est posé PAR-DESSUS l'application, pas à sa place :
  // le dashboard se monte derrière pendant la séquence, donc rien n'est
  // retardé — l'attente visuelle et le montage se recouvrent.
  const [amorcage, setAmorcage] = useState(true)
  const [clientId, setClientId] = useState<string | null>(null)
  // Atterrit sur "financial" (pas "documents") une fois le dossier prêt :
  // c'est la page qui a une valeur immédiate à la sortie d'UploadPage.
  const [page, setPage] = useState<Page>('financial')

  const splash = amorcage ? <SplashScreen onDone={() => setAmorcage(false)}/> : null

  if (clientId === null) {
    return <>{splash}<UploadPage onReady={(id) => { setClientId(id); setPage('financial') }}/>
</>
  }

  const nav: Array<[Page, string, IconName]> = [['documents', 'Données extraites', 'file'], ['financial', 'Analyse financière', 'chart'], ['agents', 'Risques & agents', 'brain']]
  const content = page === 'documents' ? <DocumentsPage clientId={clientId}/>
    : page === 'financial' ? <FinancialPage clientId={clientId} onGoToAgents={() => setPage('agents')}/>
    : page === 'guide' ? <GuidePage onNavigate={setPage}/>
    : <AgentsPage clientId={clientId} onGoToFinancial={() => setPage('financial')}/>

  return <>{splash}<div className="app-shell">
<aside className="sidebar">
<div className="logo">
<span className="logo-icon">
<img src={devoteamLogo} alt="Devoteam"/>
</span>
<span>Trust<strong>Score</strong>
</span>
</div>
<div className="nav-label">WORKSPACE</div>
<nav>{nav.map(([id, label, icon]) => <button className={page === id ? 'active' : ''} onClick={() => setPage(id)} key={id}>
<Icon name={icon}/>{label}</button>)}</nav>
<button className={page === 'guide' ? 'sidebar-bottom is-active' : 'sidebar-bottom'} onClick={() => setPage('guide')}>
<span className="help-icon">
<Icon name="info" size={16}/>
</span>
<span className="help-text">
<b>Guide de la plateforme</b>
<span>Comment lire un dossier</span>
</span>
</button>
</aside>
<main>
<header>
<div className="breadcrumb">
<Icon name="home" size={16}/>
<span>{page === 'guide' ? 'Documentation' : 'Analyse du dossier'}</span>
<i>/</i>
<b>{page === 'guide' ? 'Guide de la plateforme' : clientId.toUpperCase()}</b>
</div>
<div className="header-actions">
<button className="header-action" onClick={() => setClientId(null)}>
<Icon name="arrowLeft" size={15}/>Changer de dossier</button>
</div>
</header>
<div className="content">{content}</div>
</main>
</div>
</>
}

export default App
