import clsx from "clsx";
import { CheckCircle2, AlertOctagon, HelpCircle } from "lucide-react";
import { useI18n } from "../context/I18nContext.jsx";

const CONFIG = {
  real: {
    bg: "bg-verdict-realBg",
    text: "text-verdict-real",
    ring: "ring-verdict-real/20",
    Icon: CheckCircle2,
    label: "result.verdict.real",
  },
  fake: {
    bg: "bg-verdict-fakeBg",
    text: "text-verdict-fake",
    ring: "ring-verdict-fake/25",
    Icon: AlertOctagon,
    label: "result.verdict.fake",
  },
  uncertain: {
    bg: "bg-verdict-uncertainBg",
    text: "text-verdict-uncertain",
    ring: "ring-verdict-uncertain/25",
    Icon: HelpCircle,
    label: "result.verdict.uncertain",
  },
};

export default function VerdictPill({ verdict, size = "md" }) {
  const { t } = useI18n();
  const cfg = CONFIG[verdict] || CONFIG.uncertain;
  const Icon = cfg.Icon;
  const pad =
    size === "lg" ? "px-5 py-2 text-sm" : "px-4 py-1.5 text-xs";
  const iconSize = size === "lg" ? 18 : 14;

  return (
    <span
      className={clsx(
        "verdict-pill ring-1",
        cfg.bg,
        cfg.text,
        cfg.ring,
        pad
      )}
    >
      <Icon size={iconSize} strokeWidth={2.4} />
      {t(cfg.label)}
    </span>
  );
}
