import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Copy, Hash } from "lucide-react";

/**
 * Display a copyable Analysis ID badge.
 *
 * Shows: [#] Analysis ID  A7F3-92KD  [copy icon]
 *
 * On click anywhere on the badge, the full ID is copied to the clipboard
 * and a brief checkmark animation confirms.
 */
export default function AnalysisIdBadge({ id }) {
  const [copied, setCopied] = useState(false);

  if (!id) return null;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard API can fail in non-HTTPS contexts; silently ignore
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="group inline-flex items-center gap-2 rounded-full
                 bg-paper-sunken/60 px-3 py-1.5
                 text-xs ring-1 ring-black/5 transition
                 hover:bg-paper-sunken hover:ring-black/10
                 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      aria-label={`Copy Analysis ID ${id}`}
      title="Click to copy"
    >
      <Hash size={12} className="text-ink-subtle" />
      <span className="text-ink-subtle">Analysis ID</span>
      <span className="font-mono tabular-nums text-ink">{id}</span>

      {/* Icon swap: Copy ↔ Check */}
      <span className="relative inline-flex h-3.5 w-3.5 items-center justify-center">
        <AnimatePresence mode="wait" initial={false}>
          {copied ? (
            <motion.span
              key="check"
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.6 }}
              transition={{ duration: 0.15 }}
              className="absolute"
            >
              <Check size={14} strokeWidth={2.6} className="text-verdict-real" />
            </motion.span>
          ) : (
            <motion.span
              key="copy"
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.6 }}
              transition={{ duration: 0.15 }}
              className="absolute"
            >
              <Copy
                size={12}
                className="text-ink-subtle transition group-hover:text-ink"
              />
            </motion.span>
          )}
        </AnimatePresence>
      </span>
    </button>
  );
}