import "./Section.css";

export default function Section({ title, subtitle, right, children }) {
  return (
    <section className="section">
      <div className="section__header">
        <div>
          <h2 className="section__title">{title}</h2>
          {subtitle && <p className="section__subtitle">{subtitle}</p>}
        </div>
        {right}
      </div>
      <div className="section__body">{children}</div>
    </section>
  );
}
