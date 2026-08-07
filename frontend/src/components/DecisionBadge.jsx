import "./DecisionBadge.css";

const LABELS = {
  accord: "Accord",
  a_surveiller: "À surveiller",
  refus: "Refus",
};

// `decision` : "accord" | "a_surveiller" | "refus" | null (agent 2 en
// échec, voir routes.py) — null affiché distinctement, jamais confondu
// avec "accord".
export default function DecisionBadge({ decision, size = "md" }) {
  const key = decision && LABELS[decision] ? decision : "inconnu";
  const label = LABELS[decision] || "Non déterminée";

  return (
    <span className={`decision-badge decision-badge--${key} decision-badge--${size}`}>
      <span className="decision-badge__dot" />
      {label}
    </span>
  );
}
