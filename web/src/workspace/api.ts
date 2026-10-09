/**
 * API client for the COTRACE local server.
 * Connects to /api endpoints and /api/events SSE stream per STANDALONE_V1_PLAN §3.2 & §3.3.
 */

import type { Chat, ChatSummary } from './types';

export const API_BASE = '/api';

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
      'chat_ready',
      'pipeline_status',
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

