import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy } from "../copy";
import type { PresetAdmin } from "../types";

type Edit = Pick<
  PresetAdmin,
  "title" | "subtitle" | "question_template" | "prompt_focus" | "topic" | "is_active"
>;

export function CmsPresets() {
  const [items, setItems] = useState<PresetAdmin[] | null>(null);
  const [edits, setEdits] = useState<Record<number, Edit>>({});
  const [saved, setSaved] = useState<number | null>(null);

  async function reload() {
    const list = await api.cmsPresets();
    setItems(list);
    setEdits(
      Object.fromEntries(
        list.map((p) => [
          p.id,
          {
            title: p.title,
            subtitle: p.subtitle,
            question_template: p.question_template,
            prompt_focus: p.prompt_focus,
            topic: p.topic,
            is_active: p.is_active,
          },
        ]),
      ),
    );
  }

  useEffect(() => {
    void reload();
  }, []);

  function set(id: number, patch: Partial<Edit>) {
    setEdits((p) => ({ ...p, [id]: { ...p[id], ...patch } }));
  }

  async function save(id: number) {
    await api.cmsPresetUpdate(id, edits[id]);
    setSaved(id);
    window.setTimeout(() => setSaved(null), 1500);
    await reload();
  }
  async function remove(id: number) {
    if (!window.confirm(copy.cms.pDeleteConfirm)) return;
    await api.cmsPresetDelete(id);
    await reload();
  }
  async function add() {
    await api.cmsPresetCreate({ title: "Новый вопрос", topic: "other", is_active: true });
    await reload();
  }

  return (
    <section className="cms-group">
      <h2>{copy.cms.presetsTitle}</h2>
      <p className="muted">{copy.cms.presetsIntro}</p>

      {(items ?? []).map((p) => {
        const e = edits[p.id];
        if (!e) return null;
        return (
          <div key={p.id} className="cms-preset">
            <div className="cms-preset-grid">
              <label className="cms-field">
                <span>{copy.cms.pTitle}</span>
                <input value={e.title} onChange={(ev) => set(p.id, { title: ev.target.value })} />
              </label>
              <label className="cms-field">
                <span>{copy.cms.pSubtitle}</span>
                <input
                  value={e.subtitle}
                  onChange={(ev) => set(p.id, { subtitle: ev.target.value })}
                />
              </label>
              <label className="cms-field">
                <span>{copy.cms.pTopic}</span>
                <input value={e.topic} onChange={(ev) => set(p.id, { topic: ev.target.value })} />
              </label>
              <label className="cms-field cms-check">
                <input
                  type="checkbox"
                  checked={e.is_active}
                  onChange={(ev) => set(p.id, { is_active: ev.target.checked })}
                />
                <span>{copy.cms.pActive}</span>
              </label>
            </div>
            <label className="cms-field">
              <span>{copy.cms.pQuestion}</span>
              <input
                value={e.question_template}
                onChange={(ev) => set(p.id, { question_template: ev.target.value })}
              />
            </label>
            <label className="cms-field">
              <span>{copy.cms.pFocus}</span>
              <textarea
                rows={2}
                value={e.prompt_focus}
                onChange={(ev) => set(p.id, { prompt_focus: ev.target.value })}
              />
            </label>
            <div className="cms-actions">
              <button className="btn-secondary" onClick={() => void save(p.id)}>
                {copy.cms.pSave}
              </button>
              {saved === p.id && <span className="muted">{copy.cms.pSaved}</span>}
              <button className="btn-danger" onClick={() => void remove(p.id)}>
                {copy.cms.pDelete}
              </button>
            </div>
          </div>
        );
      })}

      <button className="btn-secondary cms-add" onClick={() => void add()}>
        + {copy.cms.pAdd}
      </button>
    </section>
  );
}
