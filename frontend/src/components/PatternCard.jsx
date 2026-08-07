import Tag, { NIVEAU_RISQUE_TONE } from "./Tag";
import "./PatternCard.css";

export default function PatternCard({ pattern }) {
  return (
    <div className="pattern-card">
      <div className="pattern-card__header">
        <span className="pattern-card__id">{pattern.id}</span>
        <Tag tone={NIVEAU_RISQUE_TONE[pattern.niveau_risque] || "neutral"}>{pattern.niveau_risque}</Tag>
      </div>
      <h4 className="pattern-card__title">{pattern.titre}</h4>
      <p className="pattern-card__diagnostic">{pattern.diagnostic}</p>
      {pattern.hypotheses?.length > 0 && (
        <p className="pattern-card__hypothesis">
          <span>Hypothèse possible :</span> {pattern.hypotheses[0]}
        </p>
      )}
    </div>
  );
}
