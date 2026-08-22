import { useState } from 'react'
import { Icon } from './Icon'
import type { IconName } from './Icon'
import { RATIO_DEFS, formatRatioValue } from './lib/financialRatios'

type Destination = 'documents' | 'financial' | 'agents'

/** Le parcours réel d'un dossier, de l'upload au rapport. */
const STEPS: Array<{ icon: IconName; kicker: string; title: string; text: string }> = [
  {
    icon: 'download',
    kicker: 'ÉTAPE 01',
    title: 'Dépôt du dossier',
    text: 'Vous déposez les PDF du client en les rangeant par catégorie : fiche de renseignements, demande de crédit, attestations DGI et CNSS, bilans (un fichier par exercice), relevés Attijariwafa et CIH, tableau d’amortissement, centrale des risques et garanties.',
  },
  {
    icon: 'file',
    kicker: 'ÉTAPE 02',
    title: 'Extraction',
    text: 'Chaque pièce est lue et convertie en champs tracés — la valeur, le document dont elle vient et sa page. Ce qui n’est pas trouvé reste vide : la plateforme ne comble jamais un trou par une estimation.',
  },
  {
    icon: 'chart',
    kicker: 'ÉTAPE 03',
    title: 'Calculs déterministes',
    text: 'Ratios, score Altman Z et DSCR sont produits par formules, sans aucune IA. Le même dossier donne toujours exactement le même résultat, et chaque valeur est rattachable à ses postes de bilan.',
  },
  {
    icon: 'brain',
    kicker: 'ÉTAPE 04',
    title: 'Analyse des agents',
    text: 'Deux agents comparent les ratios aux normes du secteur, croisent les signaux faibles et rédigent une décision motivée. C’est la seule étape qui mobilise des LLM — et elle ne part jamais toute seule.',
  },
]

const SERVICES: Array<{ icon: IconName; name: string; port: string; role: string }> = [
  { icon: 'file', name: 'document-service', port: ':8000', role: 'Reçoit les PDF, en extrait les champs tracés et conserve le dossier dans MongoDB.' },
  { icon: 'chart', name: 'financial-service', port: ':8001', role: 'Calcule les ratios, le score Altman Z, le DSCR et la couverture par les garanties. Aucune IA.' },
  { icon: 'brain', name: 'agentic-service', port: ':8002', role: 'Fait tourner les deux agents, le benchmark sectoriel et la décision argumentée.' },
  { icon: 'download', name: 'report-service', port: ':8003', role: 'Assemble le rapport de crédit complet et le rend consultable en PDF.' },
]

const CATEGORY_LABELS: Record<string, { label: string; icon: IconName }> = {
  liquidite: { label: 'Liquidité', icon: 'droplet' },
  solvabilite: { label: 'Solvabilité', icon: 'bank' },
  rentabilite: { label: 'Rentabilité', icon: 'chartUp' },
  activite: { label: 'Activité', icon: 'clock' },
  cash_flow: { label: 'Flux de trésorerie', icon: 'zap' },
}

const FAQ: Array<{ q: string; a: string }> = [
  {
    q: 'Pourquoi l’analyse des agents ne démarre-t-elle pas automatiquement ?',
    a: 'Contrairement aux pages Données extraites et Analyse financière, qui se chargent seules, elle consomme un quota LLM partagé et limité. Elle reste donc une action volontaire : rien ne part en arrivant sur la page.',
  },
  {
    q: 'Que se passe-t-il si une pièce manque au dossier ?',
    a: 'Les champs concernés restent vides et s’affichent « — ». Les indicateurs qui en dépendent ne sont pas calculés du tout, plutôt que d’être estimés à partir d’hypothèses. Un dossier incomplet donne donc moins de résultats, jamais de résultats approximatifs.',
  },
  {
    q: 'D’où viennent les seuils utilisés pour juger un ratio ?',
    a: 'Des fiches de normes sectorielles que l’agent consulte déjà pour son benchmark. Ces fiches sont marquées [SIMULÉ] : ce sont des repères de plausibilité construits pour l’exercice, pas des statistiques de marché réelles. Les indicateurs qu’aucune fiche ne couvre sont affichés en valeur brute, sans verdict.',
  },
  {
    q: 'Les calculs financiers passent-ils par un modèle de langage ?',
    a: 'Non. Tout ce qui est chiffré — ratios, Altman Z, DSCR, garanties — sort de formules déterministes. Les LLM n’interviennent que pour interpréter ces chiffres sur la page Risques & agents, et leur décision cite toujours les indicateurs sur lesquels elle s’appuie.',
  },
  {
    q: 'Comment récupérer le rapport complet ?',
    a: 'Le bouton « Voir le rapport complet », en bas du panneau Recommandation de la page Risques & agents, ouvre le rapport de crédit dans un nouvel onglet une fois l’analyse terminée.',
  },
]

