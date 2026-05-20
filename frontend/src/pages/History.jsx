import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Trash2, RefreshCw } from "lucide-react";
import HistoryItem from "../components/HistoryItem.jsx";
import { clearHistory, fetchHistory } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";

export default function History() {
  const { t } = useI18n();
  const [entries, setEntries] = useState(null);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const data = await fetchHistory(100);
      setEntries(data?.entries || []);
    } catch (e) {
      setErr(t("err.network"));
    }
  }, [t]);

  useEffect(() => {
    load();
  }, [load]);

  const onClear = useCallback(async () => {
    if (!confirm(t("history.confirm_clear"))) return;
    try {
      await clearHistory();
      setEntries([]);
    } catch (e) {
      setErr(t("err.generic"));
    }
  }, [t]);

  return (
    <section className="container-app pt-12 pb-20 sm:pt-20">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10 flex items-end justify-between"
      >
        <div>
          <p className="section-eyebrow mb-3">History</p>
          <h1 className="font-display text-4xl leading-tight sm:text-5xl">
            {t("history.title")}
          </h1>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="btn-pill text-xs !px-3 !py-2">
            <RefreshCw size={13} />
          </button>
          {entries && entries.length > 0 && (
            <button
              onClick={onClear}
              className="btn-pill text-xs !px-3 !py-2 text-verdict-fake"
            >
              <Trash2 size={13} />
              <span className="hidden sm:inline">{t("history.clear")}</span>
            </button>
          )}
        </div>
      </motion.div>

      {err && (
        <div className="mb-6 rounded-xl bg-verdict-fakeBg px-4 py-3 text-sm text-verdict-fake ring-1 ring-verdict-fake/20">
          {err}
        </div>
      )}

      {entries == null ? (
        <HistorySkeleton />
      ) : entries.length === 0 ? (
        <div className="card p-10 text-center text-ink-muted">
          {t("history.empty")}
        </div>
      ) : (
        <motion.ul
          initial="hidden"
          animate="show"
          variants={{
            hidden: {},
            show: { transition: { staggerChildren: 0.04 } },
          }}
          className="flex flex-col gap-3"
        >
          {entries.map((e) => (
            <motion.div
              key={e.id}
              variants={{
                hidden: { opacity: 0, y: 10 },
                show: { opacity: 1, y: 0 },
              }}
              transition={{ duration: 0.35 }}
            >
              <HistoryItem entry={e} />
            </motion.div>
          ))}
        </motion.ul>
      )}
    </section>
  );
}

function HistorySkeleton() {
  return (
    <ul className="flex flex-col gap-3">
      {[0, 1, 2].map((i) => (
        <li key={i} className="card p-5">
          <div className="shimmer h-6 w-1/3 rounded" />
          <div className="shimmer mt-2 h-4 w-1/5 rounded" />
        </li>
      ))}
    </ul>
  );
}
