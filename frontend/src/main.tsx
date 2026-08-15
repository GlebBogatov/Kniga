import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { Footer } from "./components/Footer";
import { LegalPage } from "./components/LegalPage";
import "./styles/palette.css";
import "./styles/app.css";

// Лёгкая hash-навигация (без роутер-зависимости): работает на GitHub Pages
// при любом base-path. Маршруты: #/ — приложение, #/legal/<slug> — документ.
function useHashPath() {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const onHash = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return hash.replace(/^#/, "") || "/";
}

function Root() {
  const path = useHashPath();
  const legalMatch = path.match(/^\/legal\/([\w-]+)/);
  return (
    <>
      {legalMatch ? <LegalPage slug={legalMatch[1]} /> : <App />}
      <Footer />
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
