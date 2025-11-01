import { NavLink } from "react-router-dom";

export default function Header() {
  return (
    <header className="app-header">
      <div className="branding">
        <NavLink to="/" className="branding-link" end>
          <img
            src="/flowguard_logo.png"
            alt="FlowGuard – Intelligent Log & Metrics Aggregator"
            className="branding-logo"
          />
        </NavLink>
      </div>
      <nav className="nav-links">
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/explorer">Explorer</NavLink>
        <NavLink to="/settings">Settings</NavLink>
      </nav>
    </header>
  );
}
