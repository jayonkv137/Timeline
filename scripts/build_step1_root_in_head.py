import os

def build():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace 3D · Root Goal in Cranial Canvas</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #060609;
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

    /* Enhanced Obsidian Floating Typography: Zero pill background, high readability */
    .obsidian-label {
      position: absolute;
      transform: translate(-50%, 0);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      pointer-events: auto;
      cursor: default;
      transition: opacity 0.25s ease;
    }
    .kicker {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.8px;
      color: #38bdf8;
      margin-bottom: 4px;
      text-shadow: 0 0 14px rgba(56, 189, 248, 0.8), 0 2px 6px rgba(0,0,0,0.9);
    }
    .main-goal-title {
      font-size: 16px;
      font-weight: 600;
      color: #ffffff;
      letter-spacing: -0.3px;
      text-shadow: 
        0 2px 14px rgba(0, 0, 0, 1),
        0 0 24px rgba(6, 6, 9, 0.95),
        0 0 6px rgba(0, 0, 0, 0.9);
      max-width: 380px;
      line-height: 1.35;
    }
    .goal-meta {
      font-size: 11px;
      color: #94a3b8;
      margin-top: 4px;
      font-weight: 400;
      text-shadow: 0 2px 8px rgba(0, 0, 0, 0.9);
    }

    /* Top HUD */
    .top-hud {
      position: absolute;
      top: 24px; left: 28px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 6px;
      pointer-events: none;
    }
    .hud-title {
      font-size: 15px;
      font-weight: 700;
      color: #f8fafc;
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .hud-badge {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 3px 9px;
      border-radius: 9999px;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.35);
    }
    .hud-desc {
      font-size: 12px;
      color: #94a3b8;
      max-width: 440px;
      line-height: 1.45;
    }

    /* Controls Panel */
    .controls-panel {
      position: absolute;
      top: 24px; right: 28px;
      z-index: 10;
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 14px;
      padding: 12px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .panel-header {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: #64748b;
    }
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      font-size: 12px;
      color: #cbd5e1;
      cursor: pointer;
    }
    .toggle-row:hover { color: #fff; }
    .toggle-switch {
      width: 32px; height: 18px;
      background: #334155;
      border-radius: 9999px;
      position: relative;
      transition: background 0.2s;
    }
    .toggle-switch::after {
      content: '';
      position: absolute;
      top: 2px; left: 2px;
      width: 14px; height: 14px;
      border-radius: 50%;
      background: #fff;
      transition: transform 0.2s;
    }
    .toggle-switch.active { background: #38bdf8; }
    .toggle-switch.active::after { transform: translateX(14px); }

    /* Bottom Info */
    .bottom-hint {
      position: absolute;
      bottom: 24px; left: 28px;
      z-index: 10;
      font-size: 11px;
      color: #64748b;
      display: flex;
      flex-direction: column;
      gap: 4px;
      pointer-events: none;
    }
    .bottom-hint span { color: #94a3b8; }

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
    <div class="obsidian-label" id="root-label">
      <div class="kicker">ROOT GOAL · ORIGIN U(1,1)</div>
      <div class="main-goal-title">Course assignment strategy and deliverables</div>
      <div class="goal-meta">outcome 1 · Established at Turn U(1,1)</div>
    </div>
  </div>

  <div class="top-hud">
    <div class="hud-title">CoTrace 3D Universe <span class="hud-badge">Step 1: Root Goal Origin</span></div>
    <div class="hud-desc">The central conversation anchor (outcome 1) placed in the cranial brain cavity of the neutral 3D white human-AI head shell.</div>
  </div>

  <div class="controls-panel">
    <div class="panel-header">3D Cranial Layers</div>
    <div class="toggle-row" id="toggle-glass">
      <span>Glossy Translucent Shell</span>
      <div class="toggle-switch active" id="sw-glass"></div>
    </div>
    <div class="toggle-row" id="toggle-contours">
      <span>Topographic Scanlines</span>
      <div class="toggle-switch active" id="sw-contours"></div>
    </div>
    <div class="toggle-row" id="toggle-grid">
      <span>Cybernetic Meridians</span>
      <div class="toggle-switch active" id="sw-grid"></div>
    </div>
    <div class="toggle-row" id="toggle-root">
      <span>Root Goal Sphere & Rings</span>
      <div class="toggle-switch active" id="sw-root"></div>
    </div>
    <div class="toggle-row" id="toggle-spin">
      <span>Auto-Rotation</span>
      <div class="toggle-switch active" id="sw-spin"></div>
    </div>
  </div>

  <div class="bottom-hint">
    <div>Left-click drag: <span>Rotate 3D head & core</span></div>
    <div>Scroll wheel: <span>Zoom into cranial cavity</span></div>
    <div>Right-click drag: <span>Pan view</span></div>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    let scene, camera, renderer, controls;
    let headGroup, glassMesh, contoursGroup, meridiansGroup;
    let rootGroup, rootSphere, rootRingsGroup;
    let autoSpin = true;
    const labelEl = document.getElementById('root-label');

    // Root Goal Position inside the cranium (cerebral brain cavity)
    const ROOT_POS = new THREE.Vector3(0, 16.0, 0);

    function init() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x060609, 0.0016);

      camera = new THREE.PerspectiveCamera(46, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, 14, 135);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      document.getElementById('canvas-container').appendChild(renderer.domElement);

      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 25;
        controls.maxDistance = 450;
        controls.target.set(0, 8, 0);
      }

      // Lights: Neutral white studio lighting for the head shell + localized glow for root goal
      const ambient = new THREE.AmbientLight(0x1e293b, 1.2);
      scene.add(ambient);

      const keyLight = new THREE.DirectionalLight(0xffffff, 1.7);
      keyLight.position.set(70, 90, 80);
      scene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0xe2e8f0, 1.1);
      fillLight.position.set(-80, -40, -60);
      scene.add(fillLight);

      const rimLight = new THREE.DirectionalLight(0xffffff, 1.4);
      rimLight.position.set(0, 60, -100);
      scene.add(rimLight);

      // Root Goal Point Light: casts soft celestial blue radiance from inside the cranium
      const rootLight = new THREE.PointLight(0x38bdf8, 2.8, 160);
      rootLight.position.copy(ROOT_POS);
      scene.add(rootLight);

      // 1. Build the 3D Cranial Shell
      buildCranialShell();

      // 2. Build the Root Goal Node inside the Cranium
      buildRootGoalNode();

      // Events
      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, 14, 135);
        if (controls) controls.target.set(0, 8, 0);
      });

      setupToggles();
      animate();
    }

    function buildCranialShell() {
      headGroup = new THREE.Group();
      scene.add(headGroup);

      const numSlices = 54;
      const pointsPerSlice = 64;
      const sliceRings = [];

      for (let i = 0; i < numSlices; i++) {
        const t = i / (numSlices - 1);
        const y = -50 + t * 96;

        let rx, rz_f, rz_b, z_off;

        if (y >= 28) {
          const norm = (y - 28) / 18;
          const r_scale = Math.sqrt(Math.max(0.001, 1 - norm * norm));
          rx = 22.0 * r_scale;
          rz_f = 23.5 * r_scale;
          rz_b = 26.5 * r_scale;
          z_off = -1.2 * norm;
        } else if (y >= 12) {
          const norm = (y - 12) / 16;
          rx = 22.5 + (1 - norm) * 1.5;
          rz_f = 24.5 + (1 - norm) * 1.5;
          rz_b = 27.5;
          z_off = 0.5;
        } else if (y >= 1) {
          const norm = (y - 1) / 11;
          rx = 21.0 + norm * 2.0;
          rz_f = 24.0 + (1 - norm) * 2.5;
          rz_b = 26.5;
          z_off = 2.0;
        } else if (y >= -11) {
          rx = 18.5 + ((y + 11) / 12) * 2.5;
          rz_f = 23.0;
          rz_b = 24.5;
          z_off = 3.5;
        } else if (y >= -24) {
          const norm = (y + 24) / 13;
          rx = 14.5 + norm * 4.0;
          rz_f = 18.5 + norm * 4.5;
          rz_b = 20.0 + norm * 4.5;
          z_off = 2.5;
        } else if (y >= -36) {
          const norm = (y + 36) / 12;
          rx = 12.5 + norm * 2.0;
          rz_f = 13.0 + norm * 5.5;
          rz_b = 15.0 + norm * 5.0;
          z_off = -0.5;
        } else {
          const norm = (y + 50) / 14;
          rx = 15.0 - norm * 2.5;
          rz_f = 16.0 - norm * 3.0;
          rz_b = 17.5 - norm * 2.5;
          z_off = -3.5;
        }

        const ring = [];
        for (let j = 0; j < pointsPerSlice; j++) {
          const phi = (j / pointsPerSlice) * Math.PI * 2;
          const cosP = Math.cos(phi);
          const sinP = Math.sin(phi);
          const rz = sinP >= 0 ? rz_f : rz_b;

          let featZ = 0;
          let featX = 0;

          if (sinP > 0.2) {
            if (y >= -8 && y <= 3 && Math.abs(cosP) < 0.35) {
              const noseH = Math.exp(-Math.pow((y + 3.0) / 3.5, 2));
              const noseW = Math.exp(-Math.pow(cosP / 0.18, 2));
              featZ += noseH * noseW * 7.5;
            }
            if (y >= 3 && y <= 10 && Math.abs(cosP) >= 0.25 && Math.abs(cosP) <= 0.65) {
              const eyeH = Math.exp(-Math.pow((y - 6.5) / 2.5, 2));
              const eyeW = Math.exp(-Math.pow((Math.abs(cosP) - 0.42) / 0.15, 2));
              featZ -= eyeH * eyeW * 3.2;
            }
            if (y >= -4 && y <= 4 && Math.abs(cosP) >= 0.45 && Math.abs(cosP) <= 0.85) {
              const cheek = Math.exp(-Math.pow(y / 3.0, 2)) * Math.exp(-Math.pow((Math.abs(cosP) - 0.65) / 0.18, 2));
              featZ += cheek * 2.2;
              featX += Math.sign(cosP) * cheek * 1.5;
            }
            if (y >= -14 && y <= -8 && Math.abs(cosP) < 0.4) {
              const lipH = Math.exp(-Math.pow((y + 11.0) / 2.0, 2));
              const lipW = Math.exp(-Math.pow(cosP / 0.22, 2));
              featZ += lipH * lipW * 3.0;
            }
            if (y >= -23 && y <= -16 && Math.abs(cosP) < 0.45) {
              const chinH = Math.exp(-Math.pow((y + 19.5) / 2.5, 2));
              const chinW = Math.exp(-Math.pow(cosP / 0.25, 2));
              featZ += chinH * chinW * 4.2;
            }
          }

          const px = (rx + featX) * cosP;
          const pz = (rz + featZ) * sinP + z_off;
          const py = y;
          ring.push(new THREE.Vector3(px, py, pz));
        }
        sliceRings.push(ring);
      }

      // Topographic Contours (White Scanlines)
      contoursGroup = new THREE.Group();
      headGroup.add(contoursGroup);

      sliceRings.forEach((ring, idx) => {
        const loopPoints = [...ring, ring[0]];
        const loopGeo = new THREE.BufferGeometry().setFromPoints(loopPoints);
        const isKeyRing = idx % 3 === 0;
        const sliceMat = new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: isKeyRing ? 0.55 : 0.25
        });
        const lineLoop = new THREE.Line(loopGeo, sliceMat);
        contoursGroup.add(lineLoop);
      });

      // Cybernetic Meridians
      meridiansGroup = new THREE.Group();
      headGroup.add(meridiansGroup);

      const numMeridians = 18;
      for (let m = 0; m < numMeridians; m++) {
        const ptIdx = Math.floor((m / numMeridians) * pointsPerSlice);
        const meridianPoints = [];
        for (let i = 0; i < numSlices; i++) {
          meridianPoints.push(sliceRings[i][ptIdx]);
        }
        const mGeo = new THREE.BufferGeometry().setFromPoints(meridianPoints);
        const mMat = new THREE.LineBasicMaterial({
          color: 0xe2e8f0,
          transparent: true,
          opacity: 0.16
        });
        meridiansGroup.add(new THREE.Line(mGeo, mMat));
      }

      // Translucent Glossy White Glass Shell
      const vertArray = [];
      const indexArray = [];

      for (let i = 0; i < numSlices; i++) {
        for (let j = 0; j < pointsPerSlice; j++) {
          const pt = sliceRings[i][j];
          vertArray.push(pt.x, pt.y, pt.z);
        }
      }

      for (let i = 0; i < numSlices - 1; i++) {
        for (let j = 0; j < pointsPerSlice; j++) {
          const nextJ = (j + 1) % pointsPerSlice;
          const a = i * pointsPerSlice + j;
          const b = (i + 1) * pointsPerSlice + j;
          const c = (i + 1) * pointsPerSlice + nextJ;
          const d = i * pointsPerSlice + nextJ;
          indexArray.push(a, b, d);
          indexArray.push(b, c, d);
        }
      }

      const surfaceGeo = new THREE.BufferGeometry();
      surfaceGeo.setAttribute('position', new THREE.Float32BufferAttribute(vertArray, 3));
      surfaceGeo.setIndex(indexArray);
      surfaceGeo.computeVertexNormals();

      const glassMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        roughness: 0.1,
        metalness: 0.05,
        transmission: 0.88,
        ior: 1.35,
        transparent: true,
        opacity: 0.20,
        clearcoat: 0.95,
        clearcoatRoughness: 0.08,
        side: THREE.DoubleSide
      });

      glassMesh = new THREE.Mesh(surfaceGeo, glassMat);
      headGroup.add(glassMesh);
    }

    function buildRootGoalNode() {
      rootGroup = new THREE.Group();
      rootGroup.position.copy(ROOT_POS);
      headGroup.add(rootGroup);

      // 1. OUTER TRANSLUCENT GLOWING ROOT SPHERE
      // Radius = 9.5
      const sphereGeo = new THREE.SphereGeometry(9.5, 48, 48);
      const outerMat = new THREE.MeshPhysicalMaterial({
        color: 0x38bdf8,
        emissive: 0x0284c7,
        emissiveIntensity: 0.75,
        roughness: 0.12,
        metalness: 0.1,
        transparent: true,
        opacity: 0.82,
        transmission: 0.35,
        clearcoat: 0.9,
        clearcoatRoughness: 0.1
      });
      rootSphere = new THREE.Mesh(sphereGeo, outerMat);
      rootGroup.add(rootSphere);

      // 2. INNER LUMINOUS NUCLEUS
      const coreGeo = new THREE.SphereGeometry(6.2, 32, 32);
      const coreMat = new THREE.MeshStandardMaterial({
        color: 0xe0f2fe,
        emissive: 0x38bdf8,
        emissiveIntensity: 1.0,
        roughness: 0.2,
        transparent: true,
        opacity: 0.9
      });
      const coreSphere = new THREE.Mesh(coreGeo, coreMat);
      rootGroup.add(coreSphere);

      // 3. CONCENTRIC CELESTIAL ORIGIN RINGS (Astrolabe / Coordinate Origin)
      rootRingsGroup = new THREE.Group();
      rootGroup.add(rootRingsGroup);

      // Ring 1 (Inner equatorial ring)
      const ring1Geo = new THREE.TorusGeometry(14.0, 0.24, 16, 96);
      const ring1Mat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x38bdf8,
        emissiveIntensity: 0.85,
        transparent: true,
        opacity: 0.85
      });
      rootRingsGroup.add(new THREE.Mesh(ring1Geo, ring1Mat));

      // Ring 2 (Middle celestial ring)
      const ring2Geo = new THREE.TorusGeometry(19.5, 0.18, 16, 96);
      const ring2Mat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        emissive: 0x0ea5e9,
        emissiveIntensity: 0.6,
        transparent: true,
        opacity: 0.65
      });
      rootRingsGroup.add(new THREE.Mesh(ring2Geo, ring2Mat));

      // Ring 3 (Outer delicate horizon ring)
      const ring3Geo = new THREE.TorusGeometry(26.0, 0.14, 16, 96);
      const ring3Mat = new THREE.MeshStandardMaterial({
        color: 0x818cf8,
        emissive: 0x6366f1,
        emissiveIntensity: 0.45,
        transparent: true,
        opacity: 0.45
      });
      rootRingsGroup.add(new THREE.Mesh(ring3Geo, ring3Mat));

      // Coordinate rays radiating softly into the skull
      const rayCount = 12;
      for (let r = 0; r < rayCount; r++) {
        const angle = (r / rayCount) * Math.PI * 2;
        const p1 = new THREE.Vector3(Math.cos(angle) * 10.5, Math.sin(angle) * 10.5, 0);
        const p2 = new THREE.Vector3(Math.cos(angle) * 38.0, Math.sin(angle) * 38.0, 0);
        const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const lineMat = new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.22
        });
        rootRingsGroup.add(new THREE.Line(lineGeo, lineMat));
      }

      // Tilt rings slightly for 3D orbital depth
      rootRingsGroup.rotation.x = Math.PI * 0.18;
      rootRingsGroup.rotation.y = Math.PI * 0.08;
    }

    function setupToggles() {
      setupToggle('toggle-glass', 'sw-glass', (active) => { glassMesh.visible = active; });
      setupToggle('toggle-contours', 'sw-contours', (active) => { contoursGroup.visible = active; });
      setupToggle('toggle-grid', 'sw-grid', (active) => { meridiansGroup.visible = active; });
      setupToggle('toggle-root', 'sw-root', (active) => { 
        rootGroup.visible = active;
        labelEl.style.display = active ? 'flex' : 'none';
      });
      setupToggle('toggle-spin', 'sw-spin', (active) => { autoSpin = active; });
    }

    function setupToggle(rowId, swId, callback) {
      const row = document.getElementById(rowId);
      const sw = document.getElementById(swId);
      row.addEventListener('click', () => {
        const isActive = sw.classList.toggle('active');
        callback(isActive);
      });
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
      requestAnimationFrame(animate);

      if (controls) controls.update();

      if (autoSpin && headGroup) {
        headGroup.rotation.y += 0.0035;
      }

      // Gentle internal rings orbit
      if (rootRingsGroup) {
        rootRingsGroup.rotation.z += 0.002;
      }

      // Update High-Readability Obsidian Floating Label
      if (labelEl && rootSphere) {
        // Project 3D anchor position just below the root node and rings
        const anchor = new THREE.Vector3(0, ROOT_POS.y - 14.5, 0);
        // Transform by headGroup rotation so text tracks with the head
        anchor.applyMatrix4(headGroup.matrixWorld);
        anchor.project(camera);

        const x = (anchor.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-(anchor.y * 0.5) + 0.5) * window.innerHeight;

        labelEl.style.left = `${x}px`;
        labelEl.style.top = `${y}px`;

        // Smooth distance fade based on camera distance (Obsidian LOD)
        const camDist = camera.position.distanceTo(new THREE.Vector3(0, 14, 0));
        if (camDist > 340) {
          labelEl.style.opacity = '0';
        } else if (camDist > 220) {
          const t = 1 - (camDist - 220) / 120;
          labelEl.style.opacity = t.toFixed(2);
        } else {
          labelEl.style.opacity = '1';
        }

        // Hide if behind camera
        if (anchor.z > 1) {
          labelEl.style.display = 'none';
        } else {
          labelEl.style.display = 'flex';
        }
      }

      renderer.render(scene, camera);
    }

    window.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
"""
    out_path = 'design_pack/playground_3d.html'
    with open(out_path, 'w') as f:
        f.write(html_content)
    print(f"Step 1 with Cranial Shell and Root Node built: {out_path} ({len(html_content)} bytes)")

if __name__ == '__main__':
    build()
