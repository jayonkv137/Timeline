"""Read-only projection of supplied pipeline exports + repository transcripts."""
import argparse, json, math, re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--exports',type=Path,required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[2]; chats=[]; warnings=[]
ids=['c05_research_medium','c04_writing_short','c03_coding_short','c07_research_short','c20_coding_short','c27_creative_short','c30_creative_short','c10_research_short','c16_research_short','c17_research_short']
names=['AI creativity · paper research','Human–AI interaction design','Interactive portfolio','Co-creation research','Figma migration','Jellyfish motion study','Language-learning videos','Project contribution','Co-creative panel','Datafied Society']
def pair_of(s):
 m=re.search(r'\((\d+),',s or '');return int(m[1]) if m else 1
def who(s):return 'human' if s.startswith('U') else 'ai'
for cid,title in zip(ids,names):
 d=json.loads((a.exports/(cid+'.json')).read_text());dlg=json.loads((repo/'data/corpus'/cid/'dialogue.json').read_text());N=d['total_pairs'];ops=d['step_3_operations_log'];rows=[r for pp in d['step_4_pairs'] for r in pp['ledger_rows']];outcomes=d['step_1_outcomes'];actions={x['id']:x for x in d['step_3_all_actions']}
 if max(t['pair'] for t in dlg)!=N:
  warnings.append(cid+': transcript/export pair count mismatch; omitted');continue
 root=next(o for o in outcomes if o['parent'] is None);positions=[(-100,-132),(102,-117),(-115,104),(115,109),(0,192),(-158,0),(158,5)];nodes=[]
 for o in outcomes:
  related=[r for r in rows if r['outcome_id']==o['id']];birth=min([r['pair_added'] for r in related]+[x['pair'] for x in ops if x['outcome_id']==o['id']]+[pair_of(o.get('turn_id'))]);isroot=o['id']==root['id'];i=len(nodes)-1;x,y=(0,0) if isroot else positions[i%len(positions)];nodes.append(dict(id=o['id'],title=o['text'],parent=o['parent'],related=o.get('related',[]),born=1 if isroot else birth,x=x,y=y,root=isroot,sourcePair=1 if isroot else birth,sourceSpeaker=who(next((r['action_id'] for r in related if r['pair_added']==birth),o.get('turn_id','U')))))
 atoms=[]
 for r in d['step_2_requirements']:
  origin=(r.get('creation_action_ids') or ['U(1,1)'])[0];born=r.get('created_at_pair',pair_of(origin));ancestors=[s for s in d['step_2_slots'] if s['outcome_id']==r['outcome_id'] and s['slot_id'] in r.get('related_to',[])];slot=ancestors[0] if ancestors else None;origin2=(slot.get('creation_action_ids') or ['A(1,1)'])[0] if slot else origin;deleted=min([x['pair'] for x in ops if x['outcome_id']==r['outcome_id'] and x['target_id']==r['req_id'] and x['target_type']=='requirement' and x['op']=='delete'] or [N+1]);atoms.append(dict(id=r['outcome_id']+':'+r['req_id'],nodeId=r['outcome_id'],kind='resolved' if slot else 'requirement',text=r['text'],question=slot['text'] if slot else None,origin=who(origin2),resolver=who(origin),born=born,end=deleted,sourcePair=pair_of(origin),sourceSpeaker=who(origin),quote=actions.get(origin,{}).get('evidence_quote',''),choices=slot.get('choices',[]) if slot else []))
 for s in d['step_2_slots']:
  aid=(s.get('creation_action_ids') or ['A(1,1)'])[0];end=min([x['pair'] for x in ops if x['outcome_id']==s['outcome_id'] and x['target_id']==s['slot_id'] and x['target_type']=='slot' and x['op'] in ['resolve','abandon']] or [N+1]);atoms.append(dict(id=s['outcome_id']+':'+s['slot_id'],nodeId=s['outcome_id'],kind='question',text=s['text'],question=None,origin=who(aid),resolver=None,born=pair_of(aid),end=end,sourcePair=pair_of(aid),sourceSpeaker=who(aid),quote=actions.get(aid,{}).get('evidence_quote',''),choices=s.get('choices',[])))
 snapshots=[]
 for pp in d['step_4_pairs']:
  P=pp['pair'];mass={n['id']:{'human':0,'ai':0,'delta':0} for n in nodes}
  for r in rows:
   if r['pair_added']<=P:
    m=mass[r['outcome_id']];m['human' if r['speaker']=='U' else 'ai']+=r['score'];m['delta']+=r['score'] if r['pair_added']==P else 0
  active=[r for r in pp['ledger_rows'] if r['speaker']=='A'];active.sort(key=lambda r:int(re.search(r',(\d+)\)',r['action_id']).group(1)) if re.search(r',(\d+)\)',r['action_id']) else 0);terminal=active[-1]['outcome_id'] if active else root['id'];snapshots.append(dict(pair=P,mass=mass,terminal=terminal))
 chats.append(dict(id=cid,title=title,rootTitle=root['text'],category=cid.split('_')[1].title(),totalPairs=N,dialogue=dlg,nodes=nodes,atoms=atoms,snapshots=snapshots,summary=d['dialogue_summary']))
output=repo/'web/src/workspace/data.generated.json';output.write_text(json.dumps(dict(chats=chats,links=[],warnings=warnings),ensure_ascii=False,separators=(',',':')))
print('Compiled',len(chats),'chats;',sum(c['totalPairs'] for c in chats),'pairs;',output.stat().st_size,'bytes');print('Warnings:',warnings)
# Ground-truth regression from supplied graph specification.
c=chats[0]
assert [sum(v['human']+v['ai'] for k,v in p['mass'].items() if k!='outcome 1') for p in c['snapshots']]==[62,237,412,625,919,1049,1137]
print('Seven-pair mass regression passed.')
