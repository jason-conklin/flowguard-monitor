import { NavLink } from "react-router-dom";

export default function Header() {
  return (
    <header className="app-header">
      <div className="branding">
        <span className="logo-dot" />
        <div>
          <h1>FlowGuard</h1>
          <p>Intelligent Log &amp; Metrics Aggregator</p>
        </div>
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

