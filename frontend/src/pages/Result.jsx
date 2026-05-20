import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ResultCard from "../components/ResultCard.jsx";
import { useAnalysis } from "../context/AnalysisContext.jsx";

/**
 * Result page.
 *
 * Rendering is delegated to ResultCard, which consumes the new
 * language-neutral backend payload (explanation.simple_key and
 * details[].reason_keys) and translates every label via useI18n().
 * This page is only responsible for routing: if no analysis result
 * is in context, bounce the user back to /analyze.
 */
export default function Result() {
  const navigate = useNavigate();
  const { result, reset } = useAnalysis();

  useEffect(() => {
    if (!result) navigate("/analyze", { replace: true });
  }, [result, navigate]);

  if (!result) return null;

  return (
    <section className="container-app pt-10 pb-20 sm:pt-16">
      <div className="mx-auto max-w-3xl">
        <ResultCard
          data={result}
          onRetry={() => {
            reset();
            navigate("/analyze");
          }}
        />
      </div>
    </section>
  );
}