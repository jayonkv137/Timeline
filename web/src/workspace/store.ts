import { create } from 'zustand';
import seed from './data.generated.json';
import type { Chat, ChatSummary, ChatView, LoadingState } from './types';
import { newView } from './types';
import { fetchBundle, fetchChats, subscribeEvents } from './api';

const defaultChats = seed.chats as unknown as Chat[];

function checkOffline(): boolean {
  if (typeof window === 'undefined') return true;
  if (window.location.protocol === 'file:') return true;
  const params = new URLSearchParams(window.location.search);
  return params.get('offline') === '1';
}

interface State {
  chats: Chat[];
  tabs: string[];
  active: string;
  views: Record<string, ChatView>;
  loading: LoadingState;
  error: string | null;
  isOffline: boolean;
  open: (id: string) => void;
  close: (id: string) => void;
  patch: (id: string, p: Partial<ChatView>) => void;
  newChat: () => void;
  appendDraft: (id: string, text: string) => void;
  loadBundle: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export const useWorkspace = create<State>((set, get) => ({
  chats: defaultChats,
  tabs: defaultChats.length > 1 ? [defaultChats[0].id, defaultChats[1].id] : (defaultChats[0] ? [defaultChats[0].id] : []),
  active: defaultChats[0]?.id || 'brain',
  views: Object.fromEntries(defaultChats.map(c => [c.id, newView(c.totalPairs || 1)])),
  loading: checkOffline() ? 'ready' : 'loading',
  error: null,
  isOffline: checkOffline(),

  open: (id: string) => {
    set(s => id === 'brain' ? { active: id } : { active: id, tabs: s.tabs.includes(id) ? s.tabs : [...s.tabs, id] });
    if (id !== 'brain' && !get().isOffline) {
      get().loadBundle(id);
    }
  },

  close: (id: string) => set(s => {
    const i = s.tabs.indexOf(id);
    const tabs = s.tabs.filter(t => t !== id);
    return {
      tabs,
      active: s.active === id ? (tabs[Math.max(0, i - 1)] || 'brain') : s.active,
    };
  }),

  patch: (id: string, p: Partial<ChatView>) => set(s => ({
    views: {
      ...s.views,
      [id]: { ...(s.views[id] || newView()), ...p },
    },
  })),

  newChat: () => set(s => {
    const id = 'draft-' + Date.now();
    const draftChat: Chat = {
      id,
      title: 'New conversation',
      rootTitle: '',
      category: 'Draft',
      totalPairs: 0,
      dialogue: [],
      nodes: [],
      atoms: [],
      snapshots: [],
      summary: '',
      status: 'ready',
    };
    return {
      chats: [draftChat, ...s.chats],
      tabs: [...s.tabs, id],
      active: id,
      views: { ...s.views, [id]: newView() },
    };
  }),

  appendDraft: (id: string, text: string) => set(s => ({
    chats: s.chats.map(c => c.id !== id ? c : {
      ...c,
      title: c.title === 'New conversation' ? text.slice(0, 42) : c.title,
      dialogue: [...c.dialogue, {
        pair: c.totalPairs + 1,
        speaker: 'user',
        text,
        attachments: [],
        ts: new Date().toISOString(),
      }],
    }),
    views: {
      ...s.views,
      [id]: { ...(s.views[id] || newView()), draft: '' },
    },
  })),

  loadBundle: async (id: string) => {
    if (get().isOffline || id === 'brain' || id.startsWith('draft-')) return;
    try {
      const bundle = await fetchBundle(id);
      set(s => ({
        chats: s.chats.map(c => c.id === id ? { ...c, ...bundle } : c),
        views: {
          ...s.views,
          [id]: s.views[id] || newView(bundle.totalPairs || 1),
        },
      }));
    } catch (err: any) {
      console.warn(`COTRACE: Could not load bundle for ${id}:`, err);
    }
  },

  refresh: async () => {
    if (get().isOffline) return;
    set({ loading: 'loading', error: null });
    try {
      const list: ChatSummary[] = await fetchChats();
      if (!list || list.length === 0) {
        set({ loading: 'empty', chats: [] });
        return;
      }

      // Map summaries into Chat models, reusing existing loaded bundles if present
      const currentChats = get().chats;
      const updatedChats: Chat[] = list.map(item => {
        const existing = currentChats.find(c => c.id === item.id);
        if (existing && existing.nodes && existing.nodes.length > 0) {
          return {
            ...existing,
            title: item.title,
            category: item.category,
            totalPairs: item.totalPairs,
            status: item.status,
            source: item.source,
          };
        }
        return {
          id: item.id,
          title: item.title,
          rootTitle: item.title,
          category: item.category,
          totalPairs: item.totalPairs,
          dialogue: [],
          nodes: [],
          atoms: [],
          snapshots: [],
          summary: '',
          status: item.status,
          source: item.source,
        };
      });

      set({ chats: updatedChats, loading: 'ready' });

      // Fetch full bundle for active chat if needed
      const activeId = get().active;
      if (activeId && activeId !== 'brain') {
        get().loadBundle(activeId);
      }
    } catch (err: any) {
      console.warn('COTRACE: Server unavailable, falling back to bundled sample data:', err);
      set({
        chats: defaultChats,
        isOffline: true,
        loading: 'ready',
        error: null,
      });
    }
  },
}));

// Auto-initialize when running in browser
if (typeof window !== 'undefined' && !checkOffline()) {
  useWorkspace.getState().refresh();

  // Subscribe to live SSE events
  subscribeEvents((event, data) => {
    const st = useWorkspace.getState();
    if (event === 'chat_updated' && data?.chatId) {
      useWorkspace.setState(s => ({
        chats: s.chats.map(c => c.id === data.chatId ? {
          ...c,
          title: data.title || c.title,
          category: data.category || c.category,
        } : c),
      }));
    } else if (event === 'chat_trashed' && data?.chatId) {
      st.close(data.chatId);
      useWorkspace.setState(s => ({
        chats: s.chats.filter(c => c.id !== data.chatId),
      }));
    } else if (event === 'chat_restored') {
      st.refresh();
    } else if ((event === 'pair_ready' || event === 'chat_ready') && data?.chatId) {
      st.loadBundle(data.chatId);
    }
  });
}
