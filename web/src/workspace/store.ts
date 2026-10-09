import { create } from 'zustand';
import seed from './data.generated.json';
import type { Chat, ChatView } from './types';
import { newView } from './types';
const chats=seed.chats as unknown as Chat[];
interface State { chats:Chat[]; tabs:string[]; active:string; views:Record<string,ChatView>; open:(id:string)=>void; close:(id:string)=>void; patch:(id:string,p:Partial<ChatView>)=>void; newChat:()=>void; appendDraft:(id:string,text:string)=>void }
export const useWorkspace=create<State>((set)=>({
 chats,tabs:[chats[0].id,chats[1].id],active:chats[0].id,views:Object.fromEntries(chats.map(c=>[c.id,newView(c.totalPairs||1)])),
 open:id=>set(s=>id==='brain'?{active:id}:{active:id,tabs:s.tabs.includes(id)?s.tabs:[...s.tabs,id]}),
 close:id=>set(s=>{const i=s.tabs.indexOf(id),tabs=s.tabs.filter(t=>t!==id);return{tabs,active:s.active===id?(tabs[Math.max(0,i-1)]||'brain'):s.active}}),
 patch:(id,p)=>set(s=>({views:{...s.views,[id]:{...(s.views[id]||newView()),...p}}})),
 newChat:()=>set(s=>{const id='draft-'+Date.now();return{chats:[{id,title:'New conversation',rootTitle:'',category:'Draft',totalPairs:0,dialogue:[],nodes:[],atoms:[],snapshots:[],summary:''},...s.chats],tabs:[...s.tabs,id],active:id,views:{...s.views,[id]:newView()}}}),
 appendDraft:(id,text)=>set(s=>({chats:s.chats.map(c=>c.id!==id?c:{...c,title:c.title==='New conversation'?text.slice(0,42):c.title,dialogue:[...c.dialogue,{pair:c.totalPairs+1,speaker:'user',text,attachments:[],ts:new Date().toISOString()}]}),views:{...s.views,[id]:{...s.views[id],draft:''}}})),
}));
