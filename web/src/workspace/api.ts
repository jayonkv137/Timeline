/**
 * API client for the COTRACE local server.
 * Connects to /api endpoints and /api/events SSE stream per STANDALONE_V1_PLAN §3.2 & §3.3.
 */

import type { Chat, ChatSummary, ImportReport } from './types';

export const API_BASE =
  typeof window !== 'undefined' && window.location.protocol === 'file:'
    ? 'http://127.0.0.1:8765/api'
    : '/api';

export async function fetchChats(): Promise<ChatSummary[]> {
  const res = await fetch(`${API_BASE}/chats`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch chats: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchBundle(id: string): Promise<Chat> {
  const res = await fetch(`${API_BASE}/chats/${encodeURIComponent(id)}`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch chat bundle '${id}': ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function createChat(params?: { title?: string; category?: string }): Promise<Chat> {
  const res = await fetch(`${API_BASE}/chats`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(params || {}),
  });
  if (!res.ok) {
    throw new Error(`Failed to create chat: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatMessageStream(
  chatId: string,
  text: string,
  callbacks: {
    onToken: (token: string) => void;
    onDone: (data: { chatId: string; pair: number; text: string }) => void;
    onError: (error: string) => void;
  }
): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${encodeURIComponent(chatId)}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    const errJson = await res.json().catch(() => null);
    const errMsg = errJson?.detail || `Error sending message: ${res.status} ${res.statusText}`;
    callbacks.onError(errMsg);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError('ReadableStream not supported by browser environment');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = 'message';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.slice(6).trim();
        } else if (trimmed.startsWith('data:')) {
          const dataStr = trimmed.slice(5).trim();
          try {
            const data = JSON.parse(dataStr);
            if (currentEvent === 'token') {
              callbacks.onToken(data.token || data.text || '');
            } else if (currentEvent === 'done') {
              callbacks.onDone(data);
            } else if (currentEvent === 'error') {
              callbacks.onError(data.error || 'Server streaming error');
            }
          } catch {
            if (currentEvent === 'token') {
              callbacks.onToken(dataStr);
            }
          }
        }
      }
    }
  } catch (err: any) {
    callbacks.onError(err.message || 'Stream connection failed');
  }
}

export async function updateChatMeta(
  id: string,
  patch: { title?: string; category?: string }
): Promise<{ title?: string; category?: string }> {
  const res = await fetch(`${API_BASE}/chats/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(patch),
  });
  if (!res.ok) {
    throw new Error(`Failed to update chat '${id}': ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function trashChat(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to trash chat '${id}': ${res.status} ${res.statusText}`);
  }
}

export async function restoreChat(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/chats/${encodeURIComponent(id)}/restore`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to restore chat '${id}': ${res.status} ${res.statusText}`);
  }
}

export function subscribeEvents(
  onEvent: (event: string, data: any) => void,
  onError?: (err: Event) => void
): () => void {
  if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
    return () => {};
  }

  let source: EventSource | null = null;
  try {
    source = new EventSource(`${API_BASE}/events`);

    const knownEvents = [
      'chat_created',
      'chat_updated',
      'chat_trashed',
      'chat_restored',
      'pair_ready',
      'pair_flagged',
      'chat_ready',
      'pipeline_status',
      'queue_changed',
      'job_progress',
      'job_error',
      'budget_stop',
    ];

    for (const evt of knownEvents) {
      source.addEventListener(evt, (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data);
          onEvent(evt, parsed);
        } catch {
          onEvent(evt, e.data);
        }
      });
    }

    source.onerror = (err) => {
      if (onError) onError(err);
    };
  } catch (err) {
    console.warn('COTRACE: Could not initialize EventSource stream', err);
  }

  return () => {
    if (source) {
      source.close();
      source = null;
    }
  };
}

export interface Settings {
  provider_url: string;
  model_fast: string;
  model_main: string;
  model_step2: string;
  model_step3: string;
  chat_model: string;
  monthly_budget: number;
  parallel_jobs: number;
  has_api_key: boolean;
  key_preview: string;
}

