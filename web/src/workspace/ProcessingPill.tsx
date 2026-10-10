import { useState } from 'react';
import { ArrowUpCircle, Pause, Play, Square, X, AlertCircle, Sliders } from 'lucide-react';
import type { QueueStatus } from './api';

interface ProcessingPillProps {
  queueStatus: QueueStatus | null;
  onMapNext: (jobId: string) => Promise<void>;
  onCancel: (jobId: string) => Promise<void>;
  onPauseAll: () => Promise<void>;
  onResumeAll: () => Promise<void>;
  onOpenSettings?: () => void;
  onOpenUsage?: () => void;
}

export function ProcessingPill({
  queueStatus,
  onMapNext,
  onCancel,
  onPauseAll,
  onResumeAll,
  onOpenSettings,
  onOpenUsage,
}: ProcessingPillProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [confirmStopId, setConfirmStopId] = useState<string | null>(null);

  if (!queueStatus) return null;

  const { runningCount, waitingCount, isPaused, pauseReason, isBackoff, backoffRemaining, jobs } = queueStatus;
  const activeJobs = jobs.filter(j => j.status === 'running' || j.status === 'queued');

  // Pill disappears completely when no jobs are active or paused
  if (runningCount === 0 && waitingCount === 0 && !isPaused && !isBackoff) {
    return null;
  }

  // Budget stop special message (§3.2)
  if (pauseReason === 'budget_reached') {
    return (
      <div className="processing-pill-container">
        <button
          className="processing-pill pill-alert"
          onClick={onOpenUsage}
          title="Monthly budget cap reached. Click to view usage and raise cap."
        >
          <AlertCircle size={13} />
          <span>Paused · monthly budget reached · <u>Raise cap</u></span>
        </button>
      </div>
    );
  }

  // Auth / key error special message (§3.2, §5)
  if (pauseReason === 'missing_key' || pauseReason === 'auth_error') {
    return (
      <div className="processing-pill-container">
        <button
          className="processing-pill pill-alert"
          onClick={onOpenSettings}
          title="Can't reach the model. Click to check your API key in Settings."
        >
          <AlertCircle size={13} />
          <span>Can’t reach the model · check your key · <u>Settings</u></span>
        </button>
      </div>
    );
  }

  // Rate limit backoff special message (§3.2)
  if (isBackoff && backoffRemaining > 0) {
    return (
      <div className="processing-pill-container">
        <div className="processing-pill pill-warning">
          <span className="pill-dot warning" />
          <span>Rate-limited · backing off {Math.ceil(backoffRemaining)}s…</span>
        </div>
      </div>
    );
  }

  const label = isPaused
    ? `Paused · ${activeJobs.length} ${activeJobs.length === 1 ? 'chat' : 'chats'}`
    : `Mapping ${runningCount} ${runningCount === 1 ? 'chat' : 'chats'} · ${waitingCount} waiting`;

  return (
    <div className="processing-pill-container">
      {popoverOpen && (
        <div className="processing-popover" role="dialog" aria-label="Mapping queue controls">
          <div className="popover-header">
            <div>
              <strong>Mapping Queue</strong>
              <small>{activeJobs.length} active</small>
            </div>
            <div className="popover-actions">
              {isPaused ? (
                <button className="pill-btn primary" onClick={onResumeAll} title="Resume queue processing">
                  <Play size={12} /> Resume all
                </button>
              ) : (
                <button className="pill-btn" onClick={onPauseAll} title="Pause queue processing">
                  <Pause size={12} /> Pause all
                </button>
              )}
              {onOpenSettings && (
                <button className="icon-btn settings" onClick={onOpenSettings} title="Settings" aria-label="Open settings">
                  <Sliders size={13} />
                </button>
              )}
              <button className="icon-btn close" onClick={() => setPopoverOpen(false)} aria-label="Close popover">
                <X size={14} />
              </button>
            </div>
          </div>

          <div className="popover-list">
            {activeJobs.map((j) => {
              const isRunning = j.status === 'running';
              const progressPct = Math.round(((j.completedPairs || 0) / (j.totalPairs || 1)) * 100);

              return (
                <div key={j.id} className={`popover-row ${isRunning ? 'row-running' : 'row-waiting'}`}>
                  <div className="row-info">
                    <span className="row-title" title={j.title}>{j.title}</span>
                    <span className="row-sub">
                      {isRunning
                        ? `Mapping · ${j.completedPairs} of ${j.totalPairs}`
                        : `Waiting · ${j.totalPairs} exchanges`}
                    </span>
                    {isRunning && (
                      <div className="row-progress-track">
                        <div className="row-progress-fill" style={{ width: `${progressPct}%` }} />
                      </div>
                    )}
                  </div>

                  <div className="row-controls">
                    {!isRunning && (
                      <button
                        className="pill-btn map-next"
                        onClick={() => onMapNext(j.id)}
                        title="Move to front of queue"
                      >
                        <ArrowUpCircle size={12} /> Map next
                      </button>
                    )}
                    <button
                      className="pill-btn stop"
                      onClick={() => setConfirmStopId(j.id)}
                      title="Stop mapping"
                    >
                      <Square size={11} /> Stop
                    </button>
                  </div>

                  {confirmStopId === j.id && (
                    <div className="stop-confirm-modal">
                      <p>Stop mapping? Mapped exchanges are kept; nothing is deleted.</p>
                      <div className="confirm-buttons">
                        <button
                          className="pill-btn danger"
                          onClick={async () => {
                            await onCancel(j.id);
                            setConfirmStopId(null);
                          }}
                        >
                          Confirm stop
                        </button>
                        <button className="pill-btn" onClick={() => setConfirmStopId(null)}>
                          Keep mapping
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <button
        className={`processing-pill ${isPaused ? 'pill-paused' : ''}`}
        onClick={() => setPopoverOpen(!popoverOpen)}
        aria-expanded={popoverOpen}
        aria-label={label}
      >
        <span className={`pill-dot ${isPaused ? 'paused' : 'active'}`} />
        <span className="pill-text">{label}</span>
      </button>
    </div>
  );
}
