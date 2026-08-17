import { useState } from "react";

import { copy } from "../copy";

const KEY = "kn_cookie_ok";

export function CookieBanner() {
  const [accepted, setAccepted] = useState(() => {
    try {
      return localStorage.getItem(KEY) === "1";
    } catch {
      return true;
    }
  });

  if (accepted) return null;

  function accept() {
    try {
      localStorage.setItem(KEY, "1");
    } catch {
      /* нет localStorage */
    }
    setAccepted(true);
  }

  return (
    <div className="cookie-banner">
      <span>
        {copy.consent.cookieText}{" "}
        <a href="#/legal/privacy">{copy.consent.cookieMore}</a>
      </span>
      <button className="btn-secondary" onClick={accept}>
        {copy.consent.cookieAccept}
      </button>
    </div>
  );
}
