import Tag from "./Tag";
import { splitRatioName, categoryLabel, ratioLabel, formatRatioValue, verdictTone, verdictLabel } from "../utils/ratios";
import "./RatioTable.css";

// Table complète de tous les ratios calculés, groupés par catégorie —
// aucune sélection/filtrage : chaque ratio renvoyé par
// outil_benchmark_sectoriel est affiché (voir la demande explicite d'
// afficher TOUS les ratios, pas une sélection réduite).
export default function RatioTable({ ratios }) {
  if (!ratios || ratios.length === 0) {
    return <p className="ratio-table__empty">Aucun ratio disponible.</p>;
  }

  const groups = {};
  for (const r of ratios) {
    const { category, key } = splitRatioName(r.ratio_name);
    if (!groups[category]) groups[category] = [];
    groups[category].push({ ...r, key });
  }

  return (
    <div className="ratio-table">
      {Object.entries(groups).map(([category, rows]) => (
        <div key={category} className="ratio-table__group">
          <h3 className="ratio-table__group-title">{categoryLabel(category)}</h3>
          <table className="ratio-table__table">
            <thead>
              <tr>
                <th>Ratio</th>
                <th>Valeur</th>
                <th>Verdict</th>
                <th>Référence</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.ratio_name}>
                  <td className="ratio-table__name">{ratioLabel(r.key)}</td>
                  <td className="ratio-table__value">{formatRatioValue(r.key, r.ratio_value)}</td>
                  <td>
                    {r.verdict ? (
                      <Tag tone={verdictTone(r.verdict.verdict)}>{verdictLabel(r.verdict.verdict)}</Tag>
                    ) : (
                      <span className="ratio-table__no-verdict">non normé</span>
                    )}
                  </td>
                  <td className="ratio-table__ref">{r.reference_id || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
