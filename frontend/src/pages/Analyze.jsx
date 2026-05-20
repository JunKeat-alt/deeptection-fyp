import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import UploadZone from "../components/UploadZone.jsx";
import MediaPreview from "../components/MediaPreview.jsx";
import LoadingScreen from "../components/LoadingScreen.jsx";
import { useAnalysis } from "../context/AnalysisContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import ModeSelector from "../components/ModeSelector.jsx";

export default function Analyze() {
  const { t } = useI18n();
  const { status, result, error } = useAnalysis();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === "done" && result) {
      navigate("/result", { replace: true });
    }
  }, [status, result, navigate]);

  if (status === "analyzing") return <LoadingScreen />;

  return (
    <section className="container-app pt-12 pb-20 sm:pt-20">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10 max-w-2xl"
      >
        <p className="section-eyebrow mb-3">Check</p>
        <h1 className="font-display text-4xl leading-tight sm:text-5xl">
          {t("upload.title")}
        </h1>
        <p className="mt-4 text-ink-muted">{t("upload.sub")}</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, delay: 0.05 }}
      >
        <p className="mb-8 text-xs text-ink-subtle">
          Using an ensemble of your trained model and the HuggingFace baseline to reduce false positives.
        </p>

        <ModeSelector />
        <UploadZone />
        <MediaPreview />
      </motion.div>

      {status === "error" && error && (
        <div className="mt-6 rounded-xl bg-verdict-fakeBg px-4 py-3 text-sm text-verdict-fake ring-1 ring-verdict-fake/20">
          {error}
        </div>
      )}
    </section>
  );
}