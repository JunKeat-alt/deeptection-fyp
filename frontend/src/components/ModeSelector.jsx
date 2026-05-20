import clsx from "clsx";
import { MessageSquare, Film } from "lucide-react";
import { useAnalysis } from "../context/AnalysisContext.jsx";

export default function ModeSelector() {
  const { mode, setMode } = useAnalysis();

  return (
    <div className="mb-8">
      <div className="mb-3 flex items-center gap-2">
        <p className="section-eyebrow normal-case tracking-normal">
          Analysis Mode
        </p>
      </div>

      <div className="inline-flex max-w-full items-center gap-1 rounded-full bg-paper-raised p-1 shadow-ring ring-1 ring-black/5">
        <button
          type="button"
          onClick={() => setMode("daily")}
          className={clsx(
            "flex items-center gap-2 rounded-full px-4 py-2 text-sm transition",
            mode === "daily"
              ? "bg-ink text-paper-raised shadow-soft"
              : "text-ink-muted hover:text-ink"
          )}
        >
          <MessageSquare size={14} />
          Daily Message
          <span className="ml-1 text-[10px] uppercase tracking-wider opacity-70">
            Recommended
          </span>
        </button>

        <button
          type="button"
          onClick={() => setMode("clear_media")}
          className={clsx(
            "flex items-center gap-2 rounded-full px-4 py-2 text-sm transition",
            mode === "clear_media"
              ? "bg-ink text-paper-raised shadow-soft"
              : "text-ink-muted hover:text-ink"
          )}
        >
          <Film size={14} />
          Clear Media
        </button>
      </div>

      <p className="mt-3 max-w-xl text-xs text-ink-subtle">
        {mode === "daily"
          ? "Recommended for WhatsApp voice notes, phone recordings, and real-world videos."
          : "Suitable for movies, studio-quality audio, and clean speech."}
      </p>
    </div>
  );
}