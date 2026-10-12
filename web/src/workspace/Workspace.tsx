import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, BarChart3, BrainCircuit, Check, Copy, GitBranch, Menu, MessageSquare, PanelLeftClose, PanelRightClose, PanelRightOpen, Plus, Search, Settings, Upload, X, Pin, RotateCcw, Sparkles } from 'lucide-react';
import { useWorkspace } from './store';
import type { Chat, ChatView } from './types';
import { LocalGraph } from './LocalGraph';
import { Brain } from './Brain';
import { applyChatUpdate } from './adapter';
import { SettingsModal } from './SettingsModal';
import { UsageModal } from './UsageModal';
import { ImportModal } from './ImportModal';
import { ProcessingPill } from './ProcessingPill';
import { fetchJobs, cancelJob, mapNextJob, pauseAllJobs, resumeAllJobs, processImportBatch, createChat, sendChatMessageStream, type QueueStatus } from './api';
import { useEvidence, EvidenceStrip } from './useEvidence';

const blankView:ChatView={pair:1,scroll:0,follow:true,selected:null,draft:'',zoom:1,pan:{x:0,y:0}};

function RichText({text}:{text:string}){
  return <div className="message-text">{text.split(/\n\n+/).map((part,i)=>{
    if(/^#{1,4} /.test(part))return <h3 key={i}>{part.replace(/^#{1,4} /,'')}</h3>;
    if(part.startsWith('```'))return <pre key={i}>{part.replace(/^```[^\n]*\n?/,'').replace(/```$/,'')}</pre>;
    return <p key={i}>{part.split(/(\*\*[^*]+\*\*|`[^`]+`)/).map((s,j)=>s.startsWith('**')?<strong key={j}>{s.slice(2,-2)}</strong>:s.startsWith('`')?<code key={j}>{s.slice(1,-1)}</code>:s)}</p>;
  })}</div>;
}

export function Workspace(){
 const {chats,tabs,active,views,open,close,patch,newChat,appendDraft,mapChat,loading,error,isOffline,refresh,loadBundle}=useWorkspace();
 const [query,setQuery]=useState('');const [sidebar,setSidebar]=useState(true);const [rail,setRail]=useState(true);const [expanded,setExpanded]=useState(false);const [brainSelected,setBrainSelected]=useState<string|null>(null);const [brainFocus,setBrainFocus]=useState<string|null>(null);const [brainVisited,setBrainVisited]=useState(false);const [notice,setNotice]=useState('');const [copied,setCopied]=useState<string|null>(null);const [settingsOpen,setSettingsOpen]=useState(false);const [usageOpen,setUsageOpen]=useState(false);const [importOpen,setImportOpen]=useState(false);
 const scroll=useRef<HTMLDivElement>(null);const lockUntil=useRef(0);const scrollRaf=useRef(0);const search=useRef<HTMLInputElement>(null);const [pending,setPending]=useState<Record<string,boolean>>({});
 const [streaming,setStreaming]=useState<{chatId:string;text:string;pair:number}|null>(null);
 const [queueStatus,setQueueStatus]=useState<QueueStatus|null>(null);
 const [initiatingMap,setInitiatingMap]=useState<string|null>(null);

 const handleTriggerMap=async(targetId:string)=>{
   if(initiatingMap)return;
   setInitiatingMap(targetId);
   try{
     await mapChat(targetId);
     setNotice('Tracing decisions into spatial timeline…');
   }catch(err:any){
     setNotice(err?.message||'Could not initiate mapping');
     setInitiatingMap(null);
   }
 };

 useEffect(()=>{
   if(isOffline)return;
   fetchJobs().then(setQueueStatus).catch(()=>{});
   const onQueueEvent=()=>{fetchJobs().then(setQueueStatus).catch(()=>{});};
   const onJobFinished=(e:any)=>{
     if(e.detail?.chatId&&initiatingMap===e.detail.chatId){
       setInitiatingMap(null);
     }
   };
   window.addEventListener('cotrace:queue_changed',onQueueEvent);
   window.addEventListener('cotrace:job_progress',onQueueEvent);
   window.addEventListener('cotrace:chat_ready',onQueueEvent);
   window.addEventListener('cotrace:job_error',onQueueEvent);
   window.addEventListener('cotrace:pair_ready',onJobFinished);
   window.addEventListener('cotrace:chat_ready',onJobFinished);
   return ()=>{
     window.removeEventListener('cotrace:queue_changed',onQueueEvent);
     window.removeEventListener('cotrace:job_progress',onQueueEvent);
     window.removeEventListener('cotrace:chat_ready',onQueueEvent);
     window.removeEventListener('cotrace:job_error',onQueueEvent);
     window.removeEventListener('cotrace:pair_ready',onJobFinished);
     window.removeEventListener('cotrace:chat_ready',onJobFinished);
   };
 },[isOffline,initiatingMap]);

 async function handleProcessBatch(importId:string,convIds:string[]){
   try{
     const res=await processImportBatch(importId,convIds);
     setNotice(`Processing started for ${res.enqueuedCount} ${res.enqueuedCount===1?'chat':'chats'}.`);
     await refresh();
     const q=await fetchJobs();
     setQueueStatus(q);
     if(res.jobs&&res.jobs[0]){activate(res.jobs[0].chatId);}
   }catch(err:any){
     setNotice(`Could not start batch: ${err.message||err}`);
   }
 }
 const isBrain=active==='brain';const chat=chats.find(c=>c.id===active);const view=views[active]||blankView;const selectedChat=chats.find(c=>c.id===brainSelected);const selectedView=brainSelected?views[brainSelected]||blankView:blankView;
 const update=(v:Partial<ChatView>)=>patch(active,v);
 const ev=useEvidence({chat,viewPair:view.pair,scroll,lockUntil}); // EVIDENCE_SPEC: click a node → exact words in the chat

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
     if((e.metaKey||e.ctrlKey)&&e.key==='m'){
       e.preventDefault();
       if(chat&&(!chat.nodes||chat.nodes.length===0)&&!chat.isMapped&&chat.totalPairs>0){
         handleTriggerMap(chat.id);
       }
     }
   }
   window.addEventListener('keydown',key);
   return()=>window.removeEventListener('keydown',key);
 },[newChat,expanded,chat,initiatingMap]);

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

 async function send(){
   if(!chat||!view.draft.trim()||pending[chat.id])return;
   const text=view.draft.trim();
   update({draft:''});

   let targetChatId = chat.id;

   // If active conversation is a draft, create real chat on server
   if (targetChatId.startsWith('draft-')) {
     try {
       const created = await createChat({ title: text.slice(0, 42) });
       targetChatId = created.id;
       useWorkspace.setState(s => ({
         chats: s.chats.map(c => c.id === chat.id ? { ...created, title: text.slice(0, 42) } : c),
         tabs: s.tabs.map(t => t === chat.id ? created.id : t),
         active: created.id,
         views: { ...s.views, [created.id]: s.views[chat.id] || blankView },
       }));
     } catch (err: any) {
       setNotice(`Could not create conversation: ${err.message || err}`);
       return;
     }
   }

   const currentTotal = chat.totalPairs || (chat.dialogue.length > 0 ? Math.max(...chat.dialogue.map(t => t.pair)) : 0);
   const nextPair = currentTotal + 1;

   appendDraft(targetChatId, text);
   setPending(p => ({ ...p, [targetChatId]: true }));
   setStreaming({ chatId: targetChatId, text: '', pair: nextPair });

   setTimeout(() => { if (scroll.current) scroll.current.scrollTop = scroll.current.scrollHeight; }, 30);

   if (isOffline) {
     setNotice('Running in offline mode. Live Gemini generation requires local COTRACE server.');
     setPending(p => ({ ...p, [targetChatId]: false }));
     setStreaming(null);
     return;
   }

   sendChatMessageStream(targetChatId, text, {
     onToken: (chunk) => {
       setStreaming(s => s && s.chatId === targetChatId ? { ...s, text: s.text + chunk } : s);
       if (scroll.current) {
         scroll.current.scrollTop = scroll.current.scrollHeight;
       }
     },
     onDone: () => {
       setStreaming(null);
       setPending(p => ({ ...p, [targetChatId]: false }));
       loadBundle(targetChatId);
       setTimeout(() => { if (scroll.current) scroll.current.scrollTop = scroll.current.scrollHeight; }, 60);
     },
     onError: (errMsg) => {
       setStreaming(null);
       setPending(p => ({ ...p, [targetChatId]: false }));
       setNotice(`Chat error: ${errMsg}`);
     },
   });
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

 useEffect(()=>{
   function onBudgetStop(e:Event){
     const detail=(e as CustomEvent).detail;
     const spent=detail?.spent!=null?`$${Number(detail.spent).toFixed(2)}`:'';
     const cap=detail?.cap!=null?`$${Number(detail.cap).toFixed(2)}`:'';
     setNotice(`Monthly budget cap reached (${spent} of ${cap}). Running job halted.`);
     setUsageOpen(true);
   }
   window.addEventListener('cotrace:budget_stop',onBudgetStop);
   return()=>window.removeEventListener('cotrace:budget_stop',onBudgetStop);
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
   }} locate={()=>locate(c.id)} inspect={global} activeAtom={ev.inspect?.chatId===c.id?ev.inspect.atomId:null} onAtom={id=>{
     const a=c.atoms.find(x=>x.id===id);
     if(global){open(c.id);setTimeout(()=>ev.open(c.id,id,a,v.pair),150);}
     else if(expanded){setExpanded(false);setTimeout(()=>ev.open(c.id,id,a,v.pair),40);}
     else ev.open(c.id,id,a,v.pair);
   }}/>;
 }

 return <div className={`cotrace-workspace ${sidebar?'':'sidebar-closed'} ${rail?'':'rail-closed'} ${isBrain?'brain-active':''}`}>
  <nav className="activity-rail" aria-label="Workspace tools">
    <button className="brand-symbol" aria-label="Open Brain" onClick={()=>open('brain')}><span/><span/></button>
    <button className={'icon-button '+(!isBrain?'current':'')} aria-label="Show chats" onClick={()=>setSidebar(!sidebar)}><MessageSquare size={19}/></button>
    <button className={'icon-button '+(isBrain?'current':'')} aria-label="Brain overview" onClick={()=>open('brain')}><BrainCircuit size={20}/></button>
    <button className="icon-button" aria-label="Search conversations" onClick={()=>{setSidebar(true);setTimeout(()=>search.current?.focus(),0);}}><Search size={18}/></button>
    <button className={'icon-button '+(importOpen?'current':'')} aria-label="Import history" title="Import history" onClick={()=>setImportOpen(true)}><Upload size={18}/></button>
    <button className={'icon-button '+(usageOpen?'current':'')} aria-label="View usage and budget" title="Usage & Budget" onClick={()=>setUsageOpen(true)}><BarChart3 size={18}/></button>
    <button className={'icon-button '+(settingsOpen?'current':'')} aria-label="Open settings" title="Settings" onClick={()=>setSettingsOpen(true)}><Settings size={18}/></button>
    <div className="rail-spacer"/>
    <span className="profile-mark">J</span>
  </nav>

  {sidebar&&<aside className="history-panel">
    <div className="history-brand"><span>COTRACE</span><button className="icon-button" aria-label="Close sidebar" onClick={()=>setSidebar(false)}><PanelLeftClose size={17}/></button></div>
    <div style={{ display: 'flex', gap: '6px' }}>
      <button className="new-chat" style={{ flex: 1 }} onClick={newChat}><Plus size={16}/>New conversation<kbd>⌘ ↵</kbd></button>
      <button className="new-chat" style={{ flex: 'initial', padding: '0 10px', background: 'transparent' }} aria-label="Import history" title="Import history" onClick={()=>setImportOpen(true)}><Upload size={15}/></button>
    </div>
    <label className="search-box"><Search size={14}/><input ref={search} aria-label="Search chats" placeholder="Search chats" value={query} onChange={e=>setQuery(e.target.value)}/><kbd>⌘ K</kbd></label>
    <div className="history-section"><span>YOUR CONVERSATIONS</span><span>{filtered.length}</span></div>
    <div className="chat-list">
      {filtered.map(c => {
        const job = queueStatus?.jobs?.find(j => j.chatId === c.id);
        const isRunning = job?.status === 'running';
        const isQueued = job?.status === 'queued';
        const isFailed = job?.status === 'failed';
        const isCanceled = job?.status === 'canceled';

        const isNeedsReview = c.status === 'needs_review' || (c.flaggedPairs && c.flaggedPairs.length > 0);

        let itemClass = 'chat-list-item ' + (active === c.id ? 'active' : '');
        if (isRunning) itemClass += ' chat-mapping';
        else if (isQueued) itemClass += ' chat-waiting';
        else if (isFailed) itemClass += ' chat-failed';
        else if (isNeedsReview) itemClass += ' chat-needs-review';

        const progressPct = isRunning
          ? Math.round(((job.completedPairs || 0) / (job.totalPairs || 1)) * 100)
          : 0;

        return (
          <button key={c.id} className={itemClass} onClick={() => activate(c.id)}>
            <MessageSquare size={14} />
            <span>
              <strong>{c.title}</strong>
              <small>
                {isRunning
                  ? `Mapping · ${job.completedPairs || 0} of ${job.totalPairs}`
                  : isQueued
                  ? `Waiting · ${job.totalPairs || c.totalPairs} exchanges`
                  : isFailed
                  ? 'Couldn’t map · Retry'
                  : isCanceled
                  ? `Mapped ${job.completedPairs} of ${job.totalPairs} · Continue`
                  : isNeedsReview
                  ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span className="needs-review-badge">!</span>
                      <span>
                        {(c.flaggedPairs?.length || 1) === 1
                          ? '1 exchange needs review'
                          : `${c.flaggedPairs?.length} exchanges need review`}
                      </span>
                    </span>
                  )
                  : `${c.category} · ${c.totalPairs ? `${c.totalPairs} exchanges` : 'Draft'}`}
              </small>
            </span>
            {isRunning && (
              <div className="chat-mapping-line">
                <div className="chat-mapping-fill" style={{ width: `${progressPct}%` }} />
              </div>
            )}
            {tabs.includes(c.id) && <i className="open-dot" />}
          </button>
        );
      })}
      {filtered.length === 0 && (
        <p className="quiet-empty">
          {loading === 'empty'
            ? 'No conversations in library yet.'
            : loading === 'loading'
            ? 'Loading conversations…'
            : 'No conversations match.'}
        </p>
      )}
    </div>
    <ProcessingPill
      queueStatus={queueStatus}
      onMapNext={async (jobId) => { await mapNextJob(jobId); const q = await fetchJobs(); setQueueStatus(q); }}
      onCancel={async (jobId) => { await cancelJob(jobId); const q = await fetchJobs(); setQueueStatus(q); }}
      onPauseAll={async () => { await pauseAllJobs(); const q = await fetchJobs(); setQueueStatus(q); }}
      onResumeAll={async () => { await resumeAllJobs(); const q = await fetchJobs(); setQueueStatus(q); }}
      onOpenSettings={() => setSettingsOpen(true)}
      onOpenUsage={() => setUsageOpen(true)}
    />
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
      <div className={`conversation-scroll ${initiatingMap===chat.id?'is-scanning':''}`} ref={scroll} onScroll={onScroll} onWheel={()=>{if(!ev.inspect)lockUntil.current=0}} onTouchStart={()=>{if(!ev.inspect)lockUntil.current=0}} onMouseDown={()=>{if(!ev.inspect)lockUntil.current=0}} onKeyDown={()=>{if(!ev.inspect)lockUntil.current=0}}>
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
            {streaming&&streaming.chatId===chat.id&&streaming.pair===p&&<article data-speaker="ai" className="message ai streaming">
              <div className="message-heading">
                <span className="author-avatar ai"><span className="ai-emblem">✳</span></span>
                <strong>Assistant</strong>
                <span className="streaming-status">{streaming.text?'Replying…':'Thinking…'}</span>
              </div>
              <div className="message-text">
                {streaming.text ? (
                  <>
                    <RichText text={streaming.text} />
                    <span className="streaming-cursor" />
                  </>
                ) : (
                  <div className="typing-indicator"><span /><span /><span /></div>
                )}
              </div>
            </article>}
          </section>)}
          {streaming&&streaming.chatId===chat.id&&!chat.dialogue.some(t=>t.pair===streaming.pair)&&<section data-pair={streaming.pair} className="exchange viewed" key="streaming-pair">
            <div className="exchange-marker"><span>PAIR {streaming.pair.toString().padStart(2,'0')}</span><i/></div>
            <article data-speaker="ai" className="message ai streaming">
              <div className="message-heading">
                <span className="author-avatar ai"><span className="ai-emblem">✳</span></span>
                <strong>Assistant</strong>
                <span className="streaming-status">{streaming.text?'Replying…':'Thinking…'}</span>
              </div>
              <div className="message-text">
                {streaming.text ? (
                  <>
                    <RichText text={streaming.text} />
                    <span className="streaming-cursor" />
                  </>
                ) : (
                  <div className="typing-indicator"><span /><span /><span /></div>
                )}
              </div>
            </article>
          </section>}
        </>}
       </div>
      </div>
      <div className="composer-dock">
        {ev.inspect&&ev.atom&&<EvidenceStrip atom={ev.atom} evidence={ev.evidence} index={ev.inspect.index} resolution={ev.resolution} onStep={ev.step} onBack={ev.back} onClose={ev.close}/>}
        {!ev.inspect&&chat.totalPairs>0&&view.pair<chat.totalPairs&&<button className="back-latest" onClick={()=>jump(chat.totalPairs)}>Back to latest<ArrowDown size={13}/></button>}
        <div className="composer">
          <textarea aria-label="Message" placeholder={pending[chat.id]?'Generating response…':'Continue the conversation…'} value={view.draft} disabled={pending[chat.id]} rows={2} onChange={e=>update({draft:e.target.value})} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}}/>
          <div className="composer-bottom">
            <span><span className={`model-dot ${isOffline?'offline':'online'}`}/>{isOffline?'Chat backend in offline mode':'Live Gemini model ready'}</span>
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
      </>:chat&&<div className="unmapped-stage-container">
        {graphFor(chat,view)}
        {(!chat.isMapped&&(!chat.nodes||chat.nodes.length===0))&&(
          <div className={`mapping-stage-veil ${initiatingMap===chat.id?'is-initiating':''}`}>
            <div className="veil-ambient-drift" aria-hidden="true">
              <svg className="drift-constellation" viewBox="0 0 300 300">
                <circle cx="100" cy="120" r="14" className="drift-node drift-human"/>
                <circle cx="210" cy="180" r="16" className="drift-node drift-ai"/>
                <line x1="100" y1="120" x2="210" y2="180" className="drift-tether"/>
              </svg>
            </div>

            <div className="mapping-card minimal">
              <button 
                className="trace-decisions-btn"
                onClick={()=>handleTriggerMap(chat.id)}
                disabled={initiatingMap===chat.id||chat.totalPairs===0}
                aria-label="Map this conversation"
              >
                <Sparkles size={14} style={{color:'var(--color-party-ai-solid)'}}/>
                <span className="btn-label">
                  {initiatingMap===chat.id?'Mapping conversation…':'Map this conversation'}
                </span>
                <kbd className="btn-shortcut">⌘M</kbd>
              </button>
              {chat.totalPairs===0&&<span className="mapping-hint">Send a message to start mapping</span>}
            </div>
          </div>
        )}
      </div>}
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
  <UsageModal isOpen={usageOpen} onClose={()=>setUsageOpen(false)}/>
  <ImportModal isOpen={importOpen} onClose={()=>setImportOpen(false)} onProcessBatch={handleProcessBatch}/>
 </div>;
}
