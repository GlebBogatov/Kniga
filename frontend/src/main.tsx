import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { AuthProvider } from "./auth";
import { AuthBar } from "./components/AuthBar";
import { AdminPage } from "./components/AdminPage";
import { CabinetPage } from "./components/CabinetPage";
import { CmsPage } from "./components/CmsPage";
import { CookieBanner } from "./components/CookieBanner";
import { Footer } from "./components/Footer";
import { LegalPage } from "./components/LegalPage";
import { TariffsPage } from "./components/TariffsPage";
import "./styles/palette.css";
import "./styles/app.css";

// Лёгкая hash-навигация (без роутер-зависимости): работает на GitHub Pages
// при любом base-path. Маршруты: #/ — приложение, #/legal/<slug> — документ,
// #/cabinet — личный кабинет.
function useHashPath() {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const onHash = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return hash.replace(/^#/, "") || "/";
}

function CurrentPage({ path }: { path: string }) {
  const legalMatch = path.match(/^\/legal\/([\w-]+)/);
  if (legalMatch) return <LegalPage slug={legalMatch[1]} />;
  if (path.startsWith("/cabinet")) return <CabinetPage />;
  if (path.startsWith("/tariffs")) return <TariffsPage />;
  if (path.startsWith("/admin")) return <AdminPage />;
  if (path.startsWith("/cms")) return <CmsPage />;
  return <App />;
}

function Root() {
  const path = useHashPath();
  return (
    <AuthProvider>
      <div className="top-strip">
        <AuthBar />
      </div>
      <CurrentPage path={path} />
      <Footer />
      <CookieBanner />
    </AuthProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
