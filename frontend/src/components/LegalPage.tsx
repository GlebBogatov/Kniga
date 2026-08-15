import { useEffect } from "react";

import { copy } from "../copy";
import { LEGAL_BY_SLUG, LEGAL_DRAFT_NOTICE } from "../content/legal";

export function LegalPage({ slug }: { slug: string }) {
  const doc = LEGAL_BY_SLUG[slug];

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [slug]);

  return (
    <main className="app legal">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      {!doc ? (
        <p className="muted">{copy.footer.notFound}</p>
      ) : (
        <article>
          <h1 className="legal-title">{doc.title}</h1>
          <p className="legal-updated muted">
            {copy.footer.updated}: {doc.updated}
          </p>
          <div className="legal-draft">{LEGAL_DRAFT_NOTICE}</div>
          {doc.intro && <p className="legal-intro">{doc.intro}</p>}
          {doc.sections.map((s) => (
            <section key={s.heading} className="legal-section">
              <h2>{s.heading}</h2>
              {s.body.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </section>
          ))}
        </article>
      )}
    </main>
  );
}
