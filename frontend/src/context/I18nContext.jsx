import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { LOCALES, LOCALE_META, translate } from "../i18n.js";

const STORAGE_KEY = "deeptection.lang";

const I18nContext = createContext(null);

/**
 * Provides locale + translation state to the whole app.
 *
 *  lang          current locale code ("en" | "ta" | "ar")
 *  setLang(code) switch locale
 *  t(key, vars?) translate a key in the current locale
 *  locales       list of supported codes
 *  meta          map of { code: { label, nativeLabel, dir } }
 *  dir           current text direction, "ltr" | "rtl"
 *
 * Side effects on mount + every language change:
 *   document.documentElement.lang = <code>
 *   document.documentElement.dir  = "ltr" | "rtl"
 *   localStorage persists the user's choice
 */
export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && LOCALES.includes(saved)) return saved;
    } catch {
      /* localStorage unavailable — ignore */
    }
    return "en";
  });

  // Apply document-level attributes whenever the language changes
  useEffect(() => {
    const meta = LOCALE_META[lang] || LOCALE_META.en;
    try {
      document.documentElement.lang = lang;
      document.documentElement.dir = meta.dir;
    } catch {
      /* non-browser env — ignore */
    }
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* private mode — ignore */
    }
  }, [lang]);

  const setLang = useCallback((code) => {
    if (!LOCALES.includes(code)) return;
    setLangState(code);
  }, []);

  const t = useCallback(
    (key, vars) => translate(lang, key, vars),
    [lang]
  );

  const value = useMemo(() => {
    const meta = LOCALE_META[lang] || LOCALE_META.en;
    return {
      lang,
      setLang,
      t,
      locales: LOCALES,
      meta: LOCALE_META,
      dir: meta.dir,
    };
  }, [lang, setLang, t]);

  return (
    <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  const v = useContext(I18nContext);
  if (!v) throw new Error("useI18n must be used inside I18nProvider");
  return v;
}