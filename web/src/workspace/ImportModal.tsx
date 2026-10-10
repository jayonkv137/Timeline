import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckSquare,
  Loader2,
  Lock,
  RefreshCw,
  Search,
  Square,
  Upload,
  X,
  Zap,
} from 'lucide-react';
import { fetchImportReport, uploadImport } from './api';
import type { ImportReport } from './types';
import './import.css';

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProcessBatch?: (importId: string, selectedConvIds: string[]) => void;
}

export function ImportModal({ isOpen, onClose, onProcessBatch }: ImportModalProps) {
  const [report, setReport] = useState<ImportReport | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Controls
  const [searchQuery, setSearchQuery] = useState('');
  const [minExchanges, setMinExchanges] = useState(false);
  const [fidelityFilter, setFidelityFilter] = useState<'all' | 'clean' | 'degraded' | 'unusable'>('all');
  const [sortBy, setSortBy] = useState<'pairs-desc' | 'pairs-asc' | 'date-desc' | 'date-asc' | 'cost-desc' | 'title-asc'>('pairs-desc');

  // Selected conversation IDs
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) {
      // Reset modal state on close
      setReport(null);
      setUploading(false);
      setError(null);
      setSelectedIds(new Set());
      setSearchQuery('');
      setMinExchanges(false);
      setFidelityFilter('all');
      setSortBy('pairs-desc');
    }
  }, [isOpen]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (isOpen && e.key === 'Escape') {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleFile = async (file: File) => {
    const isZip = file.name.toLowerCase().endsWith('.zip');
    const isJson = file.name.toLowerCase().endsWith('.json');
    const isMd = file.name.toLowerCase().endsWith('.md');

    if (!isZip && !isJson && !isMd) {
      setError('Please select an export archive (.zip) or conversation file (.json, .md).');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const uploadRes = await uploadImport(file);
      const importId = uploadRes.importId;

      // Poll until ready (standard archive takes < 0.5s)
      const pollStart = Date.now();
      const checkStatus = async () => {
        try {
          const rep = await fetchImportReport(importId);
          if (rep.status === 'ready') {
            setReport(rep);
            // Default selection: select all viable chats (pairs >= 1, not unusable, not duplicate)
            const initialSelected = new Set<string>();
            for (const c of rep.conversations) {
              if (c.pairs >= 1 && c.fidelityGrade !== 'unusable' && !c.isDuplicate) {
                initialSelected.add(c.convId);
              }
            }
            setSelectedIds(initialSelected);
            setUploading(false);
          } else if (rep.status === 'failed') {
            setError(rep.error || 'Archive scan failed to extract conversations.');
            setUploading(false);
          } else {
            // Still scanning
            if (Date.now() - pollStart < 30000) {
              setTimeout(checkStatus, 350);
            } else {
              setError('Scan timed out. Please try uploading again.');
              setUploading(false);
            }
          }
        } catch (err: any) {
          setError(err?.message || 'Error checking scan status');
          setUploading(false);
        }
      };

      await checkStatus();
    } catch (err: any) {
      setError(err?.message || 'Upload failed. Check server connection.');
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => {
    setDragOver(false);
  };

  // Filtered & Sorted conversations
  const filteredConversations = useMemo(() => {
    if (!report) return [];

    let list = [...report.conversations];

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((c) =>
        c.rawTitle.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        c.convId.toLowerCase().includes(q) ||
        c.sensitiveTriggers.some((t) => t.toLowerCase().includes(q))
      );
    }

    // Filter by >= 3 exchanges
    if (minExchanges) {
      list = list.filter((c) => c.pairs >= 3);
    }

    // Filter by fidelity grade
    if (fidelityFilter !== 'all') {
      list = list.filter((c) => c.fidelityGrade === fidelityFilter);
    }

    // Sort
    list.sort((a, b) => {
      switch (sortBy) {
        case 'pairs-desc':
          return b.pairs - a.pairs;
        case 'pairs-asc':
          return a.pairs - b.pairs;
        case 'date-desc':
          return (b.createdAt || '').localeCompare(a.createdAt || '');
        case 'date-asc':
          return (a.createdAt || '').localeCompare(b.createdAt || '');
        case 'cost-desc':
          return b.estimate.cost.expected - a.estimate.cost.expected;
        case 'title-asc':
          return a.rawTitle.localeCompare(b.rawTitle);
        default:
          return 0;
      }
    });

    return list;
  }, [report, searchQuery, minExchanges, fidelityFilter, sortBy]);

  // Selected totals & Cost Calculation
  const selectedCount = selectedIds.size;
  const { selectedPairs, selectedCostLow, selectedCostHigh } = useMemo(() => {
    if (!report) return { selectedPairs: 0, selectedCostLow: 0, selectedCostHigh: 0 };
    let pairs = 0;
    let low = 0;
    let high = 0;
    for (const c of report.conversations) {
      if (selectedIds.has(c.convId)) {
        pairs += c.pairs;
        low += c.estimate.cost.low;
        high += c.estimate.cost.high;
      }
    }
    return {
      selectedPairs: pairs,
      selectedCostLow: low,
      selectedCostHigh: high,
    };
  }, [report, selectedIds]);

  const toggleSelect = (convId: string) => {
    const next = new Set(selectedIds);
    if (next.has(convId)) {
      next.delete(convId);
    } else {
      next.add(convId);
    }
    setSelectedIds(next);
  };

  const toggleSelectAllVisible = () => {
    const allVisibleSelected = filteredConversations.every((c) => selectedIds.has(c.convId));
    const next = new Set(selectedIds);
    if (allVisibleSelected) {
      for (const c of filteredConversations) {
        next.delete(c.convId);
      }
    } else {
      for (const c of filteredConversations) {
        next.add(c.convId);
      }
    }
    setSelectedIds(next);
  };

  const handleProcess = () => {
    if (!report || selectedCount === 0) return;
    const ids = Array.from(selectedIds);
    if (onProcessBatch) {
      onProcessBatch(report.importId, ids);
    } else {
      window.dispatchEvent(
        new CustomEvent('cotrace:import-process', {
          detail: { importId: report.importId, selectedConvIds: ids },
        })
      );
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="import-modal-backdrop" onClick={onClose}>
      <div className="import-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="import-modal-header">
          <div className="import-title-wrap">
            <Upload size={18} className="import-icon-primary" />
            <h2>Import Conversations</h2>
          </div>
          <button className="import-close-btn" aria-label="Close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        {!report ? (
          <div className="import-dropzone-container">
            {uploading ? (
              <div className="import-loading-state">
                <Loader2 size={36} className="settings-spinner" />
                <h3>Ingesting & Triaging Export</h3>
                <p>Simulating pairing and calculating pre-flight estimates (zero LLM calls)...</p>
              </div>
            ) : (
              <>
                <div
                  className={`import-dropzone ${dragOver ? 'dragover' : ''}`}
                  onDrop={onDrop}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="import-dropzone-icon-wrap">
                    <Upload size={28} />
                  </div>
                  <h3>Drop your export archive here</h3>
                  <p>Upload official Claude, ChatGPT, or Gemini chat export archives to review, filter, and triage conversations locally.</p>
                  <button
                    type="button"
                    className="import-browse-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                  >
                    Browse export file
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".zip,.json,.md"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        handleFile(e.target.files[0]);
                      }
                    }}
                  />
                  <div className="import-formats-hint">
                    <span>Supported formats:</span>
                    <span className="import-format-tag">.zip</span>
                    <span className="import-format-tag">.json</span>
                    <span className="import-format-tag">.md</span>
                  </div>
                </div>
                {error && (
                  <div className="settings-alert-box error" style={{ marginTop: '16px', maxWidth: '680px' }}>
                    <AlertCircle size={15} />
                    <span>{error}</span>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          <>
            {/* Summary Bar */}
            <div className="import-summary-bar">
              <div className="import-summary-left">
                <span className="import-filename-pill">{report.sourceFilename}</span>
                <span className="import-stat-badge">
                  {report.totalConversations} conversations
                </span>
                <span className="import-stat-badge">
                  {report.totalPairs.toLocaleString()} pairs
                </span>
                <span className="import-stat-badge">
                  Clean: {report.fidelity.clean} · Degraded: {report.fidelity.degraded} · Unusable: {report.fidelity.unusable}
                </span>
                {report.sensitiveCount > 0 && (
                  <span className="import-stat-badge" style={{ color: '#fbbf24', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
                    <Lock size={11} style={{ marginRight: '4px' }} />
                    {report.sensitiveCount} Sensitive Flagged
                  </span>
                )}
              </div>
              <button
                className="import-reupload-btn"
                onClick={() => {
                  setReport(null);
                  setSelectedIds(new Set());
                }}
              >
                <RefreshCw size={12} />
                Upload different file
              </button>
            </div>

            {/* Filter and Search Bar */}
            <div className="import-filter-bar">
              <div className="import-filter-left">
                <div className="import-search-wrap">
                  <Search size={13} style={{ color: 'var(--color-text-muted)' }} />
                  <input
                    type="text"
                    placeholder="Search by title or sensitive keyword..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>

                <button
                  type="button"
                  className={`import-filter-pill-btn ${minExchanges ? 'active' : ''}`}
                  onClick={() => setMinExchanges(!minExchanges)}
                  title="Filter out 1-2 turn quick queries"
                >
                  ≥ 3 exchanges
                </button>

                <select
                  className="import-sort-select"
                  value={fidelityFilter}
                  onChange={(e) => setFidelityFilter(e.target.value as any)}
                >
                  <option value="all">All Grades</option>
                  <option value="clean">Clean ({report.fidelity.clean})</option>
                  <option value="degraded">Degraded ({report.fidelity.degraded})</option>
                  <option value="unusable">Unusable ({report.fidelity.unusable})</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Sort:</span>
                <select
                  className="import-sort-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                >
                  <option value="pairs-desc">Exchanges (High to Low)</option>
                  <option value="pairs-asc">Exchanges (Low to High)</option>
                  <option value="date-desc">Date (Newest first)</option>
                  <option value="date-asc">Date (Oldest first)</option>
                  <option value="cost-desc">Estimated Cost (High to Low)</option>
                  <option value="title-asc">Title (A-Z)</option>
                </select>
              </div>
            </div>

            {/* Review Table */}
            <div className="import-table-container">
              <table className="import-table">
                <thead>
                  <tr>
                    <th style={{ width: '40px', textAlign: 'center' }}>
                      <button
                        type="button"
                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit' }}
                        onClick={toggleSelectAllVisible}
                        title="Toggle selection for visible chats"
                      >
                        {filteredConversations.length > 0 &&
                        filteredConversations.every((c) => selectedIds.has(c.convId)) ? (
                          <CheckSquare size={14} style={{ color: 'var(--color-party-human-solid)' }} />
                        ) : (
                          <Square size={14} />
                        )}
                      </button>
                    </th>
                    <th>Title</th>
                    <th style={{ width: '90px' }}>Date</th>
                    <th style={{ width: '85px' }}>Exchanges</th>
                    <th style={{ width: '95px' }}>Fidelity</th>
                    <th style={{ width: '90px', textAlign: 'right' }}>Est. Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredConversations.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--color-text-muted)' }}>
                        No conversations match the current filters.
                      </td>
                    </tr>
                  ) : (
                    filteredConversations.map((c) => {
                      const isSelected = selectedIds.has(c.convId);
                      const dateStr = c.createdAt ? c.createdAt.slice(0, 10) : '—';
                      const costStr = `$${c.estimate.cost.expected.toFixed(3)}`;

                      return (
                        <tr
                          key={c.convId}
                          className={isSelected ? 'selected' : ''}
                          onClick={() => toggleSelect(c.convId)}
                        >
                          <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                            <button
                              type="button"
                              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit' }}
                              onClick={() => toggleSelect(c.convId)}
                            >
                              {isSelected ? (
                                <CheckSquare size={14} style={{ color: 'var(--color-party-human-solid)' }} />
                              ) : (
                                <Square size={14} />
                              )}
                            </button>
                          </td>
                          <td>
                            <div className="import-title-cell">
                              <span className="import-title-text" title={c.rawTitle}>
                                {c.rawTitle}
                              </span>
                              <div className="import-title-badges">
                                {c.sensitive && (
                                  <span
                                    className="badge-sensitive"
                                    title={`Sensitive triggers: ${c.sensitiveTriggers.join(', ')}`}
                                  >
                                    <Lock size={9} />
                                    Sensitive ({c.sensitiveTriggers.slice(0, 2).join(', ')})
                                  </span>
                                )}
                                {c.hasCode && (
                                  <span className="badge-code" title="Contains code blocks">
                                    Code
                                  </span>
                                )}
                                {c.isDuplicate && (
                                  <span className="badge-duplicate" title="Already exists in library">
                                    Duplicate
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td style={{ color: 'var(--color-text-muted)' }}>{dateStr}</td>
                          <td>
                            <strong>{c.pairs}</strong>
                            <span style={{ color: 'var(--color-text-muted)', marginLeft: '3px' }}>
                              {c.pairs === 1 ? 'pair' : 'pairs'}
                            </span>
                          </td>
                          <td>
                            <span className={`fidelity-pill ${c.fidelityGrade}`}>
                              {c.fidelityGrade}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }} className="estimate-cell">
                            {costStr}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer (Cost Gate) */}
            <div className="import-modal-footer">
              <div className="import-footer-info">
                <span>
                  Selected: <strong>{selectedCount}</strong> of {report.totalConversations} chats ({selectedPairs} pairs)
                </span>
              </div>
              <div className="import-footer-actions">
                <button type="button" className="import-cancel-btn" onClick={onClose}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="import-costgate-btn"
                  disabled={selectedCount === 0}
                  onClick={handleProcess}
                  title={
                    selectedCount === 0
                      ? 'Select at least 1 chat to process'
                      : `Process ${selectedCount} chats for approximately $${selectedCostLow.toFixed(2)}–$${selectedCostHigh.toFixed(2)}`
                  }
                >
                  <Zap size={14} />
                  <span>
                    Process {selectedCount} chats · ≈ ${selectedCostLow.toFixed(2)}–{selectedCostHigh.toFixed(2)}
                  </span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
