"""scripts/evidence_audit.py — Can every engine action quote be anchored to an exact place in its message? (EVIDENCE_SPEC §4, zero LLM calls)"""
import json,re,glob,os,collections,unicodedata,sys
def norm_map(s):
    """Normalise for matching and keep a map from normalised index -> original index."""
    out=[];idx=[];prev_space=False
    rep={'’':"'",'‘':"'",'“':'"','”':'"','—':'-','–':'-',' ':' '}
    for i,ch in enumerate(s):
        ch=rep.get(ch,ch)
        if ch in '*_`#>':continue
        if ch.isspace():
            if prev_space or not out:continue
            ch=' ';prev_space=True
        else:prev_space=False
        out.append(ch.lower());idx.append(i)
    return ''.join(out),idx
def frags(q):return [f.strip(' .,;:"\'') for f in re.split(r'\.\.\.|…',q) if len(f.strip(' .,;:"\''))>=4]
R=collections.Counter();by_role=collections.Counter();misses=[];per_chat={}
for d in sorted(glob.glob('data/chats/c*')):
    st=os.path.join(d,'state.json')
    if not os.path.exists(st):continue
    s=json.load(open(st));dia=json.load(open(os.path.join(d,'dialogue.json')));turns=dia['turns'] if isinstance(dia,dict) else dia
    txt={(t['pair'],t['speaker']):t['text'] for t in turns};c=collections.Counter()
    for a in s['actions']:
        m=re.match(r'([UA])\((\d+),(\d+)\)',a['id']);t=txt.get((int(m[2]),'user' if m[1]=='U' else 'ai'),'');q=(a.get('evidence_quote') or '').strip()
        R['actions']+=1;c['actions']+=1
        if not q:R['no quote']+=1;continue
        nt,_=norm_map(t);nq,_=norm_map(q)
        if q in t:k='exact (unique)' if t.count(q)==1 else 'exact (repeated phrase)'
        elif nq in nt:k='exact after formatting normalisation' if nt.count(nq)==1 else 'normalised (repeated phrase)'
        else:
            fs=frags(q);ok=[f for f in fs if norm_map(f)[0] in nt]
            k='multi-part (all fragments verbatim)' if fs and len(ok)==len(fs) else ('partial fragments' if ok else 'not found in its message')
            if k!='multi-part (all fragments verbatim)':
                other=[kk for kk,v in txt.items() if kk!=(int(m[2]),'user' if m[1]=='U' else 'ai') and nq[:40] in norm_map(v)[0]]
                misses.append((os.path.basename(d),a['id'],k,other[:1],q[:60]))
        R[k]+=1;c[k]+=1
    per_chat[os.path.basename(d)]=dict(c)
# which actions do requirements/questions actually point to?
roles=collections.Counter()
for d in sorted(glob.glob('data/chats/c*')):
    st=os.path.join(d,'state.json')
    if not os.path.exists(st):continue
    s=json.load(open(st))
    for r in s['requirements']:
        roles['req creation links']+=len(r['creation_action_ids']);roles['req revise links']+=len(r['revise_action_ids']);roles['req contributing links']+=len(r['contributing_action_ids']);roles['req implementation links']+=len(r['implementation_action_ids']);roles['requirements']+=1
        roles['req with >1 creation action']+=len(r['creation_action_ids'])>1
    for sl in s['slots']:
        roles['questions']+=1;roles['question resolved_into set']+=bool(sl.get('resolved_into'));roles['q contributing links']+=len(sl['contributing_action_ids'])
print('chats:',len(per_chat));print(json.dumps(dict(R),indent=1));print(json.dumps(dict(roles),indent=1))
print('misses:');[print(' ',m) for m in misses]
