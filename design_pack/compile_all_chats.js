const fs = require('fs');
const path = require('path');

const sampleDir = path.join(__dirname, 'sample_data');
const files = fs.readdirSync(sampleDir).filter(f => f.endsWith('.json'));

const CHAT_POSITIONS_2D = [
  { x: -180, y: -90 },
  { x: 0, y: -180 },
  { x: 180, y: -90 },
  { x: -150, y: 150 },
  { x: 150, y: 150 },
  { x: 0, y: 180 }
];

const CHAT_POSITIONS_3D = [
  { x: -46, y: 22, z: -10 },
  { x: 0, y: 36, z: 10 },
  { x: 46, y: -14, z: 18 },
  { x: -38, y: -32, z: 14 },
  { x: 36, y: -34, z: -16 },
  { x: 0, y: -38, z: 20 }
];

function compileAll() {
  const allChats = {};

  files.forEach(fileName => {
    const raw = JSON.parse(fs.readFileSync(path.join(sampleDir, fileName), 'utf8'));
    const chatId = raw.chat_id;
    const totalPairs = raw.total_pairs;
    const outcomes = raw.step_1_outcomes || [];
    const root = outcomes.find(o => !o.parent) || outcomes[0];
    const children = outcomes.filter(o => o.id !== root.id);

    // Build actions map for fast evidence quotes lookup
    const actionsMap = {};
    (raw.step_3_all_actions || []).forEach(a => {
      actionsMap[a.id] = a;
    });

    // Slots map
    const slotsMap = {};
    (raw.step_2_slots || []).forEach(s => {
      slotsMap[s.slot_id] = s;
    });

    const pairsData = {};
    let prevDormantSet = new Set();

    for (let p = 1; p <= totalPairs; p++) {
      const pairObj = (raw.step_4_pairs || []).find(x => x.pair === p);

      // Cumulative ledger rows up to pair p
      let cumRows = [];
      for (let i = 1; i <= p; i++) {
        const pObj = (raw.step_4_pairs || []).find(x => x.pair === i);
        if (pObj && pObj.ledger_rows) {
          cumRows.push(...pObj.ledger_rows);
        }
      }
      const curRows = (pairObj && pairObj.ledger_rows) ? pairObj.ledger_rows : [];

      // Calculate masses
      const outcomeStats = {};
      children.forEach(c => {
        outcomeStats[c.id] = { userScore: 0, aiScore: 0, totalScore: 0, delta: 0, exists: false };
      });

      cumRows.forEach(r => {
        if (outcomeStats[r.outcome_id]) {
          outcomeStats[r.outcome_id].exists = true;
          if (r.speaker === 'U') outcomeStats[r.outcome_id].userScore += r.score;
          else outcomeStats[r.outcome_id].aiScore += r.score;
          outcomeStats[r.outcome_id].totalScore += r.score;
        }
      });

      curRows.forEach(r => {
        if (outcomeStats[r.outcome_id]) {
          outcomeStats[r.outcome_id].delta += r.score;
        }
      });

      // Reqs & Slots up to pair p
      const allReqsUpToP = (raw.step_2_requirements || []).filter(r => r.created_at_pair <= p);
      const reqsCreatedInP = (raw.step_2_requirements || []).filter(r => r.created_at_pair === p);
      const slotsCreatedInP = (pairObj && pairObj.slots_created) ? pairObj.slots_created : [];

      // Also mark as existing if requirements or slots exist
      allReqsUpToP.forEach(r => {
        if (outcomeStats[r.outcome_id]) outcomeStats[r.outcome_id].exists = true;
      });
      slotsCreatedInP.forEach(s => {
        if (outcomeStats[s.outcome_id]) outcomeStats[s.outcome_id].exists = true;
      });

      // Terminal focus selector
      let terminalOutcomeId = null;
      const openSlotInP = slotsCreatedInP.find(s => s.status === 'open');
      if (openSlotInP) {
        terminalOutcomeId = openSlotInP.outcome_id;
      } else {
        let maxDelta = -1;
        children.forEach(c => {
          if (outcomeStats[c.id].delta > maxDelta) {
            maxDelta = outcomeStats[c.id].delta;
            terminalOutcomeId = c.id;
          }
        });
        if (maxDelta <= 0 && reqsCreatedInP.length > 0) {
          terminalOutcomeId = reqsCreatedInP[0].outcome_id;
        }
      }
      if (!terminalOutcomeId && children.length > 0) {
        terminalOutcomeId = children[0].id;
      }

      // Root Node stats
      const rootRows = cumRows.filter(r => r.outcome_id === root.id);
      const rootUserScore = rootRows.filter(r => r.speaker === 'U').reduce((s, r) => s + r.score, 0);
      const rootAiScore = rootRows.filter(r => r.speaker === 'A').reduce((s, r) => s + r.score, 0);
      const rootTotalScore = rootUserScore + rootAiScore;

      // Nodes array for Pair p
      const nodes = [];

      // Root Node
      nodes.push({
        id: root.id,
        text: root.text,
        x: 0, y: 0,
        vx: 0, vy: 0,
        x3d: 0, y3d: 0, z3d: 0,
        radius: 17,
        radius3d: 9.0,
        mass: 9999,
        userScore: rootUserScore,
        aiScore: rootAiScore,
        isRoot: true,
        pinned: true,
        chatJump: {
          turn: 'Pair 1 · Turn 0 (User Prompt)',
          action: 'U(1,1)',
          quote: actionsMap['U(1,1)'] ? actionsMap['U(1,1)'].evidence_quote : root.text
        }
      });

      // Child Nodes that exist up to Pair p
      children.forEach((c, idx) => {
        const stats = outcomeStats[c.id];
        if (!stats.exists && stats.totalScore === 0 && !allReqsUpToP.some(r => r.outcome_id === c.id)) {
          // Doesn't exist yet in this pair
          return;
        }

        const isDormant = (stats.delta === 0 && !reqsCreatedInP.some(r => r.outcome_id === c.id));
        const isTerminalActive = (c.id === terminalOutcomeId);

        const mass = Math.max(stats.totalScore, 10.0);
        const radius2d = 12.0 + 16.0 * Math.sqrt(Math.min(1.0, mass / 500.0));
        const radius3d = 6.5 + 10.5 * Math.sqrt(Math.min(1.0, mass / 500.0));

        const pos2d = CHAT_POSITIONS_2D[idx % CHAT_POSITIONS_2D.length];
        const pos3d = CHAT_POSITIONS_3D[idx % CHAT_POSITIONS_3D.length];

        // Chat jump quote
        let jumpTurn = `Pair ${p} · Deliverable Activity`;
        let jumpAction = 'A(1,1)';
        let jumpQuote = c.text;
        const oReqs = allReqsUpToP.filter(r => r.outcome_id === c.id);
        if (oReqs.length > 0) {
          const lastReq = oReqs[oReqs.length - 1];
          const actId = (lastReq.creation_action_ids && lastReq.creation_action_ids.length > 0) ? lastReq.creation_action_ids[0] : null;
          if (actId && actionsMap[actId]) {
            jumpTurn = `Pair ${lastReq.created_at_pair || p} · Requirement Decision`;
            jumpAction = actId;
            jumpQuote = actionsMap[actId].evidence_quote || actionsMap[actId].text;
          }
        }

        // Satellites for this child
        const satellites = [];
        const outcomeReqs = allReqsUpToP.filter(r => r.outcome_id === c.id);
        const satCount = outcomeReqs.length + (slotsCreatedInP.filter(s => s.outcome_id === c.id && s.status === 'open').length);

        let sIdx = 0;
        const angleStep = satCount > 1 ? (Math.PI * 0.76) / (satCount - 1) : 0;
        const startAngle = satCount > 1 ? -Math.PI * 0.88 : -Math.PI * 0.50;

        outcomeReqs.forEach(req => {
          const actId = (req.creation_action_ids && req.creation_action_ids.length > 0) ? req.creation_action_ids[0] : 'U(1,1)';
          const isUser = actId.startsWith('U');
          const isResolved = (req.related_to && req.related_to.length > 0);
          const angle = startAngle + sIdx * angleStep;
          sIdx++;

          let resolutionData = null;
          if (isResolved) {
            const origSlotId = req.related_to[0];
            const origSlot = slotsMap[origSlotId];
            resolutionData = {
              resolver: isUser ? 'user' : 'ai',
              question: origSlot ? origSlot.text : 'Original Question',
              selectedChoice: actionsMap[actId] ? actionsMap[actId].evidence_quote : req.text,
              options: [origSlot ? origSlot.text : 'Resolved option']
            };
          }

          const orbDist3d = radius3d + 4.2;
          const relX3d = orbDist3d * Math.cos(angle);
          const relY3d = Math.abs(orbDist3d * Math.sin(angle)) + 1.2;
          const relZ3d = 2.4 * Math.sin(sIdx * 1.7);

          satellites.push({
            id: req.req_id,
            relX3d: parseFloat(relX3d.toFixed(2)),
            relY3d: parseFloat(relY3d.toFixed(2)),
            relZ3d: parseFloat(relZ3d.toFixed(2)),
            type: 'requirement',
            origin: isUser ? 'user' : 'ai',
            label: isResolved ? 'Resolved Requirement' : (isUser ? 'User Requirement' : 'AI Requirement'),
            text: req.text,
            actionId: actId,
            turn: `Pair ${req.created_at_pair || p}`,
            color: isUser ? '#38bdf8' : '#fb923c',
            dist: radius2d + 16,
            angle: angle,
            radius: 3.5,
            isHollowRing: false,
            isResolvedSlot: isResolved,
            resolutionData: resolutionData
          });
        });

        // Open slots
        slotsCreatedInP.filter(s => s.outcome_id === c.id && s.status === 'open').forEach(slot => {
          const actId = (slot.creation_action_ids && slot.creation_action_ids.length > 0) ? slot.creation_action_ids[0] : 'A(1,1)';
          const angle = startAngle + sIdx * angleStep;
          sIdx++;

          const orbDist3d_slot = radius3d + 4.2;
          const relX3d_slot = orbDist3d_slot * Math.cos(angle);
          const relY3d_slot = Math.abs(orbDist3d_slot * Math.sin(angle)) + 1.2;
          const relZ3d_slot = 2.4 * Math.sin(sIdx * 1.7);

          satellites.push({
            id: slot.slot_id,
            relX3d: parseFloat(relX3d_slot.toFixed(2)),
            relY3d: parseFloat(relY3d_slot.toFixed(2)),
            relZ3d: parseFloat(relZ3d_slot.toFixed(2)),
            type: 'slot',
            origin: 'ai',
            label: 'AI Open Question',
            text: slot.text,
            actionId: actId,
            turn: `Pair ${p}`,
            choices: [slot.text],
            color: '#fb923c',
            dist: radius2d + 16,
            angle: angle,
            radius: 4.5,
            isHollowRing: true,
            isResolvedSlot: false
          });
        });

        nodes.push({
          id: c.id,
          text: c.text,
          x: pos2d.x, y: pos2d.y,
          vx: 0, vy: 0,
          x3d: pos3d.x, y3d: pos3d.y, z3d: pos3d.z,
          radius: radius2d,
          radius3d: radius3d,
          mass: mass,
          userScore: stats.userScore,
          aiScore: stats.aiScore,
          isRoot: false,
          isDormant: isDormant,
          isTerminalActive: isTerminalActive,
          chatJump: {
            turn: jumpTurn,
            action: jumpAction,
            quote: jumpQuote
          },
          satellites: satellites
        });
      });

      // Links array for Pair p
      const links = [];
      const presentNodeIds = new Set(nodes.map(n => n.id));

      nodes.forEach(n => {
        if (!n.isRoot) {
          links.push({
            source: root.id,
            target: n.id,
            type: 'parent_child',
            isDormant: n.isDormant,
            length: 190
          });
        }
      });

      // Relational links between adjacent children
      const childNodes = nodes.filter(n => !n.isRoot);
      for (let i = 0; i < childNodes.length - 1; i++) {
        links.push({
          source: childNodes[i].id,
          target: childNodes[i+1].id,
          type: 'related',
          isDormant: childNodes[i].isDormant && childNodes[i+1].isDormant,
          length: 200
        });
      }

      // Title & description for pair
      const activeCount = childNodes.filter(n => !n.isDormant).length;
      const dormantCount = childNodes.filter(n => n.isDormant).length;
      const childMassSum = childNodes.reduce((acc, n) => acc + (n.mass || 0), 0);
      const totalMass = childNodes.length > 0 && childMassSum > 0 ? childMassSum : rootTotalScore;

      // Deterministic Event tag
      let eventTag = '';
      if (p === 1) {
        eventTag = 'Genesis';
      } else {
        const born = childNodes.filter(n => {
          const priorReqs = (raw.step_2_requirements || []).filter(r => r.outcome_id === n.id && r.created_at_pair < p);
          let hadPriorRows = false;
          for (let i = 1; i < p; i++) {
            const pOld = (raw.step_4_pairs || []).find(x => x.pair === i);
            if (pOld && pOld.ledger_rows && pOld.ledger_rows.some(r => r.outcome_id === n.id)) hadPriorRows = true;
          }
          return priorReqs.length === 0 && !hadPriorRows;
        });

        const reactivated = childNodes.filter(n => !n.isDormant && prevDormantSet.has(n.id) && !born.some(b => b.id === n.id));

        if (born.length > 0) {
          eventTag = `${born[0].id} Born`;
        } else if (reactivated.length > 0) {
          eventTag = `${reactivated[0].id} Reactivated`;
        } else if (terminalOutcomeId) {
          eventTag = `${terminalOutcomeId} Surge`;
        } else {
          eventTag = `Active Progression`;
        }
      }

      prevDormantSet = new Set(childNodes.filter(n => n.isDormant).map(n => n.id));

      pairsData[p] = {
        pair: p,
        title: `Pair ${p} Complete · ${eventTag}`,
        badgeText: `Pair ${p} · Mass ${Math.round(totalMass)} (${eventTag})`,
        descText: `Root Origin anchored at (0,0,0). Cumulative ledger mass: ${Math.round(totalMass)}. Active focus on ${terminalOutcomeId || 'Root'}. ${childNodes.length} deliverables (${activeCount} active, ${dormantCount} dormant).`,
        terminalOutcomeId: terminalOutcomeId,
        nodes: nodes,
        links: links
      };
    }

    allChats[chatId] = {
      chatId: chatId,
      summary: raw.dialogue_summary || chatId,
      totalPairs: totalPairs,
      outcomesCount: outcomes.length,
      pairs: pairsData
    };
  });

  return allChats;
}

const compiled = compileAll();
const outputPath = path.join(__dirname, 'all_chats_data.js');
const fileContent = 'const ALL_CHATS_DATA = ' + JSON.stringify(compiled, null, 2) + ';\n' +
  'if (typeof window !== "undefined") { window.ALL_CHATS_DATA = ALL_CHATS_DATA; }\n' +
  'if (typeof module !== "undefined" && module.exports) { module.exports = ALL_CHATS_DATA; }\n';
fs.writeFileSync(outputPath, fileContent, 'utf8');

console.log('Successfully compiled all', Object.keys(compiled).length, 'chats to', outputPath);
console.log('File size:', fs.statSync(outputPath).size, 'bytes');
