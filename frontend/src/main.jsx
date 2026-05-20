import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AnalysisProvider } from "./context/AnalysisContext.jsx";
import { I18nProvider } from "./context/I18nContext.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <AnalysisProvider>
          <App />
        </AnalysisProvider>
      </I18nProvider>
    </BrowserRouter>
  </React.StrictMode>
);
