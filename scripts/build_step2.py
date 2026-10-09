import json
import os

def build_step2():
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
  <title>CoTrace 3D · Pair 1 Complete Universe (3 Outcomes)</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #06060a;
      color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
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

    /* Pure Obsidian Floating Labels: EXACT text only, zero metadata */
    .obsidian-label {
      position: absolute;
      transform: translate(-50%, 0);
      pointer-events: auto;
      cursor: default;
      text-align: center;
      white-space: nowrap;
      transition: opacity 0.2s ease;
    }
    .label-root {
      font-size: 15px;
      font-weight: 500;
      color: #ffffff;
      letter-spacing: -0.2px;
      text-shadow: 
        0 0 16px rgba(255, 255, 255, 0.9),
        0 0 32px rgba(255, 255, 255, 0.45),
        0 2px 10px rgba(0, 0, 0, 0.95);
    }
    .label-child {
      font-size: 13.5px;
      font-weight: 500;
      color: #f1f5f9;
      letter-spacing: -0.2px;
      text-shadow: 
        0 0 14px rgba(255, 255, 255, 0.8),
        0 2px 10px rgba(0, 0, 0, 0.95);
    }

    /* Top HUD */
    .top-bar {
      position: absolute;
      top: 20px; left: 24px; right: 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      z-index: 10;
      pointer-events: none;
    }
    .brand-box {
      pointer-events: auto;
      background: rgba(10, 10, 16, 0.75);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      padding: 12px 18px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .brand-title {
      font-size: 14px;
      font-weight: 700;
      letter-spacing: -0.3px;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-title span {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      padding: 2px 7px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.12);
      color: #f8fafc;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .brand-desc {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 4px;
      max-width: 480px;
      line-height: 1.4;
    }

    /* View Switcher */
    .view-switcher {
      pointer-events: auto;
      display: flex;
      gap: 8px;
    }
    .view-btn {
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #94a3b8;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 500;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s;
    }
    .view-btn:hover { background: #334155; color: #fff; }
    .view-btn.active { background: #3b82f6; border-color: #60a5fa; color: #fff; }

    /* Bottom Bar */
    .bottom-bar {
      position: absolute;
      bottom: 24px; left: 50%;
      transform: translateX(-50%);
      width: min(92%, 820px);
      background: rgba(10, 10, 16, 0.82);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 20px;
      padding: 14px 22px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
      z-index: 10;
    }
    .pair-badge {
      font-size: 13px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pair-badge span { color: #38bdf8; }
    .step-info { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 14px; }
    .legend-tag { display: flex; align-items: center; gap: 5px; }
    .line-solid-icon { width: 14px; height: 2px; background: rgba(255,255,255,0.7); }
    .line-dashed-icon { width: 14px; height: 0px; border-top: 2px dashed rgba(148,163,184,0.9); }

    .btn-reset-view {
      position: absolute;
      bottom: 24px; right: 28px;
      z-index: 10;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #cbd5e1;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-reset-view:hover {
      background: #1e293b;
      color: #fff;
      border-color: rgba(255, 255, 255, 0.3);
    }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

  <div id="canvas-container"></div>
  <div id="labels-layer">
    <!-- Root Goal Label: ONLY EXACT TEXT -->
    <div class="obsidian-label" id="root-label">
      <div class="label-root">Course assignment strategy and deliverables</div>
    </div>
    <!-- Child Outcome 2 Label: ONLY EXACT TEXT -->
    <div class="obsidian-label" id="child1-label">
      <div class="label-child">Initial assignment plan and paper search strategy</div>
    </div>
    <!-- Child Outcome 3 Label: ONLY EXACT TEXT -->
    <div class="obsidian-label" id="child2-label">
      <div class="label-child">Expanded paper bank and recommendations</div>
    </div>
  </div>

  <div id="satellite-tooltip" style="position: absolute; display: none; pointer-events: none; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #f1f5f9; max-width: 280px; line-height: 1.4; z-index: 100; box-shadow: 0 8px 24px rgba(0,0,0,0.6);"></div>

  <div class="top-bar">
    <div class="brand-box">
      <div class="brand-title">CoTrace 3D Universe <span>Pair 1 Complete</span></div>
      <div class="brand-desc">Root Origin anchored at (0,0,0) with solid tethers to Child 1 (44 mass) and Child 2 (18 mass). Satellite requirement beads and open slot rings orbit their deliverables. Hover satellites to inspect exact text.</div>
    </div>

    <div class="view-switcher">
      <a href="playground_obsidian.html" class="view-btn">Switch to 2D Obsidian View ↗</a>
      <span class="view-btn active">3D Universe View</span>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="pair-badge">
      <span>Pair 1 Universe:</span> Root ──► 2 Deliverables + Micro-Anatomy
    </div>
    <div class="step-info">
      <div class="legend-tag"><div style="width:8px;height:8px;border-radius:50%;background:#38bdf8;box-shadow:0 0 6px #38bdf8;"></div> User Req (Solid Bead)</div>
      <div class="legend-tag"><span style="display:inline-block;width:9px;height:9px;border-radius:50%;border:1.5px solid #fb923c;"></span> Open Question (Hollow Ring)</div>
      <div class="legend-tag"><div class="line-solid-icon"></div> Solid Tether</div>
      <div class="legend-tag"><div class="line-dashed-icon"></div> Dashed Relation</div>
    </div>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    let scene, camera, renderer, controls;
    let rootGroup, child1Group, child2Group;
    let tether1Line, tether2Line, relatedLine;
    let c1UserLight, c1AiLight, c2UserLight, c2AiLight;
    let c2BeaconMesh, c2BeaconMat;
    let c2SlotTorus, c2SlotTorusMat;
    const interactiveSatellites = [];
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const rootLabelEl = document.getElementById('root-label');
    const child1LabelEl = document.getElementById('child1-label');
    const child2LabelEl = document.getElementById('child2-label');

    const ROOT_POS = new THREE.Vector3(0, 0, 0);
    const CHILD1_POS = new THREE.Vector3(-44, 25, -6);
    const CHILD2_POS = new THREE.Vector3(42, 22, 6);

    function init() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x06060a, 0.0016);

      camera = new THREE.PerspectiveCamera(46, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, 18, 145);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      document.getElementById('canvas-container').appendChild(renderer.domElement);

      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 25;
        controls.maxDistance = 500;
        controls.target.set(0, 12, 0);
      }

      // Studio Ambient Light
      const ambient = new THREE.AmbientLight(0x1e293b, 1.3);
      scene.add(ambient);

      const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
      dirLight.position.set(50, 80, 70);
      scene.add(dirLight);

      // Root Point Light
      const rootLight = new THREE.PointLight(0xffffff, 2.5, 120);
      rootLight.position.copy(ROOT_POS);
      scene.add(rootLight);

      // Build 3D Scene Entities
      buildRootSphere();
      buildConnections();
      buildChildOutcome1();
      buildChildOutcome2();
      buildSpaceParticles();

      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, 18, 145);
        if (controls) controls.target.set(0, 12, 0);
      });

      // Hover Raycasting for Satellites
      const tip = document.getElementById('satellite-tooltip');
      window.addEventListener('mousemove', (e) => {
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(interactiveSatellites);

        if (intersects.length > 0) {
          const hit = intersects[0].object;
          const d = hit.userData;
          if (d && d.text) {
            tip.style.display = 'block';
            tip.style.left = `${e.clientX + 14}px`;
            tip.style.top = `${e.clientY + 10}px`;
            const badgeBg = d.color === '#38bdf8' ? 'rgba(56,189,248,0.15)' : 'rgba(251,146,60,0.15)';
            tip.innerHTML = `
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span style="font-size:10px;font-weight:700;text-transform:uppercase;color:${d.color};background:${badgeBg};padding:2px 6px;border-radius:4px;border:1px solid ${d.color}44;">${d.label}</span>
                <span style="color:#64748b;font-size:10px;">${d.id}</span>
              </div>
              <div style="color:#e2e8f0;font-size:11.5px;">${d.text}</div>
            `;
            document.body.style.cursor = 'pointer';
          }
        } else {
          tip.style.display = 'none';
          document.body.style.cursor = 'default';
        }
      });

      animate();
    }

    function buildRootSphere() {
      rootGroup = new THREE.Group();
      rootGroup.position.copy(ROOT_POS);
      scene.add(rootGroup);

      const sphereGeo = new THREE.SphereGeometry(9.0, 64, 64);
      const mat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        emissive: 0xffffff,
        emissiveIntensity: 0.85,
        roughness: 0.1,
        transparent: true,
        opacity: 0.88,
        transmission: 0.4,
        clearcoat: 1.0
      });
      rootGroup.add(new THREE.Mesh(sphereGeo, mat));

      const coreGeo = new THREE.SphereGeometry(5.5, 32, 32);
      const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95 });
      rootGroup.add(new THREE.Mesh(coreGeo, coreMat));

      const rMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.55, side: THREE.DoubleSide });
      rootGroup.add(new THREE.Mesh(new THREE.RingGeometry(13.5, 13.9, 64), rMat));
      rootGroup.add(new THREE.Mesh(new THREE.RingGeometry(19.0, 19.3, 64), rMat));
      rootGroup.add(new THREE.Mesh(new THREE.RingGeometry(26.0, 26.3, 64), rMat));

      rootGroup.rotation.x = Math.PI * 0.12;
      rootGroup.rotation.y = Math.PI * 0.08;
    }

    // Helper: Clip line strictly between outer circumferences of two 3D spheres
    function createClippedLine(p1, r1, p2, r2, isDashed = false, color = 0xffffff, opacity = 0.45) {
      const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
      const start = p1.clone().add(dir.clone().multiplyScalar(r1));
      const end = p2.clone().sub(dir.clone().multiplyScalar(r2));
      const geo = new THREE.BufferGeometry().setFromPoints([start, end]);
      if (isDashed) {
        geo.computeLineDistances();
        return new THREE.Line(geo, new THREE.LineDashedMaterial({ color: color, dashSize: 2.5, gapSize: 2.0, transparent: true, opacity: opacity }));
      } else {
        return new THREE.Line(geo, new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: opacity, linewidth: 1.5 }));
      }
    }

    function buildConnections() {
      // 1. SOLID TETHER: Root (R=9.0) -> Child 1 (R=7.8) — Strictly outside outer circumferences!
      tether1Line = createClippedLine(ROOT_POS, 9.0, CHILD1_POS, 7.8, false, 0xffffff, 0.45);
      scene.add(tether1Line);

      // 2. SOLID TETHER: Root (R=9.0) -> Child 2 (R=5.2) — Strictly outside outer circumferences!
      tether2Line = createClippedLine(ROOT_POS, 9.0, CHILD2_POS, 5.2, false, 0xffffff, 0.45);
      scene.add(tether2Line);

      // 3. DASHED RELATIONAL LINK: Child 1 (R=7.8) <--> Child 2 (R=5.2)
      relatedLine = createClippedLine(CHILD1_POS, 7.8, CHILD2_POS, 5.2, true, 0x94a3b8, 0.55);
      scene.add(relatedLine);
    }

    function buildChildOutcome1() {
      // Outcome 2: Mass 44.0 (User 19.0 / AI 25.0) -> Radius 7.8
      child1Group = new THREE.Group();
      child1Group.position.copy(CHILD1_POS);
      scene.add(child1Group);

      c1UserLight = new THREE.PointLight(0x38bdf8, 3.2, 50);
      c1UserLight.position.set(-2.8, 0, 0);
      child1Group.add(c1UserLight);

      c1AiLight = new THREE.PointLight(0xfb923c, 4.2, 55);
      c1AiLight.position.set(2.8, 0, 0);
      child1Group.add(c1AiLight);

      const beadGeo = new THREE.SphereGeometry(1.6, 16, 16);
      const userBead = new THREE.Mesh(beadGeo, new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
      userBead.position.set(-2.8, 0, 0);
      child1Group.add(userBead);

      const aiBead = new THREE.Mesh(beadGeo, new THREE.MeshBasicMaterial({ color: 0xfb923c }));
      aiBead.position.set(2.8, 0, 0);
      child1Group.add(aiBead);

      // Frosted Shell R = 7.8
      const sphereGeo = new THREE.SphereGeometry(7.8, 48, 48);
      const frostedMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.38,
        metalness: 0.05,
        transmission: 0.65,
        ior: 1.33,
        transparent: true,
        opacity: 0.82,
        clearcoat: 0.6,
        clearcoatRoughness: 0.2,
        side: THREE.DoubleSide
      });
      child1Group.add(new THREE.Mesh(sphereGeo, frostedMat));

      const auraGeo = new THREE.RingGeometry(7.6, 12.0, 48);
      const auraMat = new THREE.MeshBasicMaterial({ color: 0xffedd5, transparent: true, opacity: 0.22, side: THREE.DoubleSide });
      child1Group.add(new THREE.Mesh(auraGeo, auraMat));

      // ─────────────────────────────────────────────────────────────
      // SATELLITE MICRO-ATOMS IN UPPER CROWN (Y > 0, away from text below)
      // Tethers start on outer sphere shell (R = 7.8), never cutting inside!
      // ─────────────────────────────────────────────────────────────
      const satGeo = new THREE.SphereGeometry(1.2, 16, 16);
      const userSatMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
      const satLineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.45 });

      // req 1: (-10, 11, 2)
      const p1 = new THREE.Vector3(-10, 11, 2);
      const sat1 = new THREE.Mesh(satGeo, userSatMat);
      sat1.position.copy(p1);
      sat1.userData = { label: "User Requirement", id: "req 1", text: "The AI must review and understand the user's handwritten notes.", color: "#38bdf8" };
      child1Group.add(sat1);
      interactiveSatellites.push(sat1);

      // Clipped line starting from outer radius 7.8
      const d1 = p1.clone().normalize();
      const line1Geo = new THREE.BufferGeometry().setFromPoints([d1.clone().multiplyScalar(7.8), p1.clone().sub(d1.clone().multiplyScalar(1.2))]);
      child1Group.add(new THREE.Line(line1Geo, satLineMat));

      // req 2: (-4, 13, -2)
      const p2 = new THREE.Vector3(-4, 13, -2);
      const sat2 = new THREE.Mesh(satGeo, userSatMat);
      sat2.position.copy(p2);
      sat2.userData = { label: "User Requirement", id: "req 2", text: "The AI must review the project files and assignment requirements.", color: "#38bdf8" };
      child1Group.add(sat2);
      interactiveSatellites.push(sat2);

      const d2 = p2.clone().normalize();
      const line2Geo = new THREE.BufferGeometry().setFromPoints([d2.clone().multiplyScalar(7.8), p2.clone().sub(d2.clone().multiplyScalar(1.2))]);
      child1Group.add(new THREE.Line(line2Geo, satLineMat));
    }

    function buildChildOutcome2() {
      // Outcome 3: Mass 18.0 (User 8.0 / AI 10.0) -> Radius 5.2 (Visibly smaller)
      child2Group = new THREE.Group();
      child2Group.position.copy(CHILD2_POS);
      scene.add(child2Group);

      c2UserLight = new THREE.PointLight(0x38bdf8, 1.8, 40);
      c2UserLight.position.set(-1.8, 0, 0);
      child2Group.add(c2UserLight);

      c2AiLight = new THREE.PointLight(0xfb923c, 2.2, 45);
      c2AiLight.position.set(1.8, 0, 0);
      child2Group.add(c2AiLight);

      const beadGeo = new THREE.SphereGeometry(1.1, 16, 16);
      const userBead = new THREE.Mesh(beadGeo, new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
      userBead.position.set(-1.8, 0, 0);
      child2Group.add(userBead);

      const aiBead = new THREE.Mesh(beadGeo, new THREE.MeshBasicMaterial({ color: 0xfb923c }));
      aiBead.position.set(1.8, 0, 0);
      child2Group.add(aiBead);

      // Frosted Shell R = 5.2 (Noticeably smaller than 7.8)
      const sphereGeo = new THREE.SphereGeometry(5.2, 48, 48);
      const frostedMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.38,
        metalness: 0.05,
        transmission: 0.65,
        ior: 1.33,
        transparent: true,
        opacity: 0.82,
        clearcoat: 0.6,
        clearcoatRoughness: 0.2,
        side: THREE.DoubleSide
      });
      child2Group.add(new THREE.Mesh(sphereGeo, frostedMat));

      const auraGeo = new THREE.RingGeometry(5.0, 8.5, 48);
      const auraMat = new THREE.MeshBasicMaterial({ color: 0xffedd5, transparent: true, opacity: 0.20, side: THREE.DoubleSide });
      child2Group.add(new THREE.Mesh(auraGeo, auraMat));

      // Terminal Active Beacon Halo (Pair 1 Focus Point)
      const beaconGeo = new THREE.RingGeometry(5.4, 6.0, 48);
      c2BeaconMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.7, side: THREE.DoubleSide });
      c2BeaconMesh = new THREE.Mesh(beaconGeo, c2BeaconMat);
      child2Group.add(c2BeaconMesh);

      // ─────────────────────────────────────────────────────────────
      // SATELLITE MICRO-ATOMS IN UPPER CROWN (Y > 0, away from text below)
      // Tethers start on outer sphere shell (R = 5.2), never cutting inside!
      // ─────────────────────────────────────────────────────────────
      const satGeo = new THREE.SphereGeometry(1.1, 16, 16);
      const userSatMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
      const satLineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.45 });

      // req 1: (6, 9, 2)
      const p3 = new THREE.Vector3(6, 9, 2);
      const sat3 = new THREE.Mesh(satGeo, userSatMat);
      sat3.position.copy(p3);
      sat3.userData = { label: "User Requirement", id: "req 1", text: "Search for research papers related to AI creativity and course requirements.", color: "#38bdf8" };
      child2Group.add(sat3);
      interactiveSatellites.push(sat3);

      const d3 = p3.clone().normalize();
      const line3Geo = new THREE.BufferGeometry().setFromPoints([d3.clone().multiplyScalar(5.2), p3.clone().sub(d3.clone().multiplyScalar(1.1))]);
      child2Group.add(new THREE.Line(line3Geo, satLineMat));

      // slot 1 (Open Question): Hollow Torus Ring in Amber at (9, 7, -2)
      const p4 = new THREE.Vector3(9, 7, -2);
      const torusGeo = new THREE.TorusGeometry(1.4, 0.24, 16, 32);
      c2SlotTorusMat = new THREE.MeshBasicMaterial({ color: 0xfb923c, transparent: true, opacity: 0.85 });
      c2SlotTorus = new THREE.Mesh(torusGeo, c2SlotTorusMat);
      c2SlotTorus.position.copy(p4);
      c2SlotTorus.userData = { label: "Open Question / Slot", id: "slot 1", text: "Selection of two specific research directions to guide the paper search.", color: "#fb923c" };
      child2Group.add(c2SlotTorus);
      interactiveSatellites.push(c2SlotTorus);

      const d4 = p4.clone().normalize();
      const slotLineMat = new THREE.LineBasicMaterial({ color: 0xfb923c, transparent: true, opacity: 0.45 });
      const line4Geo = new THREE.BufferGeometry().setFromPoints([d4.clone().multiplyScalar(5.2), p4.clone().sub(d4.clone().multiplyScalar(1.4))]);
      child2Group.add(new THREE.Line(line4Geo, slotLineMat));
    }

    function buildSpaceParticles() {
      const starCount = 300;
      const positions = new Float32Array(starCount * 3);
      for (let i = 0; i < starCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 500;
        positions[i + 1] = (Math.random() - 0.5) * 500;
        positions[i + 2] = (Math.random() - 0.5) * 500;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const mat = new THREE.PointsMaterial({ color: 0xffffff, size: 1.1, transparent: true, opacity: 0.3 });
      scene.add(new THREE.Points(geo, mat));
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function updateLabelPos(el, pos, yOffset) {
      if (!el) return;
      const p = new THREE.Vector3(pos.x, pos.y - yOffset, pos.z);
      p.project(camera);

      const px = (p.x * 0.5 + 0.5) * window.innerWidth;
      const py = (-(p.y * 0.5) + 0.5) * window.innerHeight;
      el.style.left = `${px}px`;
      el.style.top = `${py}px`;

      const camDist = camera.position.distanceTo(pos);
      if (camDist > 320) {
        el.style.opacity = '0';
      } else if (camDist > 190) {
        const t = 1 - (camDist - 190) / 130;
        el.style.opacity = t.toFixed(2);
      } else {
        el.style.opacity = '1';
      }
      el.style.display = p.z > 1 ? 'none' : 'block';
    }

    function animate() {
      requestAnimationFrame(animate);

      if (controls) controls.update();

      // Subtle pulse on the internal lights
      const time = Date.now() * 0.002;
      if (c1UserLight) c1UserLight.intensity = 3.2 + Math.sin(time) * 0.4;
      if (c1AiLight) c1AiLight.intensity = 4.2 + Math.cos(time) * 0.5;
      if (c2UserLight) c2UserLight.intensity = 1.8 + Math.sin(time + 1) * 0.3;
      if (c2AiLight) c2AiLight.intensity = 2.2 + Math.cos(time + 1) * 0.3;

      if (c2BeaconMesh && c2BeaconMat) {
        const pulse = (Math.sin(time * 2.5) + 1) * 0.5;
        c2BeaconMesh.scale.set(1 + pulse * 0.3, 1 + pulse * 0.3, 1);
        c2BeaconMat.opacity = 0.65 - pulse * 0.45;
      }

      if (c2SlotTorus && c2SlotTorusMat) {
        const torusPulse = (Math.sin(time * 3.0) + 1) * 0.5;
        c2SlotTorus.scale.set(1 + torusPulse * 0.18, 1 + torusPulse * 0.18, 1 + torusPulse * 0.18);
        c2SlotTorusMat.opacity = 0.85 - torusPulse * 0.35;
      }

      // 1. Root Label Position
      if (rootLabelEl) {
        const rootAnchor = new THREE.Vector3(0, -17.5, 0);
        rootAnchor.applyMatrix4(rootGroup.matrixWorld);
        rootAnchor.project(camera);

        const rx = (rootAnchor.x * 0.5 + 0.5) * window.innerWidth;
        const ry = (-(rootAnchor.y * 0.5) + 0.5) * window.innerHeight;
        rootLabelEl.style.left = `${rx}px`;
        rootLabelEl.style.top = `${ry}px`;
        rootLabelEl.style.opacity = '1';
        rootLabelEl.style.display = rootAnchor.z > 1 ? 'none' : 'block';
      }

      // 2. Child 1 Label Position
      updateLabelPos(child1LabelEl, CHILD1_POS, 11.5);

      // 3. Child 2 Label Position
      updateLabelPos(child2LabelEl, CHILD2_POS, 8.5);

      renderer.render(scene, camera);
    }

    window.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
"""

    final_html = template.replace('__BUNDLED_CHATS_JSON__', json_str)
    out_path = 'design_pack/playground_3d.html'
    with open(out_path, 'w') as f:
        f.write(final_html)
    print(f"Updated 3D Universe View with 3 outcomes at {out_path} ({len(final_html)} bytes)")

if __name__ == '__main__':
    build_step2()
