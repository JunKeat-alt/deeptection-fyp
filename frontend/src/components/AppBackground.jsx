import { useAnalysis } from "../context/AnalysisContext.jsx";

/**
 * Decorative background layer. Sits behind all content.
 *
 * - Always pointer-events: none so it never intercepts clicks.
 * - Always behind content via z-index: -1 on a fixed layer.
 * - Slightly tints/blurs more during analyzing or error states,
 *   for visual feedback, without ever overlapping foreground UI.
 */
export default function AppBackground() {
  const { status, error } = useAnalysis();

  const tintClass =
    status === "analyzing"
      ? "bg-paper/70 backdrop-blur-md"     // soft veil during processing
      : error
      ? "bg-red-50/40 backdrop-blur-sm"    // gentle warning tint on errors
      : "bg-paper/40 backdrop-blur-sm";    // default ambient blur

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none fixed inset-0 -z-10 transition-colors duration-500 ${tintClass}`}
    >
      {/* Optional: dotted texture or gradient — purely decorative. */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(0,0,0,0.06) 1px, transparent 0)",
          backgroundSize: "24px 24px",
        }}
      />
    </div>
  );
}