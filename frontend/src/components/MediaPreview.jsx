import { useEffect, useMemo, useState } from "react";
import { FileVideo2, FileAudio2, X } from "lucide-react";
import { useAnalysis } from "../context/AnalysisContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export default function MediaPreview() {
  const { t } = useI18n();
  const { file, mediaType, reset, run, status } = useAnalysis();
  const [objectUrl, setObjectUrl] = useState(null);

  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setObjectUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const info = useMemo(() => {
    if (!file) return null;
    return { name: file.name, size: formatBytes(file.size), type: file.type || mediaType };
  }, [file, mediaType]);

  if (!file) return null;

  const Icon = mediaType === "video" ? FileVideo2 : FileAudio2;
  const busy = status === "analyzing";

  return (
    <div className="card mt-6 overflow-hidden">
      <div className="flex items-start gap-4 border-b border-black/5 p-5">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-paper-sunken ring-1 ring-black/5">
          <Icon size={20} className="text-ink-muted" strokeWidth={1.7} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{info.name}</p>
          <p className="mt-0.5 text-xs text-ink-subtle">
            {info.size} · {info.type}
          </p>
        </div>
        <button
          onClick={reset}
          disabled={busy}
          className="btn-ghost !py-1.5 !px-2"
          aria-label="Remove file"
          title={t("upload.remove")}
        >
          <X size={16} />
        </button>
      </div>

      <div className="bg-paper-sunken p-5">
        {mediaType === "video" ? (
          <video
            src={objectUrl}
            controls
            playsInline
            className="w-full rounded-xl bg-black"
            style={{ maxHeight: 360 }}
          />
        ) : (
          <audio src={objectUrl} controls className="w-full" />
        )}
      </div>

      <div className="flex items-center justify-end gap-2 p-4">
        <button onClick={reset} disabled={busy} className="btn-ghost">
          {t("upload.remove")}
        </button>
        <button onClick={run} disabled={busy} className="btn-primary">
          {busy ? t("upload.wait") : t("upload.analyze")}
        </button>
      </div>
    </div>
  );
}
