import json
import os

def build():
    chats_to_bundle = ['c05_research_medium', 'c04_writing_short', 'c16_research_short']
    bundled_data = {}

    for c in chats_to_bundle:
        path = f'design_pack/sample_data/{c}.json'
        if os.path.exists(path):
            with open(path) as f:
                bundled_data[c] = json.load(f)

    json_str = json.dumps(bundled_data)

    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace 3D Graph Playground</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #0d0d12;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
    }
    #canvas-container {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 1;
    }
    #labels-layer {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      pointer-events: none;
      z-index: 2;
    }
    .node-label {
      position: absolute;
      transform: translate(-50%, -100%);
      pointer-events: auto;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: opacity 0.2s, transform 0.2s;
    }
    .node-label-pill {
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 9999px;
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 500;
      color: #e2e8f0;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6);
      white-space: nowrap;
      max-width: 250px;
      overflow: hidden;
      text-overflow: ellipsis;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .node-label:hover .node-label-pill {
      border-color: rgba(255, 255, 255, 0.4);
      background: rgba(30, 41, 59, 0.95);
      max-width: 420px;
    }
    .mass-badge {
      font-size: 9px;
      padding: 1px 5px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.15);
      color: #94a3b8;
    }

    .top-bar {
      position: absolute;
      top: 16px; left: 20px; right: 20px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      z-index: 10;
      pointer-events: none;
    }
    .brand-box {
      pointer-events: auto;
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      padding: 12px 18px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .brand-title {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.3px;
      color: #f8fafc;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-title span {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 6px;
      border-radius: 4px;
      background: #3b82f6;
      color: #fff;
    }
    .brand-desc {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 4px;
      max-width: 420px;
      line-height: 1.4;
    }
    .chat-select {
      margin-top: 8px;
      background: #1e293b;
      color: #e2e8f0;
      border: 1px solid #334155;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 11px;
      outline: none;
      cursor: pointer;
    }

    .stats-box {
      pointer-events: auto;
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      padding: 12px 16px;
      display: flex;
      gap: 16px;
      align-items: center;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .stat-item { display: flex; flex-direction: column; align-items: flex-end; }
    .stat-label { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 600; }
    .stat-val { font-size: 14px; font-weight: 700; color: #f1f5f9; }
    .mode-pill {
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }

    .bottom-bar {
      position: absolute;
      bottom: 24px; left: 50%;
      transform: translateX(-50%);
      width: min(92%, 760px);
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      padding: 14px 22px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
      z-index: 10;
    }
    .timeline-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .pair-badge {
      font-size: 13px;
      font-weight: 700;
      color: #f8fafc;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pair-badge .current-pair-txt {
      color: #38bdf8;
    }
    .btn-group {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .ctrl-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.15s;
    }
    .ctrl-btn:hover {
      background: #334155;
      color: #fff;
      border-color: #475569;
    }
    .ctrl-btn.active {
      background: #2563eb;
      border-color: #3b82f6;
      color: #fff;
    }
    .slider-track {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .scrubber-slider {
      flex: 1;
      accent-color: #38bdf8;
      cursor: pointer;
    }
    .pair-ticks {
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: #64748b;
      padding: 0 4px;
    }

    .legend-box {
      position: absolute;
      bottom: 24px; left: 24px;
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 11px;
      color: #94a3b8;
      display: flex;
      flex-direction: column;
      gap: 6px;
      z-index: 10;
      pointer-events: none;
    }
    .legend-item { display: flex; align-items: center; gap: 8px; }
    .dot-u { width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }
    .dot-a { width: 8px; height: 8px; border-radius: 50%; background: #fb923c; box-shadow: 0 0 6px #fb923c; }
    .ring-open { width: 8px; height: 8px; border-radius: 50%; border: 1.5px solid #fbbf24; }
    .ring-res { width: 8px; height: 8px; border-radius: 50%; border: 1.5px solid #a855f7; background: #a855f7; }

    .inspector-drawer {
      position: absolute;
      top: 80px; right: 20px;
      width: 330px;
      max-height: calc(100vh - 180px);
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 16px;
      padding: 16px;
      z-index: 20;
      box-shadow: 0 16px 40px rgba(0,0,0,0.7);
      display: none;
      flex-direction: column;
      gap: 12px;
      overflow-y: auto;
    }
    .inspector-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 8px;
    }
    .inspector-title { font-size: 13px; font-weight: 700; color: #f8fafc; }
    .close-btn { background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
    .inspector-body { font-size: 12px; line-height: 1.5; color: #cbd5e1; display: flex; flex-direction: column; gap: 8px; }
    .meta-tag { font-size: 10px; font-weight: 600; text-transform: uppercase; color: #64748b; }
    .quote-box { background: rgba(0,0,0,0.3); border-left: 2px solid #38bdf8; padding: 6px 10px; border-radius: 4px; font-style: italic; color: #93c5fd; }

    .left-controls {
      position: absolute;
      top: 140px; left: 24px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 10;
    }
    .icon-btn {
      width: 36px; height: 36px;
      border-radius: 10px;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #94a3b8;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
      font-size: 15px;
    }
    .icon-btn:hover { background: #1e293b; color: #fff; }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

  <div id="canvas-container"></div>
  <div id="labels-layer"></div>

  <div class="top-bar">
    <div class="brand-box">
      <div class="brand-title">CoTrace 3D Graph <span>Sandbox</span></div>
      <div class="brand-desc" id="chat-summary-text">Loading chat summary...</div>
      <select class="chat-select" id="chat-dropdown">
        <option value="c05_research_medium">c05_research_medium (7 pairs, rich)</option>
        <option value="c04_writing_short">c04_writing_short (4 pairs)</option>
        <option value="c16_research_short">c16_research_short (1 pair)</option>
      </select>
    </div>

    <div class="stats-box">
      <div class="stat-item">
        <div class="stat-label">Mode</div>
        <div class="mode-pill" id="hud-mode">COPILOT</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Steering Split</div>
        <div class="stat-val" id="hud-split">43.5% / 56.5%</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Active Mass</div>
        <div class="stat-val" id="hud-mass">62.0</div>
      </div>
    </div>
  </div>

  <div class="left-controls">
    <button class="icon-btn" id="btn-reset-cam" title="Reset Camera">⟲</button>
    <button class="icon-btn" id="btn-toggle-labels" title="Toggle Labels">🏷</button>
    <button class="icon-btn" id="btn-toggle-spin" title="Toggle Auto-Spin">↻</button>
  </div>

  <div class="legend-box">
    <div class="legend-item"><div class="dot-u"></div> User decision (Requirement)</div>
    <div class="legend-item"><div class="dot-a"></div> AI decision (Requirement)</div>
    <div class="legend-item"><div class="ring-open"></div> Open question (Slot)</div>
    <div class="legend-item"><div class="ring-res"></div> Resolved question (Slot)</div>
  </div>

  <div class="inspector-drawer" id="inspector">
    <div class="inspector-header">
      <div class="inspector-title" id="insp-title">Node Details</div>
      <button class="close-btn" id="btn-close-insp">✕</button>
    </div>
    <div class="inspector-body" id="insp-body"></div>
  </div>

  <div class="bottom-bar">
    <div class="timeline-header">
      <div class="pair-badge">
        <span>Timeline View:</span>
        <span class="current-pair-txt" id="lbl-current-pair">Pair 1 of 7</span>
      </div>
      <div class="btn-group">
        <button class="ctrl-btn" id="btn-prev">◀ Prev</button>
        <button class="ctrl-btn" id="btn-play">▶ Play</button>
        <button class="ctrl-btn" id="btn-next">Next ▶</button>
      </div>
    </div>
    <div class="slider-track">
      <input type="range" class="scrubber-slider" id="pair-slider" min="1" max="7" value="1" step="1">
    </div>
    <div class="pair-ticks" id="pair-ticks"></div>
  </div>

  <script>
    const BUNDLED_CHATS = __BUNDLED_CHATS_JSON__;

    let currentChatKey = 'c05_research_medium';
    let currentChatData = BUNDLED_CHATS[currentChatKey];
    let currentPair = 1;
    let maxPairs = currentChatData.total_pairs;
    let isPlaying = false;
    let playTimer = null;
    let showLabels = true;
    let autoSpin = false;

    const COLOR_PALETTE = [
      0x3b82f6, // root: blue
      0x14b8a6, // teal
      0xa855f7, // purple
      0xf59e0b, // amber
      0x10b981, // emerald
      0xf43f5e, // rose
      0x06b6d4, // cyan
      0x8b5cf6  // violet
    ];

    let scene, camera, renderer, controls;
    let nodeObjects = new Map();
    let edgeObjects = [];
    let raycaster = new THREE.Raycaster();
    let mouse = new THREE.Vector2();

    const container = document.getElementById('canvas-container');
    const labelsLayer = document.getElementById('labels-layer');

    function init3D() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x0d0d12, 0.0018);

      camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 2000);
      camera.position.set(0, 0, 180);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);

      const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
      scene.add(ambientLight);

      const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
      dirLight.position.set(50, 100, 80);
      scene.add(dirLight);

      const bluePoint = new THREE.PointLight(0x38bdf8, 2.5, 300);
      bluePoint.position.set(0, 0, 30);
      scene.add(bluePoint);

      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 30;
        controls.maxDistance = 600;
      } else {
        let isDragging = false, px = 0, py = 0;
        window.addEventListener('mousedown', e => { isDragging = true; px = e.clientX; py = e.clientY; });
        window.addEventListener('mousemove', e => {
          if (!isDragging) return;
          scene.rotation.y += (e.clientX - px) * 0.005;
          scene.rotation.x += (e.clientY - py) * 0.005;
          px = e.clientX; py = e.clientY;
        });
        window.addEventListener('mouseup', () => isDragging = false);
      }

      window.addEventListener('resize', onWindowResize);
      renderer.domElement.addEventListener('click', onCanvasClick);

      loadChat(currentChatKey);
      animate();
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function loadChat(chatKey) {
      currentChatKey = chatKey;
      currentChatData = BUNDLED_CHATS[chatKey];
      maxPairs = currentChatData.total_pairs;
      currentPair = 1;

      document.getElementById('chat-summary-text').innerText = currentChatData.dialogue_summary || 'Co-creative chat interaction';
      
      const slider = document.getElementById('pair-slider');
      slider.max = maxPairs;
      slider.value = 1;

      const ticksContainer = document.getElementById('pair-ticks');
      ticksContainer.innerHTML = '';
      for (let i = 1; i <= maxPairs; i++) {
        const span = document.createElement('span');
        span.innerText = 'P' + i;
        ticksContainer.appendChild(span);
      }

      rebuildGraph();
      applyPairState(currentPair);
    }

    function rebuildGraph() {
      nodeObjects.forEach(obj => {
        scene.remove(obj.mesh);
        if (obj.satellitesGroup) scene.remove(obj.satellitesGroup);
        if (obj.labelEl) obj.labelEl.remove();
      });
      nodeObjects.clear();

      edgeObjects.forEach(e => scene.remove(e.line));
      edgeObjects = [];
      labelsLayer.innerHTML = '';

      const outcomes = currentChatData.step_1_outcomes;
      const childOutcomes = outcomes.filter(o => o.parent !== null);
      const totalChildren = childOutcomes.length;

      const rootOutcome = outcomes.find(o => o.parent === null) || outcomes[0];
      createNodeMesh(rootOutcome, 0, new THREE.Vector3(0, 0, 0), 0x3b82f6);

      childOutcomes.forEach((o, idx) => {
        const angle = (idx / totalChildren) * Math.PI * 2 + 0.3;
        const radius = 65 + (idx % 2) * 15;
        const zOffset = ((idx % 3) - 1) * 18;
        const pos = new THREE.Vector3(
          Math.cos(angle) * radius,
          Math.sin(angle) * radius * 0.85,
          zOffset
        );
        createNodeMesh(o, idx + 1, pos, COLOR_PALETTE[(idx + 1) % COLOR_PALETTE.length]);
      });

      outcomes.forEach(o => {
        if (o.parent && nodeObjects.has(o.parent) && nodeObjects.has(o.id)) {
          createEdge(nodeObjects.get(o.parent), nodeObjects.get(o.id), false);
        }
        if (o.related) {
          o.related.forEach(relId => {
            if (nodeObjects.has(o.id) && nodeObjects.has(relId)) {
              createEdge(nodeObjects.get(o.id), nodeObjects.get(relId), true);
            }
          });
        }
      });
    }

    function createNodeMesh(outcome, index, position, colorHex) {
      const sphereGeo = new THREE.SphereGeometry(1, 32, 32);
      const mat = new THREE.MeshStandardMaterial({
        color: colorHex,
        roughness: 0.25,
        metalness: 0.15,
        emissive: colorHex,
        emissiveIntensity: 0.35,
        transparent: true,
        opacity: 0
      });

      const mesh = new THREE.Mesh(sphereGeo, mat);
      mesh.position.copy(position);
      mesh.userData = { type: 'outcome', outcome: outcome };
      scene.add(mesh);

      const satGroup = new THREE.Group();
      satGroup.position.copy(position);
      scene.add(satGroup);

      const label = document.createElement('div');
      label.className = 'node-label';
      label.innerHTML = `
        <div class="node-label-pill">
          <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#${mat.color.getHexString()};"></span>
          <span class="label-text">${outcome.text}</span>
          <span class="mass-badge" id="badge-${outcome.id.replace(/\\s+/g, '-')}">0</span>
        </div>
      `;
      label.addEventListener('click', () => showInspector(outcome, 'outcome'));
      labelsLayer.appendChild(label);

      nodeObjects.set(outcome.id, {
        mesh: mesh,
        mat: mat,
        satellitesGroup: satGroup,
        targetRadius: 0.001,
        targetPos: position,
        labelEl: label,
        data: outcome,
        satellites: []
      });
    }

    function createEdge(fromObj, toObj, isRelated) {
      const points = [fromObj.mesh.position, toObj.mesh.position];
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({
        color: isRelated ? 0x64748b : 0x94a3b8,
        transparent: true,
        opacity: 0,
        linewidth: 1
      });
      const line = new THREE.Line(geo, mat);
      scene.add(line);
      edgeObjects.push({ line, from: fromObj, to: toObj, isRelated });
    }

    function applyPairState(pairNum) {
      currentPair = pairNum;
      document.getElementById('lbl-current-pair').innerText = `Pair ${pairNum} of ${maxPairs}`;
      document.getElementById('pair-slider').value = pairNum;

      const pairData = currentChatData.step_4_pairs[pairNum - 1];

      document.getElementById('hud-mode').innerText = pairData.mode.classification;
      document.getElementById('hud-split').innerText = `${pairData.influence.user_pct}% / ${pairData.influence.ai_pct}%`;

      const cumulativeMass = {};
      let totalActiveMass = 0;
      for (let p = 0; p < pairNum; p++) {
        const pObj = currentChatData.step_4_pairs[p];
        pObj.ledger_rows.forEach(r => {
          cumulativeMass[r.outcome_id] = (cumulativeMass[r.outcome_id] || 0) + r.score;
          totalActiveMass += r.score;
        });
      }
      document.getElementById('hud-mass').innerText = totalActiveMass.toFixed(0);

      let maxChildMass = 1;
      Object.keys(cumulativeMass).forEach(oid => {
        if (oid !== 'outcome 1' && cumulativeMass[oid] > maxChildMass) maxChildMass = cumulativeMass[oid];
      });

      const activeReqs = currentChatData.step_2_requirements.filter(r => r.created_at_pair <= pairNum);
      const allSlots = currentChatData.step_2_slots || [];

      nodeObjects.forEach((obj, oid) => {
        const mass = cumulativeMass[oid] || 0;
        const isRoot = obj.data.parent === null;
        const isBorn = mass > 0 || isRoot;

        const badge = document.getElementById(`badge-${oid.replace(/\\s+/g, '-')}`);
        if (badge) badge.innerText = Math.round(mass);

        if (isBorn) {
          let targetRad = 5;
          if (isRoot) {
            targetRad = 15;
          } else {
            targetRad = 5 + 10 * Math.sqrt(mass / maxChildMass);
          }
          obj.targetRadius = targetRad;
          obj.targetOpacity = 0.95;
          obj.labelEl.style.opacity = showLabels ? '1' : '0';
        } else {
          obj.targetRadius = 0.001;
          obj.targetOpacity = 0;
          obj.labelEl.style.opacity = '0';
        }

        rebuildSatellites(obj, oid, activeReqs, allSlots, pairNum);
      });

      edgeObjects.forEach(edge => {
        const fromVisible = edge.from.targetOpacity > 0.1;
        const toVisible = edge.to.targetOpacity > 0.1;
        edge.targetOpacity = (fromVisible && toVisible) ? (edge.isRelated ? 0.35 : 0.7) : 0;
      });
    }

    function rebuildSatellites(nodeObj, outcomeId, activeReqs, allSlots, pairNum) {
      const group = nodeObj.satellitesGroup;
      while (group.children.length > 0) {
        group.remove(group.children[0]);
      }

      if (nodeObj.targetRadius < 0.1) return;

      const reqsForNode = activeReqs.filter(r => r.outcome_id === outcomeId);
      const slotsForNode = allSlots.filter(s => {
        if (s.outcome_id !== outcomeId) return false;
        const caids = s.creation_action_ids || [];
        const createdPair = caids.length > 0 ? parseInt(caids[0].split('(')[1]) : 1;
        return createdPair <= pairNum;
      });

      const totalSatellites = reqsForNode.length + slotsForNode.length;
      if (totalSatellites === 0) return;

      let idx = 0;
      reqsForNode.forEach(req => {
        const isUser = req.creation_action_ids && req.creation_action_ids[0].startsWith('U');
        const color = isUser ? 0x38bdf8 : 0xfb923c;
        const dotGeo = new THREE.SphereGeometry(1.6, 16, 16);
        const dotMat = new THREE.MeshStandardMaterial({
          color: color,
          emissive: color,
          emissiveIntensity: 0.6
        });
        const dotMesh = new THREE.Mesh(dotGeo, dotMat);

        const angle = (idx / totalSatellites) * Math.PI * 2;
        const dist = nodeObj.targetRadius + 5.5;
        dotMesh.position.set(Math.cos(angle) * dist, Math.sin(angle) * dist, (idx % 2) * 2 - 1);
        dotMesh.userData = { type: 'requirement', data: req, isUser };
        group.add(dotMesh);
        idx++;
      });

      slotsForNode.forEach(slot => {
        const isResolved = slot.resolved_into && activeReqs.some(r => r.req_id === slot.resolved_into && r.outcome_id === slot.outcome_id);
        const ringColor = isResolved ? 0xa855f7 : 0xfbbf24;

        let slotMesh;
        if (isResolved) {
          const geo = new THREE.TorusGeometry(1.9, 0.45, 12, 24);
          const mat = new THREE.MeshStandardMaterial({ color: ringColor, emissive: ringColor, emissiveIntensity: 0.7 });
          slotMesh = new THREE.Mesh(geo, mat);
        } else {
          const geo = new THREE.TorusGeometry(1.9, 0.25, 12, 24);
          const mat = new THREE.MeshStandardMaterial({ color: ringColor, emissive: ringColor, emissiveIntensity: 0.5 });
          slotMesh = new THREE.Mesh(geo, mat);
        }

        const angle = (idx / totalSatellites) * Math.PI * 2;
        const dist = nodeObj.targetRadius + 6.0;
        slotMesh.position.set(Math.cos(angle) * dist, Math.sin(angle) * dist, (idx % 2) * 2 - 1);
        slotMesh.userData = { type: 'slot', data: slot, isResolved };
        group.add(slotMesh);
        idx++;
      });
    }

    function onCanvasClick(event) {
      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(scene.children, true);

      if (intersects.length > 0) {
        let hit = intersects[0].object;
        while (hit && !hit.userData.type && hit.parent && hit.parent !== scene) {
          hit = hit.parent;
        }
        if (hit && hit.userData.type) {
          showInspector(hit.userData.data || hit.userData.outcome, hit.userData.type, hit.userData);
        }
      }
    }

    function showInspector(item, type, extra) {
      const drawer = document.getElementById('inspector');
      const title = document.getElementById('insp-title');
      const body = document.getElementById('insp-body');
      drawer.style.display = 'flex';

      if (type === 'outcome') {
        title.innerText = item.id.toUpperCase();
        body.innerHTML = `
          <div class="meta-tag">Goal Node</div>
          <div style="font-weight:600; font-size:13px; color:#fff;">"${item.text}"</div>
          <div class="meta-tag">Turn Created: ${item.turn_id || 'Initial'}</div>
          <div class="meta-tag">Parent: ${item.parent || 'None (Root)'}</div>
        `;
      } else if (type === 'requirement') {
        title.innerText = `${item.outcome_id} / ${item.req_id}`;
        body.innerHTML = `
          <div class="meta-tag">Requirement (${extra.isUser ? 'User-Created 🔵' : 'AI-Created 🟠'})</div>
          <div style="font-weight:600; font-size:13px; color:#fff;">"${item.text}"</div>
          <div class="meta-tag">Type: ${item.type} | Status: ${item.status}</div>
          <div class="meta-tag">Rationale:</div>
          <div class="quote-box">"${item.rationale || 'N/A'}"</div>
          <div class="meta-tag">Created at Pair: ${item.created_at_pair}</div>
        `;
      } else if (type === 'slot') {
        title.innerText = `${item.outcome_id} / ${item.slot_id}`;
        body.innerHTML = `
          <div class="meta-tag">Question / Slot (${extra.isResolved ? 'Resolved ◎' : 'Open / Abandoned ○'})</div>
          <div style="font-weight:600; font-size:13px; color:#fff;">"${item.text}"</div>
          <div class="meta-tag">Origin: ${item.origin} | Status: ${item.status}</div>
          ${item.resolved_into ? `<div class="meta-tag">Resolved Into: ${item.resolved_into}</div>` : ''}
        `;
      }
    }

    document.getElementById('btn-close-insp').addEventListener('click', () => {
      document.getElementById('inspector').style.display = 'none';
    });

    document.getElementById('btn-prev').addEventListener('click', () => {
      if (currentPair > 1) applyPairState(currentPair - 1);
    });
    document.getElementById('btn-next').addEventListener('click', () => {
      if (currentPair < maxPairs) applyPairState(currentPair + 1);
    });
    document.getElementById('pair-slider').addEventListener('input', (e) => {
      applyPairState(parseInt(e.target.value));
    });

    document.getElementById('btn-play').addEventListener('click', () => {
      isPlaying = !isPlaying;
      const btn = document.getElementById('btn-play');
      if (isPlaying) {
        btn.innerText = '⏸ Pause';
        btn.classList.add('active');
        playTimer = setInterval(() => {
          if (currentPair < maxPairs) {
            applyPairState(currentPair + 1);
          } else {
            applyPairState(1);
          }
        }, 1800);
      } else {
        btn.innerText = '▶ Play';
        btn.classList.remove('active');
        clearInterval(playTimer);
      }
    });

    document.getElementById('chat-dropdown').addEventListener('change', (e) => {
      loadChat(e.target.value);
    });

    document.getElementById('btn-reset-cam').addEventListener('click', () => {
      camera.position.set(0, 0, 180);
      if (controls) controls.target.set(0, 0, 0);
    });

    document.getElementById('btn-toggle-labels').addEventListener('click', () => {
      showLabels = !showLabels;
      nodeObjects.forEach(obj => {
        if (obj.targetRadius > 0.1) {
          obj.labelEl.style.opacity = showLabels ? '1' : '0';
        }
      });
    });

    document.getElementById('btn-toggle-spin').addEventListener('click', () => {
      autoSpin = !autoSpin;
      document.getElementById('btn-toggle-spin').style.color = autoSpin ? '#38bdf8' : '#94a3b8';
    });

    function animate() {
      requestAnimationFrame(animate);

      if (controls) controls.update();

      if (autoSpin) {
        scene.rotation.y += 0.003;
      }

      nodeObjects.forEach(obj => {
        const currentScale = obj.mesh.scale.x;
        const targetScale = obj.targetRadius;
        const newScale = THREE.MathUtils.lerp(currentScale, targetScale, 0.08);
        obj.mesh.scale.set(newScale, newScale, newScale);

        obj.mat.opacity = THREE.MathUtils.lerp(obj.mat.opacity, obj.targetOpacity, 0.08);

        if (obj.labelEl) {
          const tempV = new THREE.Vector3();
          obj.mesh.getWorldPosition(tempV);
          tempV.y += newScale + 2.5;
          tempV.project(camera);

          const x = (tempV.x * 0.5 + 0.5) * window.innerWidth;
          const y = (-(tempV.y * 0.5) + 0.5) * window.innerHeight;

          obj.labelEl.style.left = `${x}px`;
          obj.labelEl.style.top = `${y}px`;

          if (tempV.z > 1) {
            obj.labelEl.style.display = 'none';
          } else {
            obj.labelEl.style.display = 'flex';
          }
        }

        if (obj.satellitesGroup) {
          obj.satellitesGroup.rotation.z += 0.004;
        }
      });

      edgeObjects.forEach(edge => {
        edge.line.material.opacity = THREE.MathUtils.lerp(edge.line.material.opacity, edge.targetOpacity || 0, 0.08);
      });

      renderer.render(scene, camera);
    }

    window.addEventListener('DOMContentLoaded', init3D);
  </script>
</body>
</html>
"""

    final_html = template.replace('__BUNDLED_CHATS_JSON__', json_str)
    out_path = 'design_pack/playground_3d.html'
    with open(out_path, 'w') as f:
        f.write(final_html)
    print(f"Successfully generated {out_path} ({len(final_html)} bytes)")

if __name__ == '__main__':
    build()
