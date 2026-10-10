import { useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, CheckCircle2, Layers, Loader2, RefreshCw, WifiOff, X, Zap } from 'lucide-react';
import { fetchUsage, type UsageReport } from './api';

interface UsageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEFAULT_REPORT: UsageReport = {
  month: new Date().toISOString().slice(0, 7),
  spent_this_month: 0.0,
  monthly_budget: 20.0,
  remaining_budget: 20.0,
  by_chat: {},
  by_step: {},
  by_model: {},
  recent_calls: [],
  total_calls: 0,
};

export function UsageModal({ isOpen, onClose }: UsageModalProps) {
  const [report, setReport] = useState<UsageReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  function loadData() {
    setLoading(true);
    fetchUsage()
      .then((data) => {
        setReport(data);
        setIsOfflineMode(false);
      })
      .catch((err) => {
        console.warn('COTRACE: Could not connect to live usage API, falling back to preview mode:', err);
        setReport(DEFAULT_REPORT);
        setIsOfflineMode(true);
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const spent = report?.spent_this_month ?? 0;
  const budget = report?.monthly_budget ?? 20;
  const remaining = report?.remaining_budget ?? 0;
  const pct = budget > 0 ? Math.min(100, Math.round((spent / budget) * 100)) : 0;
  const isCapped = remaining <= 0 && budget > 0;
  const isNearCap = pct >= 85 && !isCapped;

  return (
    <div
      className="settings-modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="usage-modal-title"
    >
      <div className="usage-modal-card" onClick={(e) => e.stopPropagation()}>
        <header className="settings-modal-header">
          <div className="settings-title-wrap">
            <BarChart3 size={18} className="usage-icon-primary" />
            <h2 id="usage-modal-title">Usage & Budget Guard</h2>
            {report?.month && <span className="usage-month-pill">{report.month}</span>}
          </div>
          <div className="usage-header-actions">
            <button
              className="icon-button"
              aria-label="Refresh usage data"
              title="Refresh"
              onClick={loadData}
              disabled={loading}
            >
              <RefreshCw size={15} className={loading ? 'spin-icon' : ''} />
            </button>
            <button className="settings-close-btn" onClick={onClose} aria-label="Close usage modal">
              <X size={17} />
            </button>
          </div>
        </header>

        {loading && !report ? (
          <div className="settings-loading-state">
            <Loader2 size={24} className="spin-icon" />
            <span>Calculating usage ledger…</span>
          </div>
        ) : report ? (
          <div className="usage-content">
            {isOfflineMode && (
              <div className="usage-offline-notice">
                <WifiOff size={15} />
                <div className="usage-offline-text">
                  <strong>Offline Preview Mode</strong>
                  <span>
                    Backend server not connected. Showing default budget allowance ($20.00). Open <code>http://127.0.0.1:8765</code> while <code>./cotrace start</code> is running for live metered spend.
                  </span>
                </div>
                <button className="usage-retry-btn" onClick={loadData} disabled={loading}>
                  Retry
                </button>
              </div>
            )}
            {/* Top Budget Progress Card */}
            <div className={`usage-budget-card ${isCapped ? 'capped' : isNearCap ? 'warning' : ''}`}>
              <div className="usage-card-top">
                <div>
                  <span className="eyebrow">MONTHLY SPEND</span>
                  <div className="usage-number-headline">
                    ${spent.toFixed(4)}
                    <span className="usage-cap-label">of ${budget.toFixed(2)} cap</span>
                  </div>
                </div>
                <div className="usage-badge-wrap">
                  {isCapped ? (
                    <span className="usage-status-badge capped">
                      <AlertTriangle size={12} /> Budget Cap Reached
                    </span>
                  ) : (
                    <span className="usage-status-badge active">
                      <CheckCircle2 size={12} /> ${remaining.toFixed(2)} Remaining
                    </span>
                  )}
                </div>
              </div>

              <div className="usage-progress-bar-track">
                <div
                  className={`usage-progress-bar-fill ${isCapped ? 'danger' : isNearCap ? 'warning' : 'healthy'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>

              <div className="usage-progress-meta">
                <span>{pct}% of monthly allowance consumed</span>
                <span>{report.total_calls} metered calls</span>
              </div>

              {isCapped && (
                <div className="usage-cap-alert">
                  <AlertTriangle size={15} />
                  <span>
                    New LLM jobs will refuse to start until the monthly budget is increased in Settings or the monthly cycle resets.
                  </span>
                </div>
              )}
            </div>

            {/* Breakdown Columns: By Step and By Model */}
            <div className="usage-grid">
              <div className="usage-section-box">
                <span className="eyebrow"><Layers size={13} /> SPEND BY PIPELINE STEP</span>
                <div className="usage-breakdown-list">
                  {Object.keys(report.by_step).length === 0 ? (
                    <p className="quiet-empty">No calls recorded for this month.</p>
                  ) : (
                    Object.entries(report.by_step)
                      .sort(([, a], [, b]) => b - a)
                      .map(([step, cost]) => (
                        <div key={step} className="usage-breakdown-row">
                          <span className="step-name">{step}</span>
                          <span className="step-cost">${cost.toFixed(4)}</span>
                        </div>
                      ))
                  )}
                </div>
              </div>

              <div className="usage-section-box">
                <span className="eyebrow"><Zap size={13} /> SPEND BY MODEL</span>
                <div className="usage-breakdown-list">
                  {Object.keys(report.by_model).length === 0 ? (
                    <p className="quiet-empty">No model calls recorded.</p>
                  ) : (
                    Object.entries(report.by_model)
                      .sort(([, a], [, b]) => b - a)
                      .map(([model, cost]) => (
                        <div key={model} className="usage-breakdown-row">
                          <span className="model-name">{model}</span>
                          <span className="step-cost">${cost.toFixed(4)}</span>
                        </div>
                      ))
                  )}
                </div>
              </div>
            </div>

            {/* By Chat List */}
            {Object.keys(report.by_chat).length > 0 && (
              <div className="usage-section-box">
                <span className="eyebrow">SPEND BY CONVERSATION</span>
                <div className="usage-chats-list">
                  {Object.entries(report.by_chat)
                    .sort(([, a], [, b]) => b - a)
                    .map(([chatId, cost]) => (
                      <div key={chatId} className="usage-breakdown-row">
                        <span className="chat-id-name">{chatId}</span>
                        <span className="step-cost">${cost.toFixed(4)}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Recent Calls Log */}
            <div className="usage-section-box">
              <span className="eyebrow">RECENT METERED CALLS ({report.recent_calls.length})</span>
              <div className="usage-calls-table-wrap">
                {report.recent_calls.length === 0 ? (
                  <p className="quiet-empty">No metered LLM activity in this month yet.</p>
                ) : (
                  <table className="usage-calls-table">
                    <thead>
                      <tr>
                        <th>Time (UTC)</th>
                        <th>Step</th>
                        <th>Model</th>
                        <th>Tokens</th>
                        <th>Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.recent_calls.slice(0, 15).map((call, idx) => (
                        <tr key={idx}>
                          <td>{call.timestamp.slice(11, 19)}</td>
                          <td><code>{call.step}</code></td>
                          <td>{call.model}</td>
                          <td>{call.tokens.total.toLocaleString()}</td>
                          <td className="cost-cell">${call.cost.total.toFixed(5)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
