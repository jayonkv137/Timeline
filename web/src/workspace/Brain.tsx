import { useEffect, useMemo, useRef } from 'react';
import frame from './brain-frame.html?raw';
import engine from './brain-engine.js?raw';
import tokensCss from '../design-system/tokens/tokens.css?raw';
import { tokens } from '../design-system/tokens/tokens';
// The brain runs in its own document: hand it the design-system stylesheet and the colours its engine needs.
const B=tokens.component.brain;
const brainTokens={stage:B.stage,dust:B.dust,fiber:B.fiber,link:B.link,linkRelated:B['link-related'],dendrite:B.dendrite,human:B.human,ai:B.ai,balanced:tokens.semantic.color.text.strong,
 cortex:Object.fromEntries(Object.entries(B.cortex).filter(([k])=>!k.startsWith('$'))),
 // ?brain=legacy shows the previous photon spheres for comparison
 legacyLight:typeof location!=='undefined'&&new URLSearchParams(location.search).get('brain')==='legacy'};
const source=frame.replace('<head>',`<head><style>${tokensCss}</style>`).split('/* COTRACE_ENGINE */').join(`window.COTRACE_TOKENS=${JSON.stringify(brainTokens)};`+engine);
import type { Chat } from './types';
// Placement: closeness means relation. Until cross-chat evidence exists (roadmap B1), chats gather in
// topic lobes from the corpus task type. This is a provisional stand-in and is labelled as such in docs.
const LOBES:Record<string,{side:number;direction:number[]}>={
 Research:{side:1,direction:[-.68,.38,.72]}, Coding:{side:1,direction:[.56,-.35,.75]},
 Creative:{side:-1,direction:[.48,.48,.72]}, Writing:{side:-1,direction:[-.62,-.42,.69]},
 Planning:{side:1,direction:[0,.82,.57]}, Learning:{side:-1,direction:[.05,-.72,.69]},
};
const anchors=new Map<string,{side:number;direction:number[]}>();const lobeCount=new Map<string,number>();
function anchor(id:string,category:string){if(!anchors.has(id)){const lobe=LOBES[category]||{side:anchors.size%2?1:-1,direction:[0,0,1]};const i=lobeCount.get(category)||0;lobeCount.set(category,i+1);
 const a=i*2.39996323,r=i?.2+.09*Math.sqrt(i):0,[x,y,z]=lobe.direction,d=[x+r*Math.cos(a),y+r*Math.sin(a),z];const len=Math.hypot(...d);anchors.set(id,{side:lobe.side,direction:d.map(c=>c/len)})}return anchors.get(id)!}
export function Brain({onSelect,focus,chats}:{onSelect:(id:string|null)=>void;focus:string|null;chats:Chat[]}){
 const ref=useRef<HTMLIFrameElement>(null);const callback=useRef(onSelect);callback.current=onSelect;const latest=useRef(focus);latest.current=focus;const ready=useRef(false);
 const graph=useMemo(()=>({version:1,maxPair:1,nodes:chats.filter(c=>c.totalPairs).map(c=>{const final=c.snapshots.at(-1)?.mass||{},mass=Object.values(final);return{id:c.id,title:c.title,born:1,anchor:anchor(c.id,c.category),since:c.dialogue[0]?.ts||'',
  // final-state outcome map, drawn as the territory's circuit
  outcomes:c.nodes.map(o=>({id:o.id,title:o.title,parent:o.parent,related:o.related,x:o.x,y:o.y,root:o.root,human:final[o.id]?.human||0,ai:final[o.id]?.ai||0})),ledger:[{pair:1,human:mass.reduce((s,m)=>s+m.human,0),ai:mass.reduce((s,m)=>s+m.ai,0)}]}}),links:[],atoms:[]}),[chats]);const data=useRef(graph);data.current=graph;
 function send(){ref.current?.contentWindow?.postMessage({type:'cotrace-brain-data',graph:data.current},'*');if(latest.current)ref.current?.contentWindow?.postMessage({type:'cotrace-brain-focus',id:latest.current},'*')}
 useEffect(()=>{function receive(e:MessageEvent){if(e.source!==ref.current?.contentWindow)return;if(e.data?.type==='cotrace-brain-select')callback.current(e.data.id);if(e.data?.type==='cotrace-brain-ready'){ready.current=true;send()}}
 window.addEventListener('message',receive);return()=>window.removeEventListener('message',receive)},[]);
 useEffect(()=>{if(ready.current)send()},[graph]);
 useEffect(()=>{ref.current?.contentWindow?.postMessage({type:focus?'cotrace-brain-focus':'cotrace-brain-clear',id:focus},'*')},[focus]);
 return <iframe ref={ref} className="brain-frame" title="Interactive three-dimensional brain of your conversations" srcDoc={source}/>;
}
