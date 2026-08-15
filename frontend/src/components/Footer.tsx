import { copy } from "../copy";
import { LEGAL_DOCS, SELLER } from "../content/legal";

export function Footer() {
  return (
    <footer className="site-footer">
      <nav className="footer-links">
        {LEGAL_DOCS.map((d) => (
          <a key={d.slug} href={`#/legal/${d.slug}`}>
            {d.title}
          </a>
        ))}
      </nav>
      <p className="footer-note muted">{copy.footer.disclaimer}</p>
      <p className="footer-seller muted">
        {SELLER.form} {SELLER.name} · ИНН {SELLER.inn}
      </p>
    </footer>
  );
}
