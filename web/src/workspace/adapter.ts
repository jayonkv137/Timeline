import type { Chat } from './types';
import { newView } from './types';
import { useWorkspace } from './store';
/** Boundary for an already-computed backend projection. No scoring happens here. */
export function applyChatUpdate(chat:Chat){
 if(!chat||typeof chat.id!=='string'||!Number.isInteger(chat.totalPairs)||chat.totalPairs<0||!Array.isArray(chat.dialogue)||!Array.isArray(chat.nodes)||!Array.isArray(chat.atoms)||!Array.isArray(chat.snapshots)||chat.snapshots.length!==chat.totalPairs)throw new Error('Invalid normalized conversation');
 useWorkspace.setState(s=>{
  const previous=s.chats.find(c=>c.id===chat.id);const v=s.views[chat.id]||newView(chat.totalPairs||1);
  const followLatest=v.follow&&v.pair===(previous?.totalPairs||1);
  return{chats:previous?s.chats.map(c=>c.id===chat.id?chat:c):[...s.chats,chat],views:{...s.views,[chat.id]:{...v,pair:followLatest?Math.max(1,chat.totalPairs):Math.min(v.pair,Math.max(1,chat.totalPairs))}}};
 });
}
