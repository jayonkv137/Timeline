import { create } from 'zustand';

export interface DialogueTurn {
  pair: number;
  speaker: 'user' | 'ai';
  text: string;
  attachments: string[];
  ts: string;
}

export interface DirectionData {
  you_pct: number;
  ai_pct: number;
}

export interface DecisionsData {
  you_count: number;
  ai_count: number;
  latest_ai_example: string | null;
}

export interface TimelineRequirement {
  outcome_id: string;
  req_id: string;
  label: string;
  op: 'create' | 'revise' | 'delete';
  delta_you: number;
  delta_ai: number;
  chip: 'blue' | 'grey' | 'orange';
}

export interface TimelineSlot {
  slot_id: string;
  origin: 'user' | 'AI';
  status: 'open' | 'resolved' | 'abandoned';
  resolved_into: string | null;
}

export interface TimelineRow {
  pair: number;
  delta_you: number;
  delta_ai: number;
  summary: string;
  drawer: {
    requirements: TimelineRequirement[];
    slots: TimelineSlot[];
  };
}

export interface GoalNode {
  outcome_id: string;
  text: string;
  depth: number;
  is_current?: boolean;
  parent?: string | null;
  children?: string[];
}

export interface GoalData {
  default_view: GoalNode[];
  full_tree: GoalNode[];
}

export interface HowData {
  mode: 'CENTAUR' | 'COPILOT' | 'AUTOPILOT' | 'QUIET';
  signals: {
    w_you: number;
    w_ai: number;
    h_you: number;
    h_ai: number;
    substantive_user: boolean;
  };
  split: {
    centaur_pct: number;
    copilot_pct: number;
    autopilot_pct: number;
  };
}

export interface PairBundle {
  pair: number;
  direction: DirectionData;
  decisions: DecisionsData;
  timeline: TimelineRow;
  goal: GoalData;
  how: HowData;
}

export interface PanelBundle {
  pairs: PairBundle[];
}

interface AppState {
  activeChatId: string | null;
  setActiveChatId: (id: string | null) => void;
  selectedPairIdx: number;
  setSelectedPairIdx: (idx: number) => void;
  panelBundle: PanelBundle | null;
  setPanelBundle: (pb: PanelBundle) => void;
  dialogue: DialogueTurn[];
  setDialogue: (dlg: DialogueTurn[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeChatId: null, // default to clean empty state on startup
  setActiveChatId: (id) => set({ activeChatId: id }),
  selectedPairIdx: 0,
  setSelectedPairIdx: (idx) => set({ selectedPairIdx: idx }),
  panelBundle: null,
  setPanelBundle: (pb) => set({ panelBundle: pb }),
  dialogue: [],
  setDialogue: (dlg) => set({ dialogue: dlg }),
}));
