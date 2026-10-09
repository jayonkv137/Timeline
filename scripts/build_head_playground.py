import os

def build_head():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace 3D · The Co-Creative Human-AI Cranial Canvas</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #07070a;
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
      padding: 3px 8px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.12);
      color: #f8fafc;
      border: 1px solid rgba(255, 255, 255, 0.25);
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
      background: rgba(15, 23, 42, 0.7);
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

  <!-- Top Brand -->
  <div class="top-hud">
    <div class="hud-title">CoTrace 3D Universe <span class="hud-badge">Cranial Shell Architecture</span></div>
    <div class="hud-desc">The conversational space re-imagined: a 3D translucent, glossy-white Human-AI cranial shell. The neutral white substrate where user (blue) and AI (orange) thoughts will spark and interconnect.</div>
  </div>

  <!-- Layers & Display Controls -->
  <div class="controls-panel">
    <div class="panel-header">3D Shell Layers</div>
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
    <div class="toggle-row" id="toggle-brain">
      <span>Inner Cranial Core Void</span>
      <div class="toggle-switch active" id="sw-brain"></div>
    </div>
    <div class="toggle-row" id="toggle-spin">
      <span>Auto-Rotation</span>
      <div class="toggle-switch active" id="sw-spin"></div>
    </div>
  </div>

  <!-- Bottom Controls -->
  <div class="bottom-hint">
    <div>Left-click drag: <span>Rotate 3D head 360°</span></div>
    <div>Scroll wheel: <span>Zoom into cranial cavity</span></div>
    <div>Right-click drag: <span>Pan position</span></div>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    let scene, camera, renderer, controls;
    let headGroup, glassMesh, contoursGroup, meridiansGroup, brainCavityGroup;
    let autoSpin = true;

    function init() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x07070a, 0.0018);

      camera = new THREE.PerspectiveCamera(46, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, 4, 150);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      document.getElementById('canvas-container').appendChild(renderer.domElement);

      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 35;
        controls.maxDistance = 500;
        controls.target.set(0, -2, 0);
      }

      // Lights: Studio rim lighting on translucent white glass
      const ambient = new THREE.AmbientLight(0x1e293b, 1.2);
      scene.add(ambient);

      // Key light from top-right
      const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
      keyLight.position.set(70, 90, 80);
      scene.add(keyLight);

      // Fill light from bottom-left (crisp white specular)
      const fillLight = new THREE.DirectionalLight(0xe2e8f0, 1.1);
      fillLight.position.set(-80, -40, -60);
      scene.add(fillLight);

      // Back rim light for dramatic silhouette
      const rimLight = new THREE.DirectionalLight(0xffffff, 1.4);
      rimLight.position.set(0, 60, -100);
      scene.add(rimLight);

      // Subtle internal core light inside the brain
      const brainLight = new THREE.PointLight(0xffffff, 1.5, 120);
      brainLight.position.set(0, 18, 0);
      scene.add(brainLight);

      // Build the 3D Human-AI Cranial Shell
      buildCranialShell();

      // Events
      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, 4, 150);
        if (controls) controls.target.set(0, -2, 0);
      });

      setupToggles();
      animate();
    }

    function buildCranialShell() {
      headGroup = new THREE.Group();
      headGroup.position.set(0, 0, 0);
      scene.add(headGroup);

      // 1. GENERATE THE ANATOMICAL HEAD CONTOUR SLICES
      const numSlices = 54;
      const pointsPerSlice = 64;
      const sliceRings = [];

      for (let i = 0; i < numSlices; i++) {
        const t = i / (numSlices - 1);
        const y = -50 + t * 96; // -50 (neck base) to +46 (top of skull)

        let rx, rz_f, rz_b, z_off;

        // Top Skull Dome
        if (y >= 28) {
          const norm = (y - 28) / 18;
          const r_scale = Math.sqrt(Math.max(0.001, 1 - norm * norm));
          rx = 22.0 * r_scale;
          rz_f = 23.5 * r_scale;
          rz_b = 26.5 * r_scale;
          z_off = -1.2 * norm;
        }
        // Forehead & Cranium
        else if (y >= 12) {
          const norm = (y - 12) / 16;
          rx = 22.5 + (1 - norm) * 1.5;
          rz_f = 24.5 + (1 - norm) * 1.5;
          rz_b = 27.5;
          z_off = 0.5;
        }
        // Brow & Eyes
        else if (y >= 1) {
          const norm = (y - 1) / 11;
          rx = 21.0 + norm * 2.0;
          rz_f = 24.0 + (1 - norm) * 2.5;
          rz_b = 26.5;
          z_off = 2.0;
        }
        // Nose & Cheeks
        else if (y >= -11) {
          rx = 18.5 + ((y + 11) / 12) * 2.5;
          rz_f = 23.0;
          rz_b = 24.5;
          z_off = 3.5;
        }
        // Mouth & Jaw
        else if (y >= -24) {
          const norm = (y + 24) / 13;
          rx = 14.5 + norm * 4.0;
          rz_f = 18.5 + norm * 4.5;
          rz_b = 20.0 + norm * 4.5;
          z_off = 2.5;
        }
        // Chin & Throat
        else if (y >= -36) {
          const norm = (y + 36) / 12;
          rx = 12.5 + norm * 2.0;
          rz_f = 13.0 + norm * 5.5;
          rz_b = 15.0 + norm * 5.0;
          z_off = -0.5;
        }
        // Neck Column
        else {
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

          // Facial feature sculpting on anterior face
          if (sinP > 0.2) {
            // Nose protrusion
            if (y >= -8 && y <= 3 && Math.abs(cosP) < 0.35) {
              const noseH = Math.exp(-Math.pow((y + 3.0) / 3.5, 2));
              const noseW = Math.exp(-Math.pow(cosP / 0.18, 2));
              featZ += noseH * noseW * 7.5;
            }
            // Eye socket recession
            if (y >= 3 && y <= 10 && Math.abs(cosP) >= 0.25 && Math.abs(cosP) <= 0.65) {
              const eyeH = Math.exp(-Math.pow((y - 6.5) / 2.5, 2));
              const eyeW = Math.exp(-Math.pow((Math.abs(cosP) - 0.42) / 0.15, 2));
              featZ -= eyeH * eyeW * 3.2;
            }
            // Cheekbones
            if (y >= -4 && y <= 4 && Math.abs(cosP) >= 0.45 && Math.abs(cosP) <= 0.85) {
              const cheek = Math.exp(-Math.pow(y / 3.0, 2)) * Math.exp(-Math.pow((Math.abs(cosP) - 0.65) / 0.18, 2));
              featZ += cheek * 2.2;
              featX += Math.sign(cosP) * cheek * 1.5;
            }
            // Lips
            if (y >= -14 && y <= -8 && Math.abs(cosP) < 0.4) {
              const lipH = Math.exp(-Math.pow((y + 11.0) / 2.0, 2));
              const lipW = Math.exp(-Math.pow(cosP / 0.22, 2));
              featZ += lipH * lipW * 3.0;
            }
            // Chin
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

      // 2. LAYER A: TOPOGRAPHIC SCANLINES (Reference Image 2)
      contoursGroup = new THREE.Group();
      headGroup.add(contoursGroup);

      const lineMat = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.52
      });

      sliceRings.forEach((ring, idx) => {
        // Vary opacity slightly to give optical depth
        const ringGeo = new THREE.BufferGeometry().setFromPoints(ring);
        // Connect back to start for closed loop
        const loopPoints = [...ring, ring[0]];
        const loopGeo = new THREE.BufferGeometry().setFromPoints(loopPoints);

        // Highlight key anatomical rings
        const isKeyRing = idx % 3 === 0;
        const sliceMat = new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: isKeyRing ? 0.65 : 0.32
        });
        const lineLoop = new THREE.Line(loopGeo, sliceMat);
        contoursGroup.add(lineLoop);
      });

      // 3. LAYER B: CYBERNETIC MERIDIAN GRID (Reference Image 4)
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
          opacity: 0.18
        });
        const mLine = new THREE.Line(mGeo, mMat);
        meridiansGroup.add(mLine);
      }

      // 4. LAYER C: TRANSLUCENT GLOSSY WHITE GLASS SHELL (Polygonal Skin)
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

          // Two triangles forming quad
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
        roughness: 0.12,
        metalness: 0.05,
        transmission: 0.88,
        ior: 1.35,
        transparent: true,
        opacity: 0.22,
        clearcoat: 0.95,
        clearcoatRoughness: 0.08,
        side: THREE.DoubleSide
      });

      glassMesh = new THREE.Mesh(surfaceGeo, glassMat);
      headGroup.add(glassMesh);

      // 5. LAYER D: INNER CRANIAL VOID / BRAIN CORE
      // The internal volume where blue (user) and orange (AI) thoughts will spark
      brainCavityGroup = new THREE.Group();
      headGroup.add(brainCavityGroup);

      // Delicate inner cranial hemisphere lattice
      const brainGeo = new THREE.IcosahedronGeometry(13.5, 3);
      const brainMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        wireframe: true,
        transparent: true,
        opacity: 0.15
      });
      const brainWire = new THREE.Mesh(brainGeo, brainMat);
      brainWire.position.set(0, 18, -1);
      brainCavityGroup.add(brainWire);

      // Ambient neural particle dust in the cerebrum
      const particleCount = 200;
      const particlePos = new Float32Array(particleCount * 3);
      for (let p = 0; p < particleCount * 3; p += 3) {
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        const r = Math.cbrt(Math.random()) * 11.5;
        particlePos[p] = r * Math.sin(phi) * Math.cos(theta);
        particlePos[p + 1] = 18 + r * Math.sin(phi) * Math.sin(theta) * 0.85;
        particlePos[p + 2] = -1 + r * Math.cos(phi);
      }
      const particleGeo = new THREE.BufferGeometry();
      particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
      const particleMat = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 1.2,
        transparent: true,
        opacity: 0.5
      });
      const brainDust = new THREE.Points(particleGeo, particleMat);
      brainCavityGroup.add(brainDust);
    }

    function setupToggles() {
      setupToggle('toggle-glass', 'sw-glass', (active) => { glassMesh.visible = active; });
      setupToggle('toggle-contours', 'sw-contours', (active) => { contoursGroup.visible = active; });
      setupToggle('toggle-grid', 'sw-grid', (active) => { meridiansGroup.visible = active; });
      setupToggle('toggle-brain', 'sw-brain', (active) => { brainCavityGroup.visible = active; });
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
    print(f"Cranial Head Shell built successfully: {out_path} ({len(html_content)} bytes)")

if __name__ == '__main__':
    build_head()
