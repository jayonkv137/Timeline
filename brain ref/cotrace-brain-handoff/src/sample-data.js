/* Illustrative data only. Contributions are demonstration ledger units. */
window.COTRACE_SAMPLE={
 version:1,maxPair:6,
 nodes:[
 {id:'goal',title:'Build a reflection tool',description:'The parent goal anchors this illustrative conversation.',anchor:{side:1,direction:[-.42,.3,.85]},born:1,root:true,ledger:[{pair:1,human:4,ai:1},{pair:3,human:2,ai:2},{pair:6,human:1,ai:2}],source:{chatId:'demo',turnId:'turn-1'}},
 {id:'visual',title:'Visual direction',description:'Develop the neutral brain and a contributor palette.',anchor:{side:1,direction:[-.83,.2,.5]},born:1,ledger:[{pair:1,human:2,ai:1},{pair:2,human:3,ai:2},{pair:5,human:1,ai:2}],source:{chatId:'demo',turnId:'turn-2'}},
 {id:'evidence',title:'Evidence and provenance',description:'Connect each mapped contribution to its source in the conversation.',anchor:{side:1,direction:[.35,.45,.82]},born:2,ledger:[{pair:2,human:2,ai:3},{pair:4,human:2,ai:1}],source:{chatId:'demo',turnId:'turn-4'}},
 {id:'navigation',title:'Navigation behavior',description:'Explore regions, focus an outcome, and return without losing orientation.',anchor:{side:1,direction:[-.18,-.48,.85]},born:3,ledger:[{pair:3,human:1,ai:3},{pair:6,human:2,ai:1}],source:{chatId:'demo',turnId:'turn-6'}},
 {id:'model',title:'Data model',description:'Separate outcome identity, contributor history, and rendering anchors.',anchor:{side:1,direction:[.8,.04,.57]},born:3,ledger:[{pair:3,human:1,ai:3},{pair:4,human:1,ai:2}],source:{chatId:'demo',turnId:'turn-5'}},
 {id:'access',title:'Readable interactions',description:'Keep labels legible, offer keyboard selection, and respect reduced motion.',anchor:{side:1,direction:[.2,.86,.47]},born:4,ledger:[{pair:4,human:2,ai:2},{pair:6,human:1,ai:1}],source:{chatId:'demo',turnId:'turn-8'}},
 {id:'test',title:'Evaluation plan',description:'Check selection, orientation, and contributor recognition with realistic data.',anchor:{side:-1,direction:[-.7,.35,.65]},born:5,ledger:[{pair:5,human:3,ai:1}],source:{chatId:'demo',turnId:'turn-10'}},
 {id:'delivery',title:'Developer handoff',description:'Document the visual layers and integration events.',anchor:{side:-1,direction:[.35,.65,.67]},born:6,ledger:[{pair:6,human:2,ai:3}],source:{chatId:'demo',turnId:'turn-12'}}
 ],
 links:[{source:'goal',target:'visual',kind:'parent'},{source:'goal',target:'evidence',kind:'parent'},{source:'goal',target:'navigation',kind:'parent'},{source:'goal',target:'model',kind:'parent'},{source:'goal',target:'access',kind:'parent'},{source:'goal',target:'test',kind:'parent'},{source:'goal',target:'delivery',kind:'parent'},{source:'visual',target:'access',kind:'related'},{source:'evidence',target:'model',kind:'related'}],
 atoms:[{id:'a-neutral',nodeId:'visual',kind:'requirement',text:'Keep the anatomical base neutral.',origin:'human',born:2,source:{chatId:'demo',turnId:'turn-3'}},{id:'a-palette',nodeId:'visual',kind:'question',text:'Which contributor palette should we explore?',origin:'ai',born:3,resolvedAt:5,resolver:'human',resolution:'Keep several palettes available for comparison.',source:{chatId:'demo',turnId:'turn-9'}}]
};
