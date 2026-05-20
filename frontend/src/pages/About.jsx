import { motion } from "framer-motion";
import { Cpu, ShieldCheck, HeartHandshake, Target } from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";

export default function About() {
  const { t } = useI18n();

  return (
    <section className="container-app pt-12 pb-20 sm:pt-20">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-12 max-w-2xl"
      >
        <p className="section-eyebrow mb-3">About</p>
        <h1 className="font-display text-4xl leading-tight sm:text-5xl">
          {t("about.title")}
        </h1>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.05 }}
          className="card p-8 sm:p-10"
        >
          <p className="text-lg leading-relaxed text-ink-soft">{t("about.p1")}</p>
          <p className="mt-6 text-lg leading-relaxed text-ink-soft">{t("about.p2")}</p>
          <p className="mt-6 text-lg leading-relaxed text-ink-soft">{t("about.p3")}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="flex flex-col gap-4"
        >
          <Aside Icon={Target} title="Scope" body="Detect multimedia-based phishing by analysing both face (CV) and voice (MFCC + CNN), then combining them via late fusion." />
          <Aside Icon={HeartHandshake} title="Target users" body="Parents, guardians, and elderly non-technical users who rely on voice and video messages." />
          <Aside Icon={Cpu} title="Tech" body={t("about.tech")} />
          <Aside Icon={ShieldCheck} title="SDG 16" body="Peace, Justice and Strong Institutions — trustworthy digital communication." />
        </motion.div>
      </div>
    </section>
  );
}

function Aside({ Icon, title, body }) {
  return (
    <div className="card flex items-start gap-4 p-5">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-paper-sunken ring-1 ring-black/5">
        <Icon size={16} strokeWidth={1.8} className="text-ink-muted" />
      </div>
      <div>
        <p className="font-medium">{title}</p>
        <p className="mt-1 text-sm text-ink-muted">{body}</p>
      </div>
    </div>
  );
}
