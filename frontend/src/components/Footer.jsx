export default function Footer() {
  return (
    <footer className="mt-24 border-t border-black/5 py-10 text-sm text-ink-muted">
      <div className="container-app flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="font-display text-base text-ink">Deeptection</p>
          <p className="mt-0.5 text-xs">
            Final Year Project · APU · Aligned with UN SDG 16
          </p>
        </div>
        <div className="text-xs text-ink-subtle">
          Files are analysed in-memory and not retained. © {new Date().getFullYear()} Koh Jun Keat.
        </div>
      </div>
    </footer>
  );
}
