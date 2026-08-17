import { useEffect, useState } from "react";

import { DEMO, api } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { CmsPreview, ContentItem, ContentVersion } from "../types";
import { CmsPresets } from "./CmsPresets";

export function CmsPage() {
  const { user, loading } = useAuth();
  const isEditor =
    user?.role === "editor" || user?.role === "admin" || (DEMO && !!user);

  const [items, setItems] = useState<ContentItem[] | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<string | null>(null);
  const [versionsFor, setVersionsFor] = useState<string | null>(null);
  const [versions, setVersions] = useState<ContentVersion[]>([]);
  const [question, setQuestion] = useState("Стоит ли мне менять работу этой весной?");
  const [preview, setPreview] = useState<CmsPreview | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);

  async function reload() {
    const list = await api.cmsList();
    setItems(list);
    setEdits(Object.fromEntries(list.map((i) => [i.key, i.draft ?? i.effective])));
  }

  useEffect(() => {
    if (isEditor) void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditor]);

  async function save(key: string) {
    await api.cmsSave(key, edits[key] ?? "");
    setSaved(key);
    window.setTimeout(() => setSaved(null), 1500);
    await reload();
  }
  async function publish(key: string) {
    await api.cmsSave(key, edits[key] ?? "");
    await api.cmsPublish(key);
    await reload();
  }
  async function revert(key: string) {
    await api.cmsRevert(key);
    await reload();
  }
  async function showVersions(key: string) {
    if (versionsFor === key) {
      setVersionsFor(null);
      return;
    }
    setVersions(await api.cmsVersions(key));
    setVersionsFor(key);
  }
  async function restore(key: string, id: number) {
    await api.cmsRestore(key, id);
    setVersionsFor(null);
    await reload();
  }
  async function runPreview() {
    setPreview(await api.cmsPreview(question));
  }

  if (loading) {
    return (
      <main className="app">
        <p className="muted">{copy.journal.loading}</p>
      </main>
    );
  }
  if (!isEditor) {
    return (
      <main className="app">
        <a className="legal-back" href="#/">
          ← {copy.footer.back}
        </a>
        <p className="muted">{copy.cms.noAccess}</p>
      </main>
    );
  }

  const groups = [...new Set((items ?? []).map((i) => i.group))];

  return (
    <main className="app cms">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.cms.title}</h1>
      <p className="muted cms-intro">{copy.cms.intro}</p>

      {groups.map((group) => (
        <section key={group} className="cms-group">
          <h2>{group}</h2>
          {(items ?? [])
            .filter((i) => i.group === group)
            .map((i) => (
              <div key={i.key} className="cms-item">
                <label className="cms-label">
                  {i.label}
                  {i.dirty && <span className="cms-dirty"> · {copy.cms.dirty}</span>}
                  {saved === i.key && <span className="muted"> · {copy.cms.savedFlag}</span>}
                </label>
                {i.multiline ? (
                  <textarea
                    rows={3}
                    value={edits[i.key] ?? ""}
                    onChange={(e) =>
                      setEdits((p) => ({ ...p, [i.key]: e.target.value }))
                    }
                  />
                ) : (
                  <input
                    value={edits[i.key] ?? ""}
                    onChange={(e) =>
                      setEdits((p) => ({ ...p, [i.key]: e.target.value }))
                    }
                  />
                )}
                <div className="cms-actions">
                  <button className="btn-secondary" onClick={() => void save(i.key)}>
                    {copy.cms.save}
                  </button>
                  <button className="btn-secondary" onClick={() => void publish(i.key)}>
                    {copy.cms.publish}
                  </button>
                  <button className="btn-secondary" onClick={() => void revert(i.key)}>
                    {copy.cms.revert}
                  </button>
                  <button className="btn-secondary" onClick={() => void showVersions(i.key)}>
                    {copy.cms.versions}
                  </button>
                </div>
                {versionsFor === i.key && (
                  <ul className="cms-versions">
                    {versions.length === 0 ? (
                      <li className="muted">{copy.cms.noVersions}</li>
                    ) : (
                      versions.map((v) => (
                        <li key={v.id}>
                          <span className="muted">
                            {v.created_at
                              ? new Date(v.created_at).toLocaleString("ru-RU")
                              : ""}
                          </span>
                          <span className="cms-vval">{v.value.slice(0, 80)}</span>
                          <button
                            className="btn-secondary"
                            onClick={() => void restore(i.key, v.id)}
                          >
                            {copy.cms.restore}
                          </button>
                        </li>
                      ))
                    )}
                  </ul>
                )}
              </div>
            ))}
        </section>
      ))}

      {/* Предпросмотр */}
      <section className="cms-group cms-preview">
        <h2>{copy.cms.previewTitle}</h2>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={copy.cms.previewQuestion}
        />
        <button className="btn-secondary" onClick={() => void runPreview()}>
          {copy.cms.previewBtn}
        </button>
        {preview && (
          <>
            <h3>{copy.cms.previewInterp}</h3>
            <pre className="cms-pre">{preview.interpretation_prompt}</pre>
            <h3>{copy.cms.previewCheck}</h3>
            <pre className="cms-pre">{preview.question_check_prompt}</pre>
          </>
        )}
      </section>

      <CmsPresets />
    </main>
  );
}
