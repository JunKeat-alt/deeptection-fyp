import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ShieldCheck,
  Ear,
  Eye,
  Info,
  Sparkles,
} from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";

const fadeUp = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: "easeOut" },
};

export default function Home() {
  const { t } = useI18n();

  return (
    <div>
      {/* ---------------- Hero ---------------- */}
      <section className="container-app relative pt-16 sm:pt-24">
        <motion.p
          {...fadeUp}
          className="section-eyebrow mb-5 inline-flex items-center gap-2"
        >
          <Sparkles size={12} className="text-accent" />
          Deeptection
        </motion.p>

        <motion.h1
          {...fadeUp}
          transition={{ duration: 0.55, ease: "easeOut", delay: 0.05 }}
          className="display max-w-3xl text-5xl font-medium leading-[1.05] sm:text-6xl md:text-7xl"
        >
          {t("home.title")}{" "}
          <span className="italic text-ink-muted">
            {t("home.tagline")}
          </span>
        </motion.h1>

        <motion.p
          {...fadeUp}
          transition={{ duration: 0.55, ease: "easeOut", delay: 0.12 }}
          className="mt-6 max-w-xl text-lg text-ink-muted"
        >
          {t("home.sub")}
        </motion.p>

        <motion.div
          {...fadeUp}
          transition={{ duration: 0.55, ease: "easeOut", delay: 0.18 }}
          className="mt-9 flex flex-wrap items-center gap-3"
        >
          <Link to="/analyze" className="btn-primary">
            {t("home.cta")}
            <ArrowRight size={16} />
          </Link>
          <Link to="/about" className="btn-pill">
            {t("home.cta2")}
          </Link>
        </motion.div>

        {/* Visual: verdict preview card */}
        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.25 }}
          className="mt-14"
        >
          <HeroShowcase />
        </motion.div>
      </section>

      {/* ---------------- Features ---------------- */}
      <section className="container-app mt-28 sm:mt-36">
        <div className="mb-10 max-w-2xl">
          <p className="section-eyebrow mb-3">How it works</p>
          <h2 className="font-display text-4xl leading-tight sm:text-5xl">
            {t("home.features.title")}
          </h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <FeatureCard
            Icon={ShieldCheck}
            title={t("home.f1.title")}
            body={t("home.f1.body")}
          />
          <FeatureCard
            Icon={Eye}
            title={t("home.f2.title")}
            body={t("home.f2.body")}
          />
          <FeatureCard
            Icon={Ear}
            title={t("home.f3.title")}
            body={t("home.f3.body")}
          />
        </div>
      </section>

      {/* ---------------- Educational ---------------- */}
      <section className="container-app mt-28 sm:mt-36">
        <div className="card flex flex-col gap-6 p-8 sm:flex-row sm:items-center sm:p-10">
          <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-verdict-uncertainBg text-verdict-uncertain ring-1 ring-black/5">
            <Info size={22} />
          </div>
          <div className="flex-1">
            <h3 className="font-display text-2xl">{t("home.edu.title")}</h3>
            <p className="mt-2 text-ink-muted">{t("home.edu.body")}</p>
          </div>
          <Link to="/analyze" className="btn-primary self-start sm:self-auto">
            {t("home.cta")}
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}

/* --------------------- bits --------------------- */
function FeatureCard({ Icon, title, body }) {
  return (
    <div className="card flex flex-col gap-4 p-6">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-paper-sunken ring-1 ring-black/5">
        <Icon size={18} strokeWidth={1.7} className="text-ink-muted" />
      </div>
      <h3 className="font-display text-xl">{title}</h3>
      <p className="text-sm leading-relaxed text-ink-muted">{body}</p>
    </div>
  );
}

function HeroShowcase() {
  // A decorative preview of a fake verdict card to give visual substance above the fold
  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -inset-16 -z-10 rounded-[40px] bg-hero-glow"
      />
      <div className="mx-auto grid max-w-4xl gap-6 rounded-[32px] bg-paper-raised p-7 shadow-card ring-1 ring-black/5 sm:grid-cols-[1.1fr_1fr]">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 text-xs text-ink-subtle">
            <span className="h-2 w-2 rounded-full bg-verdict-fake"></span>
            voice-note-from-mum.mp3
          </div>
          <div>
            <span className="verdict-pill ring-1 bg-verdict-fakeBg text-verdict-fake ring-verdict-fake/20 px-4 py-1.5 text-xs">
              Likely a deepfake
            </span>
            <p className="mt-3 font-display text-2xl leading-tight">
              This voice shows strong signs of being AI-generated.
            </p>
          </div>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <MiniStat label="Risk" value="82%" tone="fake" />
            <MiniStat label="Confidence" value="76%" tone="accent" />
          </div>
        </div>
        <div className="relative hidden overflow-hidden rounded-2xl bg-paper-sunken sm:block">
          <div className="grid place-items-center">
            <WaveformArt />
          </div>
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[10px] uppercase tracking-widest text-ink-subtle">
            <span>voice · 16kHz</span>
            <span>MFCC</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value, tone }) {
  const toneCls =
    tone === "fake"
      ? "text-verdict-fake"
      : tone === "real"
      ? "text-verdict-real"
      : "text-accent";
  return (
    <div className="rounded-xl bg-paper-sunken/70 px-4 py-3 ring-1 ring-black/5">
      <p className="text-[11px] uppercase tracking-wider text-ink-subtle">
        {label}
      </p>
      <p className={`mt-1 font-mono text-lg tabular-nums ${toneCls}`}>{value}</p>
    </div>
  );
}

function WaveformArt() {
  // A decorative SVG waveform using CSS vars that look like audio analysis.
  const bars = new Array(56).fill(0).map((_, i) => {
    const seed = Math.sin(i * 0.7) * 0.5 + Math.cos(i * 0.21) * 0.4;
    return Math.max(0.15, Math.abs(seed) * 0.9 + (i % 7 === 0 ? 0.2 : 0));
  });
  return (
    <svg viewBox="0 0 300 140" className="h-full w-full px-6" aria-hidden="true">
      {bars.map((h, i) => {
        const x = (300 / bars.length) * i + 3;
        const barH = 120 * h;
        const y = 70 - barH / 2;
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={2}
            height={barH}
            rx={1}
            fill="#0B0F14"
            opacity={0.15 + h * 0.5}
          />
        );
      })}
      <line x1="0" x2="300" y1="70" y2="70" stroke="#0B0F14" strokeOpacity="0.08" />
    </svg>
  );
}
