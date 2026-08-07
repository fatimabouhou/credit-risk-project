import "./Tag.css";

// Petit badge coloré générique — réutilisé pour niveau_risque (patterns),
// severite (anomalies), zone Altman, verdicts de ratios. `tone` fixe la
// couleur, le texte affiché reste celui du back-end (jamais reformulé).
export default function Tag({ tone = "neutral", children }) {
  return <span className={`tag tag--${tone}`}>{children}</span>;
}

// Mappings partagés — un seul endroit qui décide "élevé"/"elevee"/
// "distress" -> couleur, pour ne pas le refaire dans chaque page.
export const NIVEAU_RISQUE_TONE = {
  "élevé": "danger",
  "modéré": "warning",
  "faible": "success",
};

export const SEVERITE_TONE = {
  elevee: "danger",
  a_surveiller: "warning",
};

export const ALTMAN_ZONE_TONE = {
  distress: "danger",
  grey: "warning",
  safe: "success",
};
