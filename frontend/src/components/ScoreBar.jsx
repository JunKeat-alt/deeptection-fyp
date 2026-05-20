import { useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import clsx from "clsx";

/**
 * Score bar with animated width and animated number countup.
 *
 * `score` is 0..1 (higher = riskier).
 * `variant` controls colour:
 *   - "risk"       (default): red / amber / green based on band
 *   - "confidence": flat accent blue
 *
 * Both the bar fill and the number animate in sync, ~0.9s,
 * with Apple-style ease-out (cubic-bezier 0.16, 1, 0.3, 1).
 */
export default function ScoreBar({
  score,
  label,
  sublabel,
  variant = "risk",
  delay = 0,
}) {
  // Animated value (0 to 100)
  const motionPct = useMotionValue(0);
  const displayPct = useTransform(motionPct, (v) => Math.round(v));

  useEffect(() => {
    if (score == null || Number.isNaN(score)) return;
    const target = Math.max(0, Math.min(1, score)) * 100;

    const controls = animate(motionPct, target, {
      duration: 0.9,
      delay,
      ease: [0.16, 1, 0.3, 1], // Apple "easeOutExpo"
    });
    return () => controls.stop();
  }, [score, delay, motionPct]);

  // Empty/unavailable state
  if (score == null || Number.isNaN(score)) {
    return (
      <div className="flex items-center justify-between rounded-xl bg-paper-sunken/60 px-4 py-3 text-sm text-ink-subtle">
        <span>{label}</span>
        <span className="italic">—</span>
      </div>
    );
  }

  const pct = Math.round(score * 100);
  const band =
    variant === "confidence"
      ? "accent"
      : score >= 0.6
      ? "fake"
      : score <= 0.4
      ? "real"
      : "uncertain";

  const barColor = {
    accent: "bg-accent",
    real: "bg-verdict-real",
    fake: "bg-verdict-fake",
    uncertain: "bg-verdict-uncertain",
  }[band];

  return (
    <div className="rounded-xl bg-paper-sunken/60 p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <div>
          <p className="text-sm font-medium text-ink">{label}</p>
          {sublabel && <p className="text-xs text-ink-subtle">{sublabel}</p>}
        </div>
        <p className="font-mono text-sm tabular-nums text-ink">
          <motion.span>{displayPct}</motion.span>%
        </p>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-paper-raised ring-1 ring-black/5">
        <motion.div
          className={clsx("h-full rounded-full", barColor)}
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(2, pct)}%` }}
          transition={{
            duration: 0.9,
            delay,
            ease: [0.16, 1, 0.3, 1],
          }}
        />
      </div>
    </div>
  );
}