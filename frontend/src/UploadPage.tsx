import { useState } from 'react'
import { extractDossier, getFinancialReport, humanizeError, uploadDocuments } from './api'
import type { UploadEntry } from './api'
import { Icon } from './Icon'
import type { IconName } from './Icon'
import devoteamLogo from './assets/devoteam-logo.webp'

type SingleSlotKey = Exclude<UploadEntry['category'], 'bilan'>

const REQUIRED_SLOTS: Array<{ key: SingleSlotKey; label: string; hint: string; icon: IconName }> = [
  { key: 'fiche_renseignements', label: 'Fiche de renseignements', hint: 'Identité, secteur, capital social', icon: 'user' },
]

const OPTIONAL_SLOTS: Array<{ key: SingleSlotKey; label: string; hint: string; icon: IconName }> = [
  { key: 'demande_credit', label: 'Demande de crédit', hint: 'Montant, objet, apport', icon: 'file' },
  { key: 'attestation_dgi', label: 'Attestation DGI', hint: 'Conformité fiscale', icon: 'check' },
  { key: 'attestation_cnss', label: 'Attestation CNSS', hint: 'Conformité sociale', icon: 'check' },
  { key: 'releve_attijariwafa', label: 'Relevé bancaire — Attijariwafa', hint: 'Mouvements, soldes', icon: 'bank' },
  { key: 'releve_cih', label: 'Relevé bancaire — CIH', hint: 'Mouvements, soldes', icon: 'bank' },
  { key: 'amortissement', label: "Tableau d'amortissement", hint: 'Crédits en cours', icon: 'chart' },
  { key: 'centrale_risques', label: 'Centrale des risques (BAM)', hint: 'Incidents de paiement', icon: 'alert' },
  { key: 'garanties', label: 'Garanties proposées', hint: 'Hypothèque, nantissement, caution', icon: 'bank' },
]

const ALL_SLOTS = [...REQUIRED_SLOTS, ...OPTIONAL_SLOTS]

interface BilanRow {
  file: File | null
  year: string
}

type Stage = 'idle' | 'uploading' | 'extracting' | 'calculating' | 'error' | 'done'

const STAGES: Array<{ key: Exclude<Stage, 'idle' | 'error' | 'done'>; label: string }> = [
  { key: 'uploading', label: 'Envoi des documents' },
  { key: 'extracting', label: 'Extraction (document-service)' },
  { key: 'calculating', label: 'Calcul des ratios (financial-service)' },
]

const WIZARD_STEPS = ['Informations', 'Documents obligatoires', 'Documents complémentaires', 'Vérification']

const CURRENT_YEAR = new Date().getFullYear()
const YEAR_OPTIONS = Array.from({ length: 7 }, (_, i) => String(CURRENT_YEAR - i))

function formatSize(bytes: number): string {
  return bytes >= 1_000_000 ? `${(bytes / 1_000_000).toFixed(1)} Mo` : `${Math.round(bytes / 1024)} Ko`
}

function Stepper({ current }: { current: number }) {
  return <ol className="wizard-steps">
    {WIZARD_STEPS.map((label, i) => <li className={i < current ? 'done' : i === current ? 'active' : undefined} key={label}>
      <span className="wizard-step-circle">{i < current ? <Icon name="check" size={13}/> : i + 1}</span>
      <span className="wizard-step-label">{label}</span>
      {i < WIZARD_STEPS.length - 1 && <i className="wizard-step-line"/>}
    </li>)}
  </ol>
}

function Dropzone({ accept, label, disabled, onSelect }: { accept: string; label: string; disabled: boolean; onSelect: (file: File | null) => void }) {
  return <label className="doc-dropzone">
    <input type="file" accept={accept} disabled={disabled} onChange={(e) => onSelect(e.target.files?.[0] ?? null)}/>
    <Icon name="download" size={15}/>
    <span>Déposez votre fichier ici</span>
    <small>ou</small>
    <span className="doc-dropzone-button">{label}</span>
  </label>
}

function FileSlot({ label, hint, icon = 'file', required, file, onSelect, disabled }: { label: string; hint: string; icon?: IconName; required?: boolean; file: File | null; onSelect: (file: File | null) => void; disabled: boolean }) {
  return <div className={`doc-slot${file ? ' filled' : ''}`}>
    <div className="doc-slot-head">
      <span className="doc-slot-icon"><Icon name={icon} size={17}/></span>
      <div><b>{label}</b><small>{hint}</small></div>
      {required && <span className="doc-badge">Requis</span>}
    </div>
    {file
      ? <div className="doc-chip"><Icon name="check" size={13}/><span className="doc-chip-name">{file.name}</span><span className="doc-chip-size">{formatSize(file.size)}</span><button type="button" className="doc-chip-remove" onClick={() => onSelect(null)} disabled={disabled} title="Retirer ce fichier"><Icon name="x" size={13}/></button></div>
      : <Dropzone accept="application/pdf" label="Choisir un fichier PDF" disabled={disabled} onSelect={onSelect}/>}
  </div>
}

/**
 * Première page de l'app : dépose les PDF du dossier avant d'accéder au
 * dashboard. Enchaîne upload -> extraction -> calcul financier dans le
 * même parcours ("on doit simplement déclencher le financial service",
 * pas une étape de visualisation intermédiaire) : l'agent d'analyse
 * (agentic-service, coûteux en quota Groq) reste volontairement une
 * action séparée, déclenchée explicitement sur la page Risques & agents.
 *
 * Parcours en étapes (inspiré d'un wizard d'upload administratif classique :
 * informations -> pièces jointes -> vérification -> envoi) plutôt qu'un
 * long formulaire à défilement — plus lisible pour ~10 documents distincts.
 */
export default function UploadPage({ onReady }: { onReady: (clientId: string) => void }) {
  const [step, setStep] = useState(0)
  const [clientId, setClientId] = useState('')
  const [slots, setSlots] = useState<Partial<Record<SingleSlotKey, File>>>({})
  const [bilans, setBilans] = useState<BilanRow[]>([{ file: null, year: '' }])
  const [stage, setStage] = useState<Stage>('idle')
  const [error, setError] = useState<string | null>(null)

  const setSlotFile = (key: SingleSlotKey, file: File | null) => {
    setSlots((prev) => {
      const next = { ...prev }
      if (file) next[key] = file
      else delete next[key]
      return next
    })
  }

  const setBilan = (index: number, patch: Partial<BilanRow>) => {
    setBilans((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  }

  const filledBilans = bilans.filter((b) => b.file !== null)
  const bilansValid = filledBilans.length > 0 && filledBilans.every((b) => /^20\d{2}$/.test(b.year))
  const busy = stage !== 'idle' && stage !== 'error' && stage !== 'done'

  const stepValid = [clientId.trim().length > 0, !!slots.fiche_renseignements && bilansValid, true, true]
  const canGoNext = stepValid[step]

  const entries: UploadEntry[] = [
    ...Object.entries(slots).map(([category, file]) => ({ file: file as File, category: category as SingleSlotKey, year: '' })),
    ...filledBilans.map((b) => ({ file: b.file as File, category: 'bilan' as const, year: b.year })),
  ]

  const handleSubmit = async () => {
    if (!bilansValid || busy) return
    const id = clientId.trim()
    setError(null)
    try {
      setStage('uploading')
      await uploadDocuments(id, entries)
      setStage('extracting')
      await extractDossier(id)
      setStage('calculating')
      await getFinancialReport(id)
      setStage('done')
      onReady(id)
    } catch (err) {
      setStage('error')
      setError(humanizeError(err))
    }
  }

  const stageIndex = STAGES.findIndex((s) => s.key === stage)

  return <section className="hero-page">
    <div className="upload-top">
      <div className="logo"><span className="logo-icon"><img src={devoteamLogo} alt="Devoteam"/></span><span>Trust<strong>Score</strong></span></div>
      <div className="hero upload-hero"><div className="upload-hero-icon"><Icon name="folder" size={20}/></div><div><h1>Constituer le dossier client</h1><p className="lead">Déposez les pièces du dossier de crédit. L'extraction et le calcul des ratios se lancent automatiquement une fois le dossier envoyé.</p></div></div>
    </div>

    <div className="panel upload-panel">
      <Stepper current={step}/>

      {step === 0 && <div className="wizard-pane">
        <h2 className="wizard-pane-title">Identifier le dossier</h2>
        <p className="lead">Cet identifiant sert de référence pour toutes les pièces du dossier et pour les analyses qui suivront.</p>
        <label className="upload-field"><span>Identifiant client<em>*</em></span><input value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="ex: data" disabled={busy} autoFocus/></label>
      </div>}

      {step === 1 && <div className="wizard-pane">
        <div className="wizard-pane-header">
          <div><h2 className="wizard-pane-title">Documents obligatoires</h2><p className="lead">La fiche de renseignements et au moins un exercice (bilan) sont nécessaires pour lancer le calcul.</p></div>
          <div className="upload-info-box"><Icon name="info" size={15}/><div><b>Formats acceptés : PDF</b><span>Taille max. par fichier : 10 Mo</span></div></div>
        </div>
        <div className="upload-grid">
          {REQUIRED_SLOTS.map(({ key, label, hint, icon }) => <FileSlot key={key} label={label} hint={hint} icon={icon} required file={slots[key] ?? null} onSelect={(f) => setSlotFile(key, f)} disabled={busy}/>)}
        </div>

        <div className="upload-bilans">
          <span className="upload-bilans-title">Bilans & CPC<em>*</em> <small>(au moins un exercice)</small></span>
          {bilans.map((row, i) => <div className="bilan-row" key={i}>
            {row.file
              ? <div className="doc-chip bilan-chip"><Icon name="check" size={13}/><span className="doc-chip-name">{row.file.name}</span><span className="doc-chip-size">{formatSize(row.file.size)}</span><button type="button" className="doc-chip-remove" onClick={() => setBilan(i, { file: null })} disabled={busy} title="Retirer ce fichier"><Icon name="x" size={13}/></button></div>
              : <Dropzone accept="application/pdf" label="Choisir un bilan PDF" disabled={busy} onSelect={(f) => setBilan(i, { file: f })}/>}
            <label className="bilan-year-field"><span>Année de l'exercice</span><select className="bilan-year" value={row.year} onChange={(e) => setBilan(i, { year: e.target.value })} disabled={busy}>
              <option value="">Sélectionner une année</option>
              {YEAR_OPTIONS.map((y) => <option key={y} value={y}>{y}</option>)}
            </select></label>
            {bilans.length > 1 && <button type="button" className="icon-button" onClick={() => setBilans((prev) => prev.filter((_, idx) => idx !== i))} disabled={busy} title="Retirer cet exercice"><Icon name="x" size={14}/></button>}
          </div>)}
          <button type="button" className="text-button" onClick={() => setBilans((prev) => [...prev, { file: null, year: '' }])} disabled={busy}>+ Ajouter un exercice</button>
        </div>
      </div>}

      {step === 2 && <div className="wizard-pane">
        <h2 className="wizard-pane-title">Documents complémentaires</h2>
        <p className="lead">Facultatifs, mais chacun affine l'analyse (DSCR, conformité, cohérence bancaire). Passable sans rien sélectionner.</p>
        <div className="upload-grid">
          {OPTIONAL_SLOTS.map(({ key, label, hint, icon }) => <FileSlot key={key} label={label} hint={hint} icon={icon} file={slots[key] ?? null} onSelect={(f) => setSlotFile(key, f)} disabled={busy}/>)}
        </div>
      </div>}

      {step === 3 && <div className="wizard-pane">
        <h2 className="wizard-pane-title">Vérification</h2>
        <p className="lead">{entries.length} document{entries.length > 1 ? 's' : ''} prêt{entries.length > 1 ? 's' : ''} pour le dossier <b>{clientId.trim() || '—'}</b>.</p>

        <table className="doc-review-table">
          <thead><tr><th>Document</th><th>Catégorie</th><th>Taille</th></tr></thead>
          <tbody>
            {ALL_SLOTS.filter(({ key }) => slots[key]).map(({ key, label }) => <tr key={key}><td>{slots[key]!.name}</td><td>{label}</td><td>{formatSize(slots[key]!.size)}</td></tr>)}
            {filledBilans.map((b, i) => <tr key={`bilan-${i}`}><td>{b.file!.name}</td><td>Bilan {b.year || '?'}</td><td>{formatSize(b.file!.size)}</td></tr>)}
          </tbody>
        </table>

        {!busy && stage !== 'done' && <button className="primary-button" onClick={handleSubmit} disabled={!bilansValid}>Envoyer et lancer le calcul</button>}

        {stage !== 'idle' && <ol className="progress-stages">
          {STAGES.map((s, i) => <li className={stage === 'error' ? undefined : i < stageIndex || stage === 'done' ? 'done' : i === stageIndex ? 'active' : undefined} key={s.key}>
            <span className="progress-stage-dot">{(i < stageIndex || stage === 'done') ? <Icon name="check" size={12}/> : i + 1}</span>{s.label}
          </li>)}
        </ol>}

        {error && <p className="lead upload-error">{error} <button className="text-button" onClick={handleSubmit}>Réessayer</button></p>}
      </div>}

      <div className="wizard-nav">
        {step > 0 && <button type="button" className="outline-button" onClick={() => setStep((s) => s - 1)} disabled={busy}><Icon name="arrowLeft" size={15}/>Précédent</button>}
        {step < WIZARD_STEPS.length - 1 && <button type="button" className="primary-button" onClick={() => setStep((s) => s + 1)} disabled={!canGoNext}>Suivant<Icon name="arrow" size={15}/></button>}
      </div>
    </div>
  </section>
}