export default function GuidePage({ onNavigate }: { onNavigate: (page: Destination) => void }) {
  const [open, setOpen] = useState<number | null>(0)

  // Construit depuis RATIO_DEFS : la page suit automatiquement les
  // indicateurs réellement implémentés, sans liste recopiée à la main.
  const families = Object.entries(CATEGORY_LABELS)
    .map(([key, meta]) => ({ key, ...meta, defs: RATIO_DEFS.filter((d) => d.category === key) }))
    .filter((family) => family.defs.length > 0)
  const primaryCount = RATIO_DEFS.filter((d) => d.primary).length
  const scoredCount = RATIO_DEFS.filter((d) => d.threshold !== undefined).length

  const shortcuts: Array<{ page: Destination; icon: IconName; label: string; text: string }> = [
    { page: 'documents', icon: 'file', label: 'Données extraites', text: 'Les pièces du dossier et ce qui en a été lu' },
    { page: 'financial', icon: 'chart', label: 'Analyse financière', text: 'Ratios, Altman Z et capacité de remboursement' },
    { page: 'agents', icon: 'brain', label: 'Risques & agents', text: 'Benchmark sectoriel, signaux et décision' },
  ]

  return <>
<section className="hero">
<div>
<p className="eyebrow">TRUSTSCORE <span>•</span> DOCUMENTATION</p>
<h1>Guide de la plateforme</h1>
<p className="lead">Comment un dossier de crédit traverse la chaîne, ce qui est calculé à chaque étape, et où s’arrête la part de l’IA.</p>
</div>
</section>

<section className="guide-flow">
<div className="guide-flow-rail" aria-hidden="true">
<i/>
</div>{STEPS.map((step, i) => <article className="guide-step" style={{ '--i': i } as React.CSSProperties} key={step.title}>
<span className="guide-step-icon">
<Icon name={step.icon} size={19}/>
</span>
<span className="guide-step-kicker">{step.kicker}</span>
<h3>{step.title}</h3>
<p>{step.text}</p>
</article>)}</section>

<section className="guide-section">
<div className="guide-section-head">
<span className="panel-kicker">SOUS LE CAPOT</span>
<h2>Quatre services, une chaîne</h2>
<p className="lead">Chaque étape est portée par un service indépendant : si l’un tombe, les autres continuent de répondre avec ce qu’ils ont déjà.</p>
</div>
<div className="guide-services">{SERVICES.map((service, i) => <article className="guide-service" style={{ '--i': i } as React.CSSProperties} key={service.name}>
<span className="guide-service-icon">
<Icon name={service.icon} size={17}/>
</span>
<div>
<b>{service.name}<em>{service.port}</em>
</b>
<p>{service.role}</p>
</div>
</article>)}</div>
</section>

<section className="guide-section">
<div className="guide-section-head">
<span className="panel-kicker">CE QUI EST CALCULÉ</span>
<h2>{RATIO_DEFS.length} indicateurs, {families.length} familles</h2>
<p className="lead">Sur la page <b>Analyse financière</b>, le tableau « Ratios clés » n’en montre que six au départ — le bouton « Tous les ratios » déplie les autres. Chaque indicateur est comparé à un seuil de référence, sauf ceux qu’aucune fiche sectorielle ne couvre : ceux-là restent en valeur brute, sans verdict inventé.</p>
</div>
<div className="guide-stats">
<div>
<strong>{primaryCount}</strong>
<span>visibles dès l’ouverture du tableau</span>
</div>
<div>
<strong>{RATIO_DEFS.length - primaryCount}</strong>
<span>ajoutés au clic sur « Tous les ratios »</span>
</div>
<div>
<strong>{scoredCount}</strong>
<span>comparés à un seuil, avec verdict</span>
</div>
<div>
<strong>{RATIO_DEFS.length - scoredCount}</strong>
<span>affichés sans verdict, faute de référence</span>
</div>
</div>
<div className="guide-families">{families.map((family, i) => <article className="guide-family" style={{ '--i': i } as React.CSSProperties} key={family.key}>
<div className="guide-family-head">
<span className="guide-family-icon">
<Icon name={family.icon} size={16}/>
</span>
<b>{family.label}</b>
<em>{family.defs.length}</em>
</div>
<ul className="guide-metrics">{family.defs.map((def) => <li className={def.primary ? 'is-primary' : undefined} key={def.key} title={def.description}>
<span className="guide-metric-name">{def.label}</span>{def.threshold === undefined
  ? <span className="guide-metric-ref is-raw">valeur brute</span>
  : <span className="guide-metric-ref">{def.direction === 'max' ? '≤' : '≥'} {formatRatioValue(def.threshold, def.unit)}</span>}</li>)}</ul>
</article>)}</div>
<p className="guide-legend">
<i/> visible d’emblée
<i className="is-muted"/> apparaît au clic sur « Tous les ratios »
<b>≥ / ≤</b> le seuil doit être dépassé / ne pas être dépassé</p>
</section>

<section className="guide-section">
<div className="guide-section-head">
<span className="panel-kicker">QUESTIONS FRÉQUENTES</span>
<h2>Ce qu’il faut savoir avant de décider</h2>
</div>
<div className="guide-faq">{FAQ.map((item, i) => <div className={open === i ? 'guide-faq-item is-open' : 'guide-faq-item'} key={item.q}>
<button aria-expanded={open === i} onClick={() => setOpen(open === i ? null : i)}>
<span>{item.q}</span>
<i aria-hidden="true"/>
</button>
<div className="guide-faq-body">
<p>{item.a}</p>
</div>
</div>)}</div>
</section>

<section className="guide-shortcuts">{shortcuts.map((shortcut) => <button className="guide-shortcut" onClick={() => onNavigate(shortcut.page)} key={shortcut.page}>
<span className="guide-shortcut-icon">
<Icon name={shortcut.icon} size={18}/>
</span>
<b>{shortcut.label}</b>
<small>{shortcut.text}</small>
<Icon name="arrow" size={15}/>
</button>)}</section>
</>
}
