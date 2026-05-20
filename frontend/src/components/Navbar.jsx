import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Check, ChevronDown, Languages, ShieldCheck } from "lucide-react";
import clsx from "clsx";
import { useI18n } from "../context/I18nContext.jsx";

/* ---------- Logo ---------- */
function Logo() {
  return (
    <Link
      to="/"
      className="group flex items-center gap-2.5"
      aria-label="Deeptection home"
    >
      <span
        className="grid h-9 w-9 place-items-center rounded-xl bg-ink text-paper-raised
                   shadow-soft ring-1 ring-black/10 transition group-hover:scale-105"
      >
        <ShieldCheck size={18} strokeWidth={2.2} />
      </span>
      <span className="font-display text-xl font-semibold tracking-tight">
        Deeptection
      </span>
    </Link>
  );
}

/* ---------- Nav item ---------- */
function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        clsx(
          "relative rounded-full px-3 py-2 text-sm transition",
          isActive ? "text-ink font-medium" : "text-ink-muted hover:text-ink"
        )
      }
    >
      {({ isActive }) => (
        <>
          <span>{label}</span>
          {isActive && (
            <span className="absolute -bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-accent" />
          )}
        </>
      )}
    </NavLink>
  );
}

/* ---------- Language dropdown ---------- */
function LanguageMenu() {
  const { lang, setLang, locales, meta, dir } = useI18n();
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef(null);

  // Close on outside click or Escape
  useEffect(() => {
    if (!open) return;
    function onDocClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    function onKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const current = meta[lang] || meta.en;
  // In RTL, align the dropdown to the start (right edge). In LTR, align to right as usual.
  const alignClass = dir === "rtl" ? "start-0" : "end-0";

  return (
    <div ref={wrapperRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="btn-pill !py-2 !px-3 text-xs"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select language"
      >
        <Languages size={14} />
        <span className="hidden sm:inline">{current.nativeLabel}</span>
        <ChevronDown
          size={12}
          className={clsx("transition", open && "rotate-180")}
        />
      </button>

      {open && (
        <ul
          role="listbox"
          className={clsx(
            "absolute mt-2 min-w-[12rem] rounded-xl bg-paper-raised p-1 shadow-card ring-1 ring-black/5 z-50",
            alignClass
          )}
        >
          {locales.map((code) => {
            const m = meta[code];
            const selected = code === lang;
            return (
              <li key={code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  onClick={() => {
                    setLang(code);
                    setOpen(false);
                  }}
                  className={clsx(
                    "flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm transition",
                    selected
                      ? "bg-paper-sunken font-medium"
                      : "hover:bg-paper-sunken"
                  )}
                >
                  <span className="flex flex-col items-start">
                    <span>{m.nativeLabel}</span>
                    {m.nativeLabel !== m.label && (
                      <span className="text-[11px] text-ink-subtle">
                        {m.label}
                      </span>
                    )}
                  </span>
                  {selected && (
                    <Check size={14} className="text-accent" strokeWidth={2.5} />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/* ---------- Navbar ---------- */
export default function Navbar() {
  const { t } = useI18n();
  const loc = useLocation();
  const compact = loc.pathname === "/result";

  return (
    <header
      className={clsx(
        "sticky top-0 z-30 border-b border-black/5",
        compact ? "py-2" : "py-3"
      )}
    >
      <div className="container-app flex items-center justify-between gap-3">
        <Logo />

        <nav className="hidden items-center gap-1 md:flex">
          <NavItem to="/"        label={t("nav.home")} />
          <NavItem to="/analyze" label={t("nav.analyze")} />
          <NavItem to="/history" label={t("nav.history")} />
          <NavItem to="/about"   label={t("nav.about")} />
        </nav>

        <div className="flex items-center gap-2">
          <LanguageMenu />
        </div>
      </div>

      {/* Mobile nav */}
      <div className="container-app mt-2 flex gap-1 overflow-x-auto pb-1 md:hidden">
        <NavItem to="/"        label={t("nav.home")} />
        <NavItem to="/analyze" label={t("nav.analyze")} />
        <NavItem to="/history" label={t("nav.history")} />
        <NavItem to="/about"   label={t("nav.about")} />
      </div>
    </header>
  );
}