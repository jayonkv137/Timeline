export type Contributor = 'human' | 'ai';
export interface Turn { pair: number; speaker: 'user' | 'ai'; text: string; attachments: string[]; ts: string }
export interface Outcome { id:string; title:string; parent:string|null; related:string[]; born:number; x:number; y:number; root:boolean; sourcePair:number; sourceSpeaker:Contributor; evidence?:Evidence[] }
// Evidence (docs/EVIDENCE_SPEC.md §3): every source of an item, anchored to exact words with W3C TextQuote/TextPosition selectors.
export type EvidenceRole = 'introduced' | 'revised' | 'carried-out' | 'asked' | 'answered';
export type EvidenceMatch = 'exact' | 'normalized' | 'multipart' | 'message' | 'missing';
export interface EvidenceFragment { exact:string; prefix:string; suffix:string; start:number; end:number }
export interface Evidence { id:string; role:EvidenceRole; actionId:string|null; pair:number|null; speaker:Contributor|null; messageId?:string|null; textHash?:string|null; match:EvidenceMatch; fragments:EvidenceFragment[]; occurrences?:number; note?:string|null }
export interface Atom { id:string; nodeId:string; kind:'requirement'|'question'|'resolved'; text:string; question:string|null; origin:Contributor|null; resolver:Contributor|null; born:number; end:number; sourcePair:number; sourceSpeaker:Contributor|null; quote:string; choices:string[]; evidence?:Evidence[]; state?:'open'|'answered'|'dropped'; answeredAt?:number|null; droppedAt?:number|null }
export interface Mass { human:number; ai:number; delta:number }
export interface Snapshot { pair:number; mass:Record<string,Mass>; terminal:string }
export interface Chat { id:string; title:string; rootTitle:string; category:string; totalPairs:number; dialogue:Turn[]; nodes:Outcome[]; atoms:Atom[]; snapshots:Snapshot[]; summary:string; status?:string; source?:any }
export interface ChatSummary { id:string; title:string; category:string; totalPairs:number; status:string; updatedAt:string; mass:{you:number;ai:number;total:number}; share:{you:number;ai:number}; source?:any; isTrash?:boolean }
export type LoadingState = 'idle' | 'loading' | 'ready' | 'empty' | 'error';
export interface ChatView { pair:number; scroll:number; follow:boolean; selected:string|null; draft:string; zoom:number; pan:{x:number;y:number} }
export interface ChatLink { source:string; target:string; label:string; evidence?:string }
export const newView=(pair=1):ChatView=>({pair,scroll:-1,follow:true,selected:null,draft:'',zoom:1,pan:{x:0,y:0}});

export interface ImportConversation {
  convId: string;
  title: string;
  rawTitle: string;
  createdAt: string;
  updatedAt: string;
  pairs: number;
  rawTurns: number;
  totalChars: number;
  maxTurnChars: number;
  imagesDropped: number;
  imagesPerPair: number;
  language: string;
  hasCode: boolean;
  fidelityGrade: 'clean' | 'degraded' | 'unusable';
  sensitive: boolean;
  sensitiveTriggers: string[];
  isDuplicate: boolean;
  duplicateOf?: string | null;
  estimate: {
    tokens: { low: number; high: number; expected: number };
    cost: { low: number; high: number; expected: number };
  };
}

export interface ImportReport {
  importId: string;
  status: 'scanning' | 'ready' | 'failed';
  createdAt: string;
  sourceFilename: string;
  sourceFormat: string;
  totalConversations: number;
  totalPairs: number;
  totalChars: number;
  fidelity: {
    clean: number;
    degraded: number;
    unusable: number;
  };
  duplicates: number;
  sensitiveCount: number;
  estimate: {
    tokens: { low: number; high: number; expected: number };
    cost: { low: number; high: number; expected: number };
  };
  conversations: ImportConversation[];
  error?: string | null;
}
