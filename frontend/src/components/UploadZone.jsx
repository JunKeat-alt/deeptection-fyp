import { useCallback, useRef, useState } from "react";
import clsx from "clsx";
import { UploadCloud } from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";
import { useAnalysis } from "../context/AnalysisContext.jsx";

const VIDEO_EXTS = ["mp4", "mov", "avi", "mkv", "webm"];
const AUDIO_EXTS = ["wav", "mp3", "m4a", "flac", "ogg"];
const MAX_VIDEO_MB = 50;
const MAX_AUDIO_MB = 20;

function getExt(name = "") {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

export default function UploadZone() {
  const { t } = useI18n();
  const { setFile, setMediaType } = useAnalysis();
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState(null);
  const inputRef = useRef(null);

  const accept =
    [...VIDEO_EXTS, ...AUDIO_EXTS].map((e) => "." + e).join(",") +
    ",video/*,audio/*";

  const handle = useCallback(
    (files) => {
      setLocalError(null);
      if (!files || !files.length) return;
      const f = files[0];
      const ext = getExt(f.name);
      const isVideo = VIDEO_EXTS.includes(ext);
      const isAudio = AUDIO_EXTS.includes(ext);
      if (!isVideo && !isAudio) {
        setLocalError(t("upload.invalid_format"));
        return;
      }
      const limitMb = isVideo ? MAX_VIDEO_MB : MAX_AUDIO_MB;
      if (f.size > limitMb * 1024 * 1024) {
        setLocalError(t("upload.too_large"));
        return;
      }
      setFile(f);
      setMediaType(isVideo ? "video" : "audio");
    },
    [setFile, setMediaType, t]
  );

  const onDrop = useCallback(
    (ev) => {
      ev.preventDefault();
      setDragging(false);
      handle(ev.dataTransfer?.files);
    },
    [handle]
  );

  return (
    <div className="relative mx-auto w-full max-w-2xl overflow-hidden">
      <label
        htmlFor="deeptection-upload"
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={clsx(
          "dropzone block w-full cursor-pointer",
          dragging && "dropzone--active"
        )}
      >
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div
            className={clsx(
              "mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-paper-sunken",
              "ring-1 ring-black/5 transition",
              dragging && "bg-white ring-accent"
            )}
          >
            <UploadCloud
              size={26}
              strokeWidth={1.7}
              className={clsx(
                "transition",
                dragging ? "text-accent" : "text-ink-muted"
              )}
            />
          </div>
          <p className="font-display text-xl">{t("upload.drop")}</p>
          <p className="mt-1 text-sm text-ink-muted">
            {t("upload.or")}{" "}
            <span className="font-medium text-ink underline-offset-4 hover:underline">
              {t("upload.browse")}
            </span>
          </p>
          <p className="mt-4 max-w-xs text-xs text-ink-subtle">
            {t("upload.supported", {
              vmb: MAX_VIDEO_MB,
              vsec: 180,
              amb: MAX_AUDIO_MB,
            })}
          </p>
        </div>
        <input
          id="deeptection-upload"
          ref={inputRef}
          type="file"
          accept={accept}
          className="sr-only"
          onChange={(e) => handle(e.target.files)}
        />
      </label>

      {localError && (
        <p className="mt-3 text-center text-sm text-verdict-fake">{localError}</p>
      )}
    </div>
  );
}
