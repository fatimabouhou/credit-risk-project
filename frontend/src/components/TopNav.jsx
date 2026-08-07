import { Link, useLocation } from "react-router-dom";
import "./TopNav.css";

export default function TopNav({ clientId }) {
  const location = useLocation();

  return (
    <header className="topnav">
      <Link to="/nouvelle-analyse" className="topnav__brand">
        <span className="topnav__mark">
          <svg viewBox="0 0 24 24" width="18" height="18">
            <polygon points="12,1.5 22,6.5 22,17.5 12,22.5 2,17.5 2,6.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M7 12.5 L10.5 16 L17 8.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        Credit Risk Intelligence
      </Link>

      <nav className="topnav__links">
        <Link
          to="/nouvelle-analyse"
          className={`topnav__link ${location.pathname === "/nouvelle-analyse" ? "topnav__link--active" : ""}`}
        >
          Nouvelle analyse
        </Link>
        {clientId && (
          <Link
            to={`/historique/${clientId}`}
            className={`topnav__link ${location.pathname.startsWith("/historique") ? "topnav__link--active" : ""}`}
          >
            Historique
          </Link>
        )}
      </nav>

      <span className="topnav__brand-footer">Devoteam Africa</span>
    </header>
  );
}
