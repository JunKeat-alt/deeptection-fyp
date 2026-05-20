import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { analyze as apiAnalyze } from "../api/client.js";
import { useI18n } from "./I18nContext.jsx";

const AnalysisContext = createContext(null);

export function AnalysisProvider({ children }) {
  const { lang } = useI18n();
  const [file, setFile] = useState(null);           // File | null
  const [mediaType, setMediaType] = useState(null); // "video" | "audio" | null
  const [status, setStatus] = useState("idle");     // idle | analyzing | done | error
  const [result, setResult] = useState(null);       // backend response
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("daily"); // NEW


  const reset = useCallback(() => {
    setFile(null);
    setMediaType(null);
    setStatus("idle");
    setResult(null);
    setError(null);
  }, []);

  const run = useCallback(async () => {
    if (!file) return;
    setStatus("analyzing");
    setError(null);
    try {
      const res = await apiAnalyze(file, lang, mode); // NEW
      if (!res?.ok) {
        setError(res?.message || "Something went wrong.");
        setStatus("error");
        return;
      }
      setResult(res);
      setStatus("done");
    } catch (e) {
      setError(e?.message || "Network error");
      setStatus("error");
    }
  }, [file, lang, mode]); // NEW

  const value = useMemo(
  () => ({ file, setFile, mediaType, setMediaType, status, result, error,
        run, reset, mode, setMode }), // NEW
    [file, mediaType, status, result, error, run, reset, mode]
  );
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}


export function useAnalysis() {
  const v = useContext(AnalysisContext);
  if (!v) throw new Error("useAnalysis must be used inside AnalysisProvider");
  return v;
}
