import React, { useEffect, useState } from 'react';
import { Check, Key, Loader2, Server, Shield, Sparkles, X, AlertCircle } from 'lucide-react';
import { fetchSettings, updateSettings, testConnection, type Settings } from './api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AVAILABLE_FAST_MODELS = [
  'gemini-3.1-flash-lite',
  'gemini-3.5-flash-lite',
  'gemini-2.0-flash-lite',
  'deepseek-v4-flash',
  'gpt-oss-120b',
  'claude-3-5-haiku',
  'gpt-4o-mini',
];

const AVAILABLE_MAIN_MODELS = [
  'gemini-3.5-flash',
  'gemini-2.5-flash',
  'gemini-2.0-flash',
  'deepseek-chat',
  'deepseek-reasoner',
  'claude-3-7-sonnet',
  'claude-3-5-sonnet',
  'gpt-4o',
  'gpt-4o-mini',
  'qwen3.5-9b',
];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message?: string; error?: string } | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form state
  const [providerUrl, setProviderUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [hasApiKey, setHasApiKey] = useState(false);
  const [keyPreview, setKeyPreview] = useState('');
  const [modelFast, setModelFast] = useState('gemini-3.1-flash-lite');
  const [modelMain, setModelMain] = useState('gemini-3.5-flash');
  const [chatModel, setChatModel] = useState('gemini-3.5-flash');
  const [monthlyBudget, setMonthlyBudget] = useState(20.0);
  const [parallelJobs, setParallelJobs] = useState(2);

  useEffect(() => {
    if (!isOpen) {
      setTestResult(null);
      setSavedSuccess(false);
      return;
    }

    setLoading(true);
    fetchSettings()
      .then((data: Settings) => {
        setProviderUrl(data.provider_url || '');
        setHasApiKey(data.has_api_key);
        setKeyPreview(data.key_preview || '');
        setModelFast(data.model_fast || 'gemini-3.1-flash-lite');
        setModelMain(data.model_main || 'gemini-3.5-flash');
        setChatModel(data.chat_model || 'gemini-3.5-flash');
        setMonthlyBudget(data.monthly_budget ?? 20.0);
        setParallelJobs(data.parallel_jobs ?? 2);
        setApiKey('');
      })
      .catch((err) => {
        console.error('Failed to load settings', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testConnection({
        provider_url: providerUrl,
        api_key: apiKey ? apiKey : undefined,
      });
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ ok: false, error: err?.message || 'Connection test failed' });
    } finally {
      setTesting(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const patch: any = {
        provider_url: providerUrl,
        model_fast: modelFast,
        model_main: modelMain,
        model_step2: modelMain,
        model_step3: modelMain,
        chat_model: chatModel,
        monthly_budget: Number(monthlyBudget),
        parallel_jobs: Number(parallelJobs),
      };
      if (apiKey.trim()) {
        patch.api_key = apiKey.trim();
      }
      const updated = await updateSettings(patch);
      setHasApiKey(updated.has_api_key);
      setKeyPreview(updated.key_preview);
      setApiKey('');
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 700);
    } catch (err: any) {
      alert(`Error saving settings: ${err?.message || 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="settings-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <div className="settings-modal-card" onClick={(e) => e.stopPropagation()}>
        <header className="settings-modal-header">
          <div className="settings-title-wrap">
            <Shield size={20} className="settings-icon-primary" />
            <h2 id="settings-title">Settings & Model Routing</h2>
          </div>
          <button className="settings-close-btn" onClick={onClose} aria-label="Close settings">
            <X size={18} />
          </button>
        </header>

        {loading ? (
          <div className="settings-loading-state">
            <Loader2 size={24} className="spin-icon" />
            <span>Loading configuration…</span>
          </div>
        ) : (
          <form onSubmit={handleSave} className="settings-form">
            <div className="settings-section">
              <h3><Server size={15} /> Provider & Credentials</h3>
              <div className="settings-field">
                <label htmlFor="provider-url">OpenAI-Compatible Base URL</label>
                <input
                  id="provider-url"
                  type="text"
                  value={providerUrl}
                  onChange={(e) => setProviderUrl(e.target.value)}
                  placeholder="https://generativelanguage.googleapis.com/v1beta/openai/"
                  required
                />
              </div>

              <div className="settings-field">
                <label htmlFor="api-key">
                  <span>API Key</span>
                  {hasApiKey && <small className="key-status-badge">Configured ({keyPreview})</small>}
                </label>
                <div className="input-with-icon">
                  <Key size={14} className="input-field-icon" />
                  <input
                    id="api-key"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={hasApiKey ? 'Enter new key to replace existing…' : 'Enter API key…'}
                  />
                </div>
                <p className="field-hint">
                  Saved with mode <code>0600</code> permissions to <code>$COTRACE_HOME/secrets.json</code>. Write-only; never leaked or returned in API responses.
                </p>
              </div>

              <div className="test-connection-row">
                <button
                  type="button"
                  className="test-btn"
                  onClick={handleTestConnection}
                  disabled={testing || (!apiKey && !hasApiKey)}
                >
                  {testing ? <Loader2 size={13} className="spin-icon" /> : null}
                  Test Connection
                </button>
                {testResult && (
                  <span className={`test-feedback ${testResult.ok ? 'success' : 'failure'}`}>
                    {testResult.ok ? <Check size={14} /> : <AlertCircle size={14} />}
                    {testResult.ok ? (testResult.message || 'Connected successfully') : testResult.error}
                  </span>
                )}
              </div>
            </div>

            <div className="settings-section">
              <h3><Sparkles size={15} /> Model Routing</h3>
              <div className="settings-grid">
                <div className="settings-field">
                  <label htmlFor="model-fast">Step 1a Model (Extraction)</label>
                  <select
                    id="model-fast"
                    value={modelFast}
                    onChange={(e) => setModelFast(e.target.value)}
                  >
                    {AVAILABLE_FAST_MODELS.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>

                <div className="settings-field">
                  <label htmlFor="model-main">Main Model (Steps 1b, 2, 3)</label>
                  <select
                    id="model-main"
                    value={modelMain}
                    onChange={(e) => setModelMain(e.target.value)}
                  >
                    {AVAILABLE_MAIN_MODELS.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="settings-section">
              <h3>Budget & Concurrency</h3>
              <div className="settings-grid">
                <div className="settings-field">
                  <label htmlFor="monthly-budget">Monthly Budget ($ USD)</label>
                  <input
                    id="monthly-budget"
                    type="number"
                    step="1"
                    min="1"
                    max="1000"
                    value={monthlyBudget}
                    onChange={(e) => setMonthlyBudget(parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div className="settings-field">
                  <label htmlFor="parallel-jobs">Parallel Jobs</label>
                  <input
                    id="parallel-jobs"
                    type="number"
                    min="1"
                    max="8"
                    value={parallelJobs}
                    onChange={(e) => setParallelJobs(parseInt(e.target.value, 10) || 1)}
                  />
                </div>
              </div>
            </div>

            <footer className="settings-modal-footer">
              <button type="button" className="btn-cancel" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-save" disabled={saving}>
                {savedSuccess ? (
                  <>
                    <Check size={14} /> Saved!
                  </>
                ) : saving ? (
                  <>
                    <Loader2 size={14} className="spin-icon" /> Saving…
                  </>
                ) : (
                  'Save Settings'
                )}
              </button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
}
