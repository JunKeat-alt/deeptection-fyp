import { FileVideo2, FileAudio2, Clock } from "lucide-react";
import VerdictPill from "./VerdictPill.jsx";

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function HistoryItem({ entry }) {
  const Icon = entry.media_type === "video" ? FileVideo2 : FileAudio2;

  const final = entry.final_score;
  const confidence = entry.confidence;

  return (
    <li className="card flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-paper-sunken ring-1 ring-black/5">
          <Icon size={18} strokeWidth={1.7} className="text-ink-muted" />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium">{entry.filename}</p>
          <p className="mt-0.5 flex items-center gap-2 text-xs text-ink-subtle">
            {entry.id && (
              <span className="font-mono tabular-nums text-ink-muted">
                #{entry.id}
              </span>
            )}
            <span>·</span>
            <Clock size={11} />
            {formatDate(entry.timestamp)}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <VerdictPill verdict={entry.verdict} />
        <div className="hidden items-center gap-3 text-xs text-ink-muted sm:flex">
          <span>
            risk{" "}
            <span className="font-mono tabular-nums text-ink">
              {final != null ? `${(final * 100).toFixed(0)}%` : "—"}
            </span>
          </span>
          <span>·</span>
          <span>
            conf{" "}
            <span className="font-mono tabular-nums text-ink">
              {confidence != null ? `${(confidence * 100).toFixed(0)}%` : "—"}
            </span>
          </span>
        </div>
      </div>
    </li>
  );
}
