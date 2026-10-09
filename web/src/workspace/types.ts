export type Contributor = 'human' | 'ai';
export interface Turn { pair: number; speaker: 'user' | 'ai'; text: string; attachments: string[]; ts: string }
export interface Outcome { id:string; title:string; parent:string|null; related:string[]; born:number; x:number; y:number; root:boolean; sourcePair:number; sourceSpeaker:Contributor }
export interface Atom { id:string; nodeId:string; kind:'requirement'|'question'|'resolved'; text:string; question:string|null; origin:Contributor; resolver:Contributor|null; born:number; end:number; sourcePair:number; sourceSpeaker:Contributor; quote:string; choices:string[] }
export interface Mass { human:number; ai:number; delta:number }
export interface Snapshot { pair:number; mass:Record<string,Mass>; terminal:string }
export interface Chat { id:string; title:string; rootTitle:string; category:string; totalPairs:number; dialogue:Turn[]; nodes:Outcome[]; atoms:Atom[]; snapshots:Snapshot[]; summary:string }
export interface ChatView { pair:number; scroll:number; follow:boolean; selected:string|null; draft:string; zoom:number; pan:{x:number;y:number} }
export interface ChatLink { source:string; target:string; label:string; evidence?:string }
export const newView=(pair=1):ChatView=>({pair,scroll:-1,follow:true,selected:null,draft:'',zoom:1,pan:{x:0,y:0}});
