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
