import { NavLink } from "react-router-dom";

export default function NavBar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${isActive ? "text-primary" : "text-muted hover:text-text"}`;

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
        <NavLink to="/" className="text-lg font-semibold tracking-tight text-text">
          Search<span className="text-primary">Forge</span>
        </NavLink>
        <nav className="flex gap-6" aria-label="Main navigation">
          <NavLink to="/" className={linkClass} end>
            Search
          </NavLink>
          <NavLink to="/admin" className={linkClass}>
            Admin
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
