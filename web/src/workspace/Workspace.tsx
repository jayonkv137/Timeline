import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, BrainCircuit, Check, Copy, GitBranch, Menu, MessageSquare, PanelLeftClose, PanelRightClose, PanelRightOpen, Plus, Search, Settings, X, Pin, RotateCcw } from 'lucide-react';
import { useWorkspace } from './store';
import type { Chat, ChatView } from './types';
import { LocalGraph } from './LocalGraph';
import { Brain } from './Brain';
import { applyChatUpdate } from './adapter';
import { SettingsModal } from './SettingsModal';

const blankView:ChatView={pair:1,scroll:0,follow:true,selected:null,draft:'',zoom:1,pan:{x:0,y:0}};

function RichText({text}:{text:string}){
  return <div className="message-text">{text.split(/\n\n+/).map((part,i)=>{
    if(/^#{1,4} /.test(part))return <h3 key={i}>{part.replace(/^#{1,4} /,'')}</h3>;
    if(part.startsWith('```'))return <pre key={i}>{part.replace(/^```[^\n]*\n?/,'').replace(/```$/,'')}</pre>;
    return <p key={i}>{part.split(/(\*\*[^*]+\*\*|`[^`]+`)/).map((s,j)=>s.startsWith('**')?<strong key={j}>{s.slice(2,-2)}</strong>:s.startsWith('`')?<code key={j}>{s.slice(1,-1)}</code>:s)}</p>;
  })}</div>;
}

export function Workspace(){
 const {chats,tabs,active,views,open,close,patch,newChat,appendDraft,loading,error,isOffline,refresh}=useWorkspace();
 const [query,setQuery]=useState('');const [sidebar,setSidebar]=useState(true);const [rail,setRail]=useState(true);const [expanded,setExpanded]=useState(false);const [brainSelected,setBrainSelected]=useState<string|null>(null);const [brainFocus,setBrainFocus]=useState<string|null>(null);const [brainVisited,setBrainVisited]=useState(false);const [notice,setNotice]=useState('');const [copied,setCopied]=useState<string|null>(null);const [settingsOpen,setSettingsOpen]=useState(false);
 const scroll=useRef<HTMLDivElement>(null);const lockUntil=useRef(0);const scrollRaf=useRef(0);const search=useRef<HTMLInputElement>(null);const [pending,setPending]=useState<Record<string,boolean>>({});
 const isBrain=active==='brain';const chat=chats.find(c=>c.id===active);const view=views[active]||blankView;const selectedChat=chats.find(c=>c.id===brainSelected);const selectedView=brainSelected?views[brainSelected]||blankView:blankView;
 const update=(v:Partial<ChatView>)=>patch(active,v);

 function jump(pair:number,speaker?:string,keepGraph?:boolean){
   if(!chat)return;
   const bounded=Math.max(1,Math.min(chat.totalPairs||1,pair));
   if(!keepGraph)patch(chat.id,{pair:bounded});
   lockUntil.current=performance.now()+(keepGraph?1e9:1100);
   const p=scroll.current?.querySelector<HTMLElement>(`[data-pair="${bounded}"]${speaker?` [data-speaker="${speaker==='human'?'user':speaker}"]`:''}`);
   if(p&&scroll.current){
     scroll.current.scrollTo({top:p.getBoundingClientRect().top-scroll.current.getBoundingClientRect().top+scroll.current.scrollTop-24,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
   }
 }

 useLayoutEffect(()=>{
   setExpanded(false);
   lockUntil.current=performance.now()+150;
   const st=useWorkspace.getState();
   if(scroll.current){
     const v=st.views[active];
     if(v?.scroll===-1){
       const el=scroll.current.querySelector<HTMLElement>(`[data-pair="${v.pair}"]`);
       scroll.current.scrollTop=el?el.getBoundingClientRect().top-scroll.current.getBoundingClientRect().top+scroll.current.scrollTop-24:0;
     } else scroll.current.scrollTop=v?.scroll||0;
   }
   if(active==='brain')setBrainVisited(true);
 },[active]);

 useEffect(()=>{if(!notice)return;const t=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(t)},[notice]);

 useEffect(()=>{
   function key(e:KeyboardEvent){
     if(e.key==='Tab'&&expanded){
       const el=document.querySelector('.expanded-overlay');
       const list=el?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select');
       if(list?.length){
         const first=list[0],last=list[list.length-1];
         if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
         else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
       }
     }
     if(e.key==='Escape'){setExpanded(false);if(innerWidth<760){setSidebar(false);setRail(false);}}
     if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();setSidebar(true);setTimeout(()=>search.current?.focus(),0);}
     if((e.metaKey||e.ctrlKey)&&e.key==='Enter'){e.preventDefault();newChat();}
   }
   window.addEventListener('keydown',key);
   return()=>window.removeEventListener('keydown',key);
 },[newChat,expanded]);

 useEffect(()=>{
   const mq=matchMedia('(max-width: 1000px)');
   if(mq.matches)setRail(false);
   if(innerWidth<760)setSidebar(false);
 },[]);

 function onScroll(){
   cancelAnimationFrame(scrollRaf.current);
   scrollRaf.current=requestAnimationFrame(()=>{
     const el=scroll.current;
     if(!el||!chat)return;
     const v=useWorkspace.getState().views[chat.id];
     patch(chat.id,{scroll:el.scrollTop});
     if(!v?.follow||performance.now()<lockUntil.current||!chat.totalPairs)return;
     const line=el.getBoundingClientRect().top+Math.min(100,el.clientHeight*.22);
     let p=1;
     for(const pair of el.querySelectorAll<HTMLElement>('[data-pair]')){
       if(pair.getBoundingClientRect().top<=line)p=Number(pair.dataset.pair);
     }
     if(el.scrollTop+el.clientHeight>=el.scrollHeight-12)p=chat.totalPairs;
     p=Math.min(chat.totalPairs,p);
     if(v.pair!==p)patch(chat.id,{pair:p,selected:null});
   });
 }

 function activate(id:string){open(id);if(innerWidth<760)setSidebar(false);}
 function locate(id:string){setBrainSelected(id);setBrainFocus(id);setBrainVisited(true);open('brain');setRail(true);}

 function send(){
   if(!chat||!view.draft.trim()||pending[chat.id])return;
   const text=view.draft.trim();
   appendDraft(chat.id,text);
   setPending(p=>({...p,[chat.id]:true}));
   setNotice('Message saved in this preview. Connect the chat service to receive a reply.');
   window.dispatchEvent(new CustomEvent('cotrace:send-request',{detail:{chatId:chat.id,text}}));
   setTimeout(()=>{if(scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight},30);
 }

 async function copyText(text:string,id:string){
   try{
     await navigator.clipboard.writeText(text);
     setCopied(id);
     setTimeout(()=>setCopied(null),1500);
   }catch{
     setNotice('Copy is unavailable in this browser preview. Select the message text to copy it.');
   }
 }

 useEffect(()=>{if(expanded)document.querySelector<HTMLElement>('.expanded-overlay button')?.focus()},[expanded]);

 useEffect(()=>{
   function receive(e:Event){
     try{
       const c=(e as CustomEvent<Chat>).detail;
       applyChatUpdate(c);
       setPending(p=>({...p,[c.id]:false}));
     }catch{
       setNotice('Conversation update could not be read. Previous data was preserved.');
     }
   }
   window.addEventListener('cotrace:chat-updated',receive);
   return()=>window.removeEventListener('cotrace:chat-updated',receive);
 },[]);

 const filtered=chats.filter(c=>(c.title+' '+c.rootTitle+' '+c.summary).toLowerCase().includes(query.toLowerCase()));

 function graphFor(c:Chat,v:ChatView,global=false){
   return <LocalGraph chat={c} view={v} patch={p=>patch(c.id,p)} jump={(p,s,k)=>{
     if(global){
       open(c.id);
       patch(c.id,{pair:p});
       setTimeout(()=>{
         const el=document.querySelector<HTMLElement>(`[data-pair="${p}"]`);
         if(el&&scroll.current){
           lockUntil.current=performance.now()+500;
           scroll.current.scrollTop=el.offsetTop-scroll.current.offsetTop;
         }
       },80);
     } else jump(p,s,k);
   }} expanded={expanded} expand={()=>{
     if(global){
       open(c.id);
       setTimeout(()=>setExpanded(true),20);
     } else setExpanded(!expanded);
   }} locate={()=>locate(c.id)} inspect={global}/>;
 }

 return <div className={`cotrace-workspace ${sidebar?'':'sidebar-closed'} ${rail?'':'rail-closed'} ${isBrain?'brain-active':''}`}>
  <nav className="activity-rail" aria-label="Workspace tools">
    <button className="brand-symbol" aria-label="Open Brain" onClick={()=>open('brain')}><span/><span/></button>
    <button className={'icon-button '+(!isBrain?'current':'')} aria-label="Show chats" onClick={()=>setSidebar(!sidebar)}><MessageSquare size={19}/></button>
    <button className={'icon-button '+(isBrain?'current':'')} aria-label="Brain overview" onClick={()=>open('brain')}><BrainCircuit size={20}/></button>
    <button className="icon-button" aria-label="Search conversations" onClick={()=>{setSidebar(true);setTimeout(()=>search.current?.focus(),0);}}><Search size={18}/></button>
    <button className={'icon-button '+(settingsOpen?'current':'')} aria-label="Open settings" title="Settings" onClick={()=>setSettingsOpen(true)}><Settings size={18}/></button>
    <div className="rail-spacer"/>
    <span className="profile-mark">J</span>
  </nav>

  {sidebar&&<aside className="history-panel">
    <div className="history-brand"><span>COTRACE</span><button className="icon-button" aria-label="Close sidebar" onClick={()=>setSidebar(false)}><PanelLeftClose size={17}/></button></div>
    <button className="new-chat" onClick={newChat}><Plus size={16}/>New conversation<kbd>⌘ ↵</kbd></button>
    <label className="search-box"><Search size={14}/><input ref={search} aria-label="Search chats" placeholder="Search chats" value={query} onChange={e=>setQuery(e.target.value)}/><kbd>⌘ K</kbd></label>
    <div className="history-section"><span>YOUR CONVERSATIONS</span><span>{filtered.length}</span></div>
    <div className="chat-list">
      {filtered.map(c=><button key={c.id} className={'chat-list-item '+(active===c.id?'active':'')} onClick={()=>activate(c.id)}>
        <MessageSquare size={14}/>
        <span><strong>{c.title}</strong><small>{c.category} · {c.totalPairs?`${c.totalPairs} exchanges`:'Draft'}</small></span>
        {tabs.includes(c.id)&&<i className="open-dot"/>}
      </button>)}
      {filtered.length===0&&<p className="quiet-empty">{loading==='empty'?'No conversations in library yet.':loading==='loading'?'Loading conversations…':'No conversations match.'}</p>}
    </div>
    <div className="workspace-footer">
      <span className="workspace-avatar">J</span>
      <div>Jayon’s workspace<small>{isOffline?'Offline sample mode':'Connected local server'}</small></div>
      <span className={`local-dot ${isOffline?'offline':'online'}`}/>
    </div>
  </aside>}

  <div className="work-area">
   <div className="tab-strip" role="tablist" aria-label="Open workspace tabs">
     <button className="icon-button mobile-menu" aria-label="Open chat history" onClick={()=>setSidebar(!sidebar)}><Menu size={17}/></button>
     <button role="tab" aria-selected={isBrain} className={'workspace-tab brain-tab '+(isBrain?'active':'')} onClick={()=>open('brain')}><BrainCircuit size={15}/>Brain<Pin size={11}/></button>
     {tabs.map(id=>{
       const c=chats.find(c=>c.id===id);
       return c&&<div className={'chat-tab-wrap '+(active===id?'active':'')} key={id}>
         <button className="workspace-tab" role="tab" aria-selected={active===id} onClick={()=>activate(id)}>
           <MessageSquare size={13}/>
           <span>{c.title}</span>
         </button>
         <button className="close-tab" aria-label={'Close tab '+c.title} onClick={()=>close(id)}><X size={13}/></button>
       </div>;
     })}
     <button className="icon-button new-tab" aria-label="New conversation tab" onClick={newChat}><Plus size={17}/></button>
   </div>

   <header className="context-bar">
     <div className="breadcrumbs">
       {!sidebar&&<button className="icon-button" aria-label="Open sidebar" onClick={()=>setSidebar(true)}><Menu size={16}/></button>}
       <span>{isBrain?'Workspace':'Conversations'}</span>
       <span className="slash">/</span>
       <strong>{isBrain?'Brain':chat?.title}</strong>
     </div>
     <div className="context-actions">
       {!isBrain&&<button className="text-button locate-small" onClick={()=>locate(active)}><BrainCircuit size={14}/>Locate in Brain</button>}
       {error&&<button className="text-button retry-btn" onClick={refresh}><RotateCcw size={13}/>Retry connection</button>}
       <button className="icon-button" aria-label={rail?'Hide context panel':'Show context panel'} aria-pressed={rail} onClick={()=>setRail(!rail)}>{rail?<PanelRightClose size={17}/>:<PanelRightOpen size={17}/>}</button>
     </div>
   </header>

   <div className="content-grid">
    <main className="primary-pane" inert={expanded}>
     <div className="brain-pane" hidden={!isBrain}>
      <div className="brain-header"><div><span className="eyebrow">YOUR CONNECTED THINKING</span><h1>Every conversation.<br/><span>One place to return to.</span></h1></div><span className="brain-count">{chats.filter(c=>c.totalPairs).length} conversations</span></div>
      {brainVisited&&<Brain chats={chats} focus={brainFocus} onSelect={id=>{setBrainSelected(id);setBrainFocus(id);setRail(true);}}/>}
      <div className="brain-key"><span><i className="human"/>Human</span><span><i className="ai"/>AI</span></div>
     </div>

     {!isBrain&&chat&&<div className="conversation-pane">
      <div className="conversation-scroll" ref={scroll} onScroll={onScroll} onWheel={()=>{lockUntil.current=0}} onTouchStart={()=>{lockUntil.current=0}} onMouseDown={()=>{lockUntil.current=0}} onKeyDown={()=>{lockUntil.current=0}}>
       <div className="conversation-document">
        {chat.dialogue.length===0?<div className="new-conversation-empty">
          <div className="empty-logo"><GitBranch size={28}/></div>
          <span className="eyebrow">A NEW THREAD</span>
          <h1>What are you thinking about?</h1>
          <p>Your conversation and its ideas will grow together.</p>
        </div>:<>
          <div className="conversation-intro">
            <span className="eyebrow">{chat.category.toUpperCase()} / CONVERSATION</span>
            <h1>{chat.rootTitle||chat.title}</h1>
            <p>{chat.totalPairs?`${chat.totalPairs} exchanges · ${isOffline?'Imported archive sample':'Local library conversation'}`:'New conversation'}</p>
          </div>
          {Array.from(new Set(chat.dialogue.map(t=>t.pair))).map(p=><section data-pair={p} className={'exchange '+(view.pair===p?'viewed':'')} key={p}>
            <div className="exchange-marker"><span>PAIR {p.toString().padStart(2,'0')}</span><i/></div>
            {chat.dialogue.filter(t=>t.pair===p).map((t,i)=><article data-speaker={t.speaker} className={'message '+t.speaker} key={i}>
              <div className="message-heading">
                <span className={'author-avatar '+t.speaker}>{t.speaker==='user'?'J':<span className="ai-emblem">✳</span>}</span>
                <strong>{t.speaker==='user'?'You':'Assistant'}</strong>
                <button className="icon-button copy-message" aria-label={`Copy ${t.speaker} message in pair ${p}`} onClick={()=>copyText(t.text,chat.id+p+t.speaker)}>{copied===chat.id+p+t.speaker?<Check size={13}/>:<Copy size={13}/>}</button>
              </div>
              <RichText text={t.text}/>
              {t.attachments?.length>0&&<small className="attachments-note">{t.attachments.length} attachment references in original conversation</small>}
            </article>)}
          </section>)}
          {pending[chat.id]&&<div className="pending-note">Your message is saved for this session. Connect the chat backend to receive the assistant’s reply; the graph will update after analysis completes.</div>}
        </>}
       </div>
      </div>
      <div className="composer-dock">
        {chat.totalPairs>0&&view.pair<chat.totalPairs&&<button className="back-latest" onClick={()=>jump(chat.totalPairs)}>Back to latest<ArrowDown size={13}/></button>}
        <div className="composer">
          <textarea aria-label="Message" placeholder={pending[chat.id]?'Waiting for backend connection…':'Continue the conversation…'} value={view.draft} disabled={pending[chat.id]} rows={2} onChange={e=>update({draft:e.target.value})} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}}/>
          <div className="composer-bottom">
            <span><span className={`model-dot ${isOffline?'offline':'online'}`}/>{isOffline?'Chat backend in offline mode':'Live backend ready'}</span>
            <button className="send-button" aria-label="Send message" disabled={!view.draft.trim()||pending[chat.id]} onClick={send}><ArrowUp size={17}/></button>
          </div>
        </div>
        <div className="composer-hint"><span>Enter to send · Shift + Enter for a new line</span><span>{isOffline?'Offline preview':'Live preview'}</span></div>
      </div>
     </div>}

     {!isBrain&&!chat&&chats.length===0&&<div className="conversation-pane">
       <div className="conversation-document">
         <div className="new-conversation-empty">
           <div className="empty-logo"><GitBranch size={28}/></div>
           <span className="eyebrow">COTRACE LIBRARY</span>
           <h1>No conversations yet</h1>
           <p>Start a new conversation to begin co-creating with AI.</p>
           <button className="new-chat" style={{margin:'20px auto',display:'inline-flex'}} onClick={newChat}>
             <Plus size={16}/>New conversation
           </button>
         </div>
       </div>
     </div>}
    </main>

    {rail&&<aside className="context-panel" inert={expanded}>
      {isBrain?<>{selectedChat?<><div className="brain-inspector-heading">
        <span className="eyebrow">CONVERSATION</span>
        <button className="icon-button" aria-label="Clear Brain selection" onClick={()=>{setBrainSelected(null);setBrainFocus(null);}}><X size={14}/></button>
        <h2>{selectedChat.title}</h2>
        <p>{selectedChat.summary}</p>
        <button className="open-conversation" onClick={()=>open(selectedChat.id)}>Open conversation<ArrowRight size={15}/></button>
      </div>{graphFor(selectedChat,selectedView,true)}</>:<div className="brain-unselected">
        <BrainCircuit size={28}/>
        <h2>Follow an idea.</h2>
        <p>Select a point on the brain to preview its conversation and outcomes.</p>
        <div className="brain-conversation-list">
          {chats.filter(c=>c.totalPairs).map(c=><button key={c.id} onClick={()=>{setBrainSelected(c.id);setBrainFocus(c.id);}}>
            <MessageSquare size={14}/>{c.title}<ArrowRight size={12}/>
          </button>)}
        </div>
      </div>}
      <div className="cross-chat-note"><span className="eyebrow">CONNECTIONS BETWEEN CHATS</span><p>No verified cross-chat links are supplied yet. Shared topics alone are not shown as relationships.</p></div>
      </>:chat&&graphFor(chat,view)}
    </aside>}

    {expanded&&chat&&<div className="expanded-overlay" role="dialog" aria-modal="true" aria-label="Expanded conversation map">
      <div className="expanded-bar">
        <button className="text-button" onClick={()=>setExpanded(false)}><ArrowLeft size={15}/>Return to conversation</button>
        <span>Same conversation · Pair {view.pair}</span>
        <button className="icon-button" onClick={()=>setExpanded(false)} aria-label="Close expanded graph"><X size={18}/></button>
      </div>
      {graphFor(chat,view)}
    </div>}
   </div>

   <footer className="status-bar">
     <span>
       <span className={`status-dot ${isOffline?'offline':'online'}`}/>
       {isOffline?'Offline sample mode':'Local workspace'}
     </span>
     <span>
       {isBrain?'All conversations':chat?.totalPairs?`${chat.nodes.length} outcomes · ${chat.totalPairs} exchanges`:'No analyzed exchanges'}
       <span className="status-divider">|</span>
       {isBrain?'Spatial overview':view.follow?'Graph follows chat':'Graph follow paused'}
     </span>
   </footer>
  </div>

  {notice&&<div className="toast" role="status">{notice}<button className="icon-button" aria-label="Dismiss notification" onClick={()=>setNotice('')}><X size={14}/></button></div>}
  <SettingsModal isOpen={settingsOpen} onClose={()=>setSettingsOpen(false)}/>
 </div>;
}