export interface SettingsPatch {
  provider_url?: string;
  model_fast?: string;
  model_main?: string;
  model_step2?: string;
  model_step3?: string;
  chat_model?: string;
  monthly_budget?: number;
  parallel_jobs?: number;
  api_key?: string;
}

export interface ConnectionTestResult {
  ok: boolean;
  message?: string;
  error?: string;
  provider_url?: string;
}

export async function fetchSettings(): Promise<Settings> {
  const res = await fetch(`${API_BASE}/settings`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch settings: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function updateSettings(patch: SettingsPatch): Promise<Settings> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(patch),
  });
  if (!res.ok) {
    throw new Error(`Failed to update settings: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function testConnection(params?: {
  provider_url?: string;
  api_key?: string;
}): Promise<ConnectionTestResult> {
  const res = await fetch(`${API_BASE}/settings/test-connection`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(params || {}),
  });
  if (!res.ok) {
    throw new Error(`Connection test failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface UsageReport {
  month: string;
  spent_this_month: number;
  monthly_budget: number;
  remaining_budget: number;
  by_chat: Record<string, number>;
  by_step: Record<string, number>;
  by_model: Record<string, number>;
  recent_calls: Array<{
    timestamp: string;
    chat_id?: string;
    step: string;
    call?: string;
    model: string;
    tokens: { prompt: number; completion: number; total: number };
    cost: { prompt: number; completion: number; total: number };
    mode?: string;
  }>;
  total_calls: number;
}

export async function fetchUsage(month?: string): Promise<UsageReport> {
  const url = month ? `${API_BASE}/usage?month=${encodeURIComponent(month)}` : `${API_BASE}/usage`;
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch usage: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function uploadImport(file: File): Promise<{ importId: string; status: string; message?: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/imports`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`Upload failed: ${res.status} ${errText || res.statusText}`);
  }
  return res.json();
}

export async function fetchImportReport(importId: string): Promise<ImportReport> {
  const res = await fetch(`${API_BASE}/imports/${encodeURIComponent(importId)}`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch import report '${importId}': ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchImportsList(): Promise<Array<{ importId: string; status: string; totalConversations?: number; totalPairs?: number }>> {
  const res = await fetch(`${API_BASE}/imports`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch imports list: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Job {
  id: string;
  chatId: string;
  convId: string;
  title: string;
  status: 'queued' | 'running' | 'completed' | 'canceled' | 'failed' | 'paused';
  totalPairs: number;
  completedPairs: number;
  priority: number;
  mode?: string;
  error?: string | null;
}

export interface QueueStatus {
  isPaused: boolean;
  pauseReason: string | null;
  parallelLimit: number;
  runningCount: number;
  waitingCount: number;
  completedCount: number;
  failedCount: number;
  runningChats: string[];
  waitingChats: string[];
  isBackoff: boolean;
  backoffRemaining: number;
  jobs: Job[];
}

export async function fetchJobs(): Promise<QueueStatus> {
  const res = await fetch(`${API_BASE}/jobs`, {
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch jobs: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function processImportBatch(
  importId: string,
  conversationIds: string[],
  rehearsal: boolean = false
): Promise<{ status: string; enqueuedCount: number; jobs: Job[] }> {
  const res = await fetch(`${API_BASE}/imports/${encodeURIComponent(importId)}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ conversationIds, rehearsal }),
  });
  if (!res.ok) {
    throw new Error(`Failed to process import batch: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function mapNextJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/priority`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to map next: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function cancelJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to cancel job: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function pauseAllJobs(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/jobs/pause-all`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to pause jobs: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function resumeAllJobs(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/jobs/resume-all`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    throw new Error(`Failed to resume jobs: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function startRehearsal(
  chatIds?: string[],
  delaySeconds: number = 0.5
): Promise<{ status: string; enqueuedCount: number; jobs: Job[] }> {
  const res = await fetch(`${API_BASE}/jobs/rehearse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ chatIds: chatIds || [], delaySeconds }),
  });
  if (!res.ok) {
    throw new Error(`Failed to start rehearsal: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

