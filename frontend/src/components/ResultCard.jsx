import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  ChevronDown,
  FileCheck2,
  Info,
  RotateCcw,
  Sparkles,
  Video,
  Volume2,
} from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";
import VerdictPill from "./VerdictPill.jsx";
import ScoreBar from "./ScoreBar.jsx";
import AnalysisIdBadge from "./AnalysisIdBadge.jsx";

function riskLabel(score, t) {
  if (score == null) return "—";
  if (score >= 0.6) return t("result.risk_high");
  if (score <= 0.4) return t("result.risk_low");
  return t("result.risk_med");
}

function ModalityBadge({ labelKey, Icon, available, score }) {
  const { t } = useI18n();
  const faded = !available;
  return (
    <div
      className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs ring-1 ring-black/5
        ${faded ? "bg-paper-sunken text-ink-subtle" : "bg-paper-raised text-ink"}`}
    >
      <Icon size={13} strokeWidth={2} />
      <span>{t(labelKey)}</span>
      {available && score != null && (
        <span className="font-mono tabular-nums text-ink-muted">
          {(score * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

/**
 * Language-neutral result renderer.
 *
 * Expects the backend payload from /api/analyze, which now includes:
 *   explanation.simple_key                   — i18n key for the one-liner
 *   explanation.details[i].modality          — "video" | "audio" | "system"
 *   explanation.details[i].reason_keys[]     — i18n keys for each reason
 *
 * All user-facing text is resolved through t() so switching the
 * I18nContext locale re-renders the whole card in the target language
 * (including RTL layout for Arabic, which is handled globally on <html>).
 */
export default function ResultCard({ data, onRetry }) {
  const { t } = useI18n();
  const [expanded, setExpanded] = useState(false);

  if (!data) return null;

  const verdict = data.verdict || "uncertain";
  const final = data.final_score ?? 0.5;
  const confidence = data.confidence ?? 0;
  const video = data.video || {};
  const audio = data.audio || {};
  const fusion = data.fusion || {};
  const explanation = data.explanation || {};

  const simpleKey = explanation.simple_key || `result.simple.${verdict}`;

  const accentBg =
    verdict === "fake"
      ? "from-verdict-fakeBg"
      : verdict === "real"
      ? "from-verdict-realBg"
      : "from-verdict-uncertainBg";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="card overflow-hidden"
    >
      {/* ---- Top: verdict banner ---- */}
      <div className={`bg-gradient-to-b ${accentBg} to-transparent px-7 pt-8 pb-6`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-ink-subtle">
            <FileCheck2 size={14} />
            <span className="section-eyebrow normal-case tracking-normal">
              {data.filename || data.media_type}
            </span>
          </div>
          <AnalysisIdBadge id={data.id} />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <VerdictPill verdict={verdict} size="lg" />
          {fusion.fallback_note && (
            <span className="inline-flex items-center gap-1.5 text-xs text-ink-muted">
              <Info size={12} />
              {fusion.fallback_note}
            </span>
          )}
        </div>

        <h2 className="mt-5 font-display text-3xl leading-tight">
          {t(simpleKey)}
        </h2>
      </div>

      {/* ---- Scores ---- */}
      <div
        key={data.id || data.filename}
        className="grid gap-3 border-t border-black/5 p-6 sm:grid-cols-2"
      >
        <ScoreBar
          label={t("result.final")}
          sublabel={riskLabel(final, t)}
          score={final}
          variant="risk"
          delay={0.1}
        />
        <ScoreBar
          label={t("result.confidence")}
          score={confidence}
          variant="confidence"
          delay={0.2}
        />
        <ScoreBar
          label={t("result.video_score")}
          sublabel={video.available ? video.model : t("result.unavailable")}
          score={video.available ? video.score : null}
          variant="risk"
          delay={0.3}
        />
        <ScoreBar
          label={t("result.audio_score")}
          sublabel={audio.available ? audio.model : t("result.unavailable")}
          score={audio.available ? audio.score : null}
          variant="risk"
          delay={0.4}
        />
      </div>

      {/* ---- Modalities used ---- */}
      <div className="flex flex-wrap items-center gap-2 border-t border-black/5 px-6 py-4">
        <span className="section-eyebrow mr-1">{t("result.used")}</span>
        <ModalityBadge
          labelKey="result.modality.video"
          Icon={Video}
          available={!!video.available}
          score={video.score}
        />
        <ModalityBadge
          labelKey="result.modality.audio"
          Icon={Volume2}
          available={!!audio.available}
          score={audio.score}
        />
      </div>

      {/* ---- Explanation ---- */}
      <div className="border-t border-black/5 p-6">
        <button
          onClick={() => setExpanded((e) => !e)}
          className="flex w-full items-center justify-between rounded-xl bg-paper-sunken/60 px-4 py-3 text-left transition hover:bg-paper-sunken"
          aria-expanded={expanded}
        >
          <span className="flex items-center gap-2 text-sm font-medium">
            <Sparkles size={14} className="text-accent" />
            {t("result.why")}
          </span>
          <ChevronDown
            size={16}
            className={`text-ink-muted transition ${expanded ? "rotate-180" : ""}`}
          />
        </button>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              key="details"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 1.6 }}
              className="overflow-hidden"
            >
              <div className="mt-4 flex flex-col gap-4">
                {(explanation.details || []).map((block, i) => {
                  const modalityLabelKey = `result.modality.${block.modality}`;
                  const reasonKeys =
                    block.reason_keys || block.reasons || []; // legacy safety
                  return (
                    <div
                      key={i}
                      className="rounded-xl border border-black/5 bg-paper-raised p-4"
                    >
                      <p className="section-eyebrow mb-2 capitalize tracking-wide">
                        {t(modalityLabelKey)}
                      </p>
                      <ul className="flex flex-col gap-2">
                        {reasonKeys.map((rk, j) => (
                          <li
                            key={j}
                            className="flex items-start gap-2 text-sm text-ink-soft"
                          >
                            <Check
                              size={14}
                              strokeWidth={2.4}
                              className="mt-1 text-accent"
                            />
                            <span>{t(rk)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ---- Footer ---- */}
      <div className="flex items-center justify-between border-t border-black/5 bg-paper-sunken/40 px-6 py-4">
        <span className="inline-flex items-center gap-1.5 text-xs text-ink-subtle">
          <Check size={12} className="text-verdict-real" />
          {t("result.save")}
        </span>
        <button onClick={onRetry} className="btn-primary">
          <RotateCcw size={14} />
          {t("result.retry")}
        </button>
      </div>
    </motion.div>
  );
}