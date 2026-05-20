import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";

const STEP_KEYS = ["loading.s1", "loading.s2", "loading.s3", "loading.s4"];

export default function LoadingScreen() {
  const { t } = useI18n();
  const [step, setStep] = useState(0);

  useEffect(() => {
    // Gentle, approximate step progression — total ~16s before looping.
    const schedule = [2800, 4000, 5000, 4000];
    let cancelled = false;
    let i = 0;

    function advance() {
      if (cancelled) return;
      i = Math.min(i + 1, STEP_KEYS.length - 1);
      setStep(i);
      if (i < STEP_KEYS.length - 1) {
        setTimeout(advance, schedule[i]);
      }
    }
    const id = setTimeout(advance, schedule[0]);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, []);

  return (
    <div className="container-app flex min-h-[60vh] items-center justify-center py-16">
      <div className="card w-full max-w-xl p-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-paper-sunken"
        >
          <Loader2 className="animate-spin text-accent" size={22} />
        </motion.div>

        <h2 className="font-display text-2xl">{t("loading.title")}</h2>
        <p className="mt-1 text-sm text-ink-muted">{t("loading.sub")}</p>

        <ul className="mt-8 flex flex-col gap-3 text-left">
          {STEP_KEYS.map((k, i) => {
            const done = i < step;
            const active = i === step;
            return (
              <li
                key={k}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 transition
                  ${done ? "bg-verdict-realBg text-verdict-real" :
                    active ? "bg-accent/5 text-ink ring-1 ring-accent/20" :
                    "bg-paper-sunken/60 text-ink-subtle"}`}
              >
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-paper-raised ring-1 ring-black/5">
                  {done ? (
                    <Check size={14} className="text-verdict-real" strokeWidth={3} />
                  ) : active ? (
                    <Loader2 size={12} className="animate-spin text-accent" />
                  ) : (
                    <span className="h-1.5 w-1.5 rounded-full bg-ink-subtle" />
                  )}
                </span>
                <span className="text-sm">{t(k)}</span>
              </li>
            );
          })}
        </ul>

        <div className="mt-8 h-1 w-full overflow-hidden rounded-full bg-paper-sunken">
          <div className="shimmer h-full w-full rounded-full" />
        </div>
      </div>
    </div>
  );
}
