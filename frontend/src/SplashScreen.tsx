import { useEffect, useState } from 'react'
import { Icon } from './Icon'

/**
 * Séquence d'amorçage.
 *
 * Le déroulé rejoue la chaîne réelle d'un dossier : les pièces convergent
 * (particules aspirées), l'analyse tourne autour d'elles (orbites et
 * balayage), puis le verdict s'allume (noyau, onde de choc, marque).
 * La ligne d'état nomme les quatre étapes au moment où elles se jouent.
 *
 * Toute la chorégraphie est portée par des délais CSS ; un seul `setTimeout`
 * marque la fin. La séquence est interruptible d'un clic ou d'une touche —
 * un écran d'attente qu'on ne peut pas passer devient vite pénible.
 */

const DUREE_SEQUENCE = 4800
const DUREE_SORTIE = 700

/** Périmètre d'ellipse (Ramanujan) : longueur exacte du trait à tracer. */
function perimetreEllipse(rx: number, ry: number): number {
  return Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
}

const CENTRE = 210
const ORBITES = [
  { rx: 186, ry: 64, duree: 30, sens: 'normal', opacite: 0.3, retard: 0 },
  { rx: 150, ry: 128, duree: 22, sens: 'reverse', opacite: 0.24, retard: 0.14 },
  { rx: 118, ry: 96, duree: 16, sens: 'normal', opacite: 0.4, retard: 0.28 },
]

const NB_PARTICULES = 34
const ETAPES = ['EXTRACTION', 'CALCULS', 'BENCHMARK', 'DÉCISION']

export default function SplashScreen({ onDone }: { onDone: () => void }) {
  const [sortie, setSortie] = useState(false)

  useEffect(() => {
    const passer = () => setSortie(true)
    const fin = window.setTimeout(passer, DUREE_SEQUENCE)
    window.addEventListener('keydown', passer)
    return () => {
      window.clearTimeout(fin)
      window.removeEventListener('keydown', passer)
    }
  }, [])

  useEffect(() => {
    if (!sortie) return
    const t = window.setTimeout(onDone, DUREE_SORTIE)
    return () => window.clearTimeout(t)
  }, [sortie, onDone])

  return <div
    className={sortie ? 'splash is-leaving' : 'splash'}
    onClick={() => setSortie(true)}
    role="presentation"
  >
<span className="splash-grid" aria-hidden="true"/>
<span className="splash-vignette" aria-hidden="true"/>
<span className="splash-flash" aria-hidden="true"/>

<span className="splash-hud splash-hud--tl" aria-hidden="true"/>
<span className="splash-hud splash-hud--tr" aria-hidden="true"/>
<span className="splash-hud splash-hud--bl" aria-hidden="true"/>
<span className="splash-hud splash-hud--br" aria-hidden="true"/>

<div className="splash-stage" aria-hidden="true">
<div className="splash-particles">{Array.from({ length: NB_PARTICULES }, (_, i) => <i
  key={i}
  style={{ '--angle': `${(360 / NB_PARTICULES) * i}deg`, '--retard': `${0.055 * (i % 11)}s` } as React.CSSProperties}
/>)}</div>

<svg className="splash-orbits" viewBox="0 0 420 420">{ORBITES.map((orbite) => <g
  key={orbite.rx}
  className="splash-orbit"
  style={{ '--duree': `${orbite.duree}s`, '--sens': orbite.sens, '--retard': `${orbite.retard}s` } as React.CSSProperties}
>
<ellipse
  cx={CENTRE}
  cy={CENTRE}
  rx={orbite.rx}
  ry={orbite.ry}
  style={{ '--perimetre': String(perimetreEllipse(orbite.rx, orbite.ry)), opacity: orbite.opacite } as React.CSSProperties}
/>
<circle className="splash-satellite" cx={CENTRE + orbite.rx} cy={CENTRE} r="3.5"/>
</g>)}</svg>

<span className="splash-sweep"/>
<span className="splash-burst"/>
<span className="splash-burst splash-burst--2"/>
<span className="splash-ticks"/>
<span className="splash-core-arc"/>
<span className="splash-core">
<Icon name="brain" size={38}/>
</span>
</div>

<div className="splash-mark">
<h1>Trust<strong>Score</strong>
</h1>
<p>Analyse du risque de crédit</p>
</div>

<div className="splash-readout" aria-hidden="true">{ETAPES.map((etape, i) => <span
  key={etape}
  style={{ '--i': i } as React.CSSProperties}
>{etape}</span>)}</div>

<div className="splash-progress" aria-hidden="true">
<i/>
</div>
<span className="splash-skip">Cliquez pour passer</span>
</div>
}
