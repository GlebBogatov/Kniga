import { Fragment, useEffect, useState } from "react";

import { DEMO, api } from "../api/client";
import { useAuth } from "../auth";
import { copy } from "../copy";
import type { AdminMetrics, AdminUser } from "../types";

export function AdminPage() {
  const { user, loading } = useAuth();
  const isAdmin = user?.role === "admin" || (DEMO && !!user);

  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<AdminUser | null>(null);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);

  async function load() {
    setMetrics(await api.adminMetrics());
    setUsers(await api.adminUsers(query.trim() || undefined));
  }

  useEffect(() => {
    if (isAdmin) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  function replaceUser(u: AdminUser) {
    setUsers((prev) => (prev ? prev.map((x) => (x.id === u.id ? { ...x, ...u } : x)) : prev));
    void api.adminMetrics().then(setMetrics);
  }

  async function act(fn: Promise<AdminUser>) {
    replaceUser(await fn);
  }

  async function openPayments(u: AdminUser) {
    if (expanded?.id === u.id) {
      setExpanded(null);
      return;
    }
    setExpanded(await api.adminUser(u.id));
  }

  async function refund(u: AdminUser, paymentId: number) {
    await api.adminRefund(u.id, paymentId);
    setExpanded(await api.adminUser(u.id));
  }

  if (loading) {
    return (
      <main className="app">
        <p className="muted">{copy.journal.loading}</p>
      </main>
    );
  }

  if (!isAdmin) {
    return (
      <main className="app">
        <a className="legal-back" href="#/">
          ← {copy.footer.back}
        </a>
        <p className="muted">{copy.admin.noAccess}</p>
      </main>
    );
  }

  return (
    <main className="app admin">
      <a className="legal-back" href="#/">
        ← {copy.footer.back}
      </a>
      <h1 className="legal-title">{copy.admin.title}</h1>

      {metrics && (
        <div className="metric-grid">
          <Metric label={copy.admin.metricUsers} value={metrics.users_total} />
          <Metric label={copy.admin.metricPremium} value={metrics.users_premium} />
          <Metric label={copy.admin.metricReadings} value={metrics.readings_total} />
          <Metric label={copy.admin.metricPayments} value={metrics.payments_succeeded} />
          <Metric
            label={copy.admin.metricRevenue}
            value={metrics.revenue_total.toLocaleString("ru-RU")}
          />
        </div>
      )}

      <form
        className="admin-search"
        onSubmit={(e) => {
          e.preventDefault();
          void load();
        }}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={copy.admin.search}
        />
      </form>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>{copy.admin.colUser}</th>
              <th>{copy.admin.colPlan}</th>
              <th>{copy.admin.colReadings}</th>
              <th>{copy.admin.colStatus}</th>
              <th>{copy.admin.colActions}</th>
            </tr>
          </thead>
          <tbody>
            {(users ?? []).map((u) => (
              <Fragment key={u.id}>
                <tr>
                  <td>
                    <div className="au-name">{u.name ?? "—"}</div>
                    <div className="muted au-email">
                      {u.email} · {u.provider.toUpperCase()}
                    </div>
                  </td>
                  <td>
                    <span
                      className={
                        u.subscription.plan === "premium" ? "plan-badge premium" : "plan-badge"
                      }
                    >
                      {u.subscription.plan === "premium"
                        ? copy.cabinet.planPremium
                        : copy.cabinet.planFree}
                    </span>
                  </td>
                  <td>{u.readings}</td>
                  <td className={u.is_blocked ? "au-blocked" : ""}>
                    {u.is_blocked ? copy.admin.blocked : copy.admin.active}
                  </td>
                  <td className="au-actions">
                    <button onClick={() => void act(api.adminBlock(u.id, !u.is_blocked))}>
                      {u.is_blocked ? copy.admin.unblock : copy.admin.block}
                    </button>
                    {u.subscription.plan === "premium" ? (
                      <button onClick={() => void act(api.adminSetFree(u.id))}>
                        {copy.admin.setFree}
                      </button>
                    ) : (
                      <button onClick={() => void act(api.adminGrant(u.id, "premium_month"))}>
                        {copy.admin.grant}
                      </button>
                    )}
                    <button onClick={() => void openPayments(u)}>{copy.admin.payments}</button>
                  </td>
                </tr>
                {expanded?.id === u.id && (
                  <tr className="au-payrow">
                    <td colSpan={5}>
                      {(expanded.payments ?? []).length === 0 ? (
                        <span className="muted">{copy.admin.noPayments}</span>
                      ) : (
                        <ul className="au-payments">
                          {(expanded.payments ?? []).map((p) => (
                            <li key={p.id}>
                              {new Date(p.created_at ?? "").toLocaleDateString("ru-RU")} ·{" "}
                              {p.amount.toLocaleString("ru-RU")} ₽ · {p.status}
                              {p.status === "succeeded" && (
                                <button
                                  className="au-refund"
                                  onClick={() => void refund(u, p.id)}
                                >
                                  {copy.admin.refund}
                                </button>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="metric-card">
      <div className="metric-value">{value}</div>
      <div className="metric-label muted">{label}</div>
    </div>
  );
}
