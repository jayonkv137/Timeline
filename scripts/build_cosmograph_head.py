import os

def build():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace 3D · Cranial Surface Graph</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #050508;
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

    /* Pure Floating CosmoGraph Typography: Crisp, ethereal white, zero boxes */
    .cosmo-label {
      position: absolute;
      transform: translate(-50%, 0);
      pointer-events: auto;
      cursor: default;
      text-align: center;
      transition: opacity 0.2s ease;
      white-space: nowrap;
    }
    .cosmo-text {
      font-size: 15px;
      font-weight: 500;
      color: #ffffff;
      letter-spacing: -0.2px;
      text-shadow: 
        0 0 12px rgba(255, 255, 255, 0.9),
        0 0 24px rgba(255, 255, 255, 0.4),
        0 2px 10px rgba(0, 0, 0, 0.95);
    }

    /* Minimal Header */
    .top-hud {
      position: absolute;
      top: 24px; left: 28px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 4px;
      pointer-events: none;
    }
    .hud-title {
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .hud-title span {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      padding: 2px 7px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.12);
      color: #e2e8f0;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Controls Panel */
    .controls-panel {
      position: absolute;
      top: 24px; right: 28px;
      z-index: 10;
      background: rgba(10, 10, 16, 0.75);
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
      font-size: 10px;
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
    .toggle-switch.active { background: #ffffff; }
    .toggle-switch.active::after { transform: translateX(14px); background: #0f172a; }

    .bottom-hint {
      position: absolute;
      bottom: 24px; left: 28px;
      z-index: 10;
      font-size: 11px;
      color: #64748b;
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
    <div class="cosmo-label" id="root-label">
      <div class="cosmo-text">Course assignment strategy and deliverables</div>
    </div>
  </div>

  <div class="top-hud">
    <div class="hud-title">CoTrace 3D <span>CosmoGraph Surface Architecture</span></div>
  </div>

  <div class="controls-panel">
    <div class="panel-header">Display Controls</div>
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
    <div class="toggle-row" id="toggle-spin">
      <span>Auto-Rotation</span>
      <div class="toggle-switch" id="sw-spin"></div>
    </div>
  </div>

  <div class="bottom-hint">
    Left-click drag: <span>Rotate 3D Head</span> &nbsp;|&nbsp; Scroll: <span>Zoom</span>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    let scene, camera, renderer, controls;
    let headGroup, glassMesh, contoursGroup, meridiansGroup;
    let rootMarkerGroup, rootLight;
    let autoSpin = false;
    const labelEl = document.getElementById('root-label');

    // Surface Anchor Position on the Cranium/Forehead Surface
    // Located at (0, 19.5, 25.8) - directly on the anterior head surface
    const SURFACE_POINT = new THREE.Vector3(0, 19.5, 25.8);
    // Surface normal pointing outward (slightly tilted upward ~16 deg)
    const SURFACE_NORMAL = new THREE.Vector3(0, 0.28, 0.96).normalize();

    function init() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x050508, 0.0016);

      camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, 16, 125);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      document.getElementById('canvas-container').appendChild(renderer.domElement);

      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 30;
        controls.maxDistance = 450;
        controls.target.set(0, 12, 0);
      }

      // Studio Lighting for Translucent White Glass + CosmoGraph Atmospheric Radiance
      const ambient = new THREE.AmbientLight(0x1e293b, 1.2);
      scene.add(ambient);

      // Key light illuminating the contours
      const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
      keyLight.position.set(60, 90, 80);
      scene.add(keyLight);

      // Backlight for Fresnel rim glow
      const backLight = new THREE.DirectionalLight(0xffffff, 1.3);
      backLight.position.set(0, 50, -90);
      scene.add(backLight);

      // Soft white localized point light at the surface root marker
      rootLight = new THREE.PointLight(0xffffff, 3.2, 90);
      rootLight.position.copy(SURFACE_POINT).add(SURFACE_NORMAL.clone().multiplyScalar(4));
      scene.add(rootLight);

      // 1. Build the 3D Head Surface Shell
      buildCranialShell();

      // 2. Build the CosmoGraph Surface Node & Concentric/Radial Rings
      buildCosmoSurfaceNode();

      // Events
      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, 16, 125);
        if (controls) controls.target.set(0, 12, 0);
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

      // 1. Topographic Scanlines (White)
      contoursGroup = new THREE.Group();
      headGroup.add(contoursGroup);

      sliceRings.forEach((ring, idx) => {
        const loopPoints = [...ring, ring[0]];
        const loopGeo = new THREE.BufferGeometry().setFromPoints(loopPoints);
        const isKeyRing = idx % 3 === 0;
        const sliceMat = new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: isKeyRing ? 0.45 : 0.20
        });
        contoursGroup.add(new THREE.Line(loopGeo, sliceMat));
      });

      // 2. Cybernetic Meridians
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
          opacity: 0.14
        });
        meridiansGroup.add(new THREE.Line(mGeo, mMat));
      }

      // 3. Translucent Glossy White Shell
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
        roughness: 0.12,
        metalness: 0.05,
        transmission: 0.90,
        ior: 1.35,
        transparent: true,
        opacity: 0.18,
        clearcoat: 0.95,
        clearcoatRoughness: 0.08,
        side: THREE.DoubleSide
      });

      glassMesh = new THREE.Mesh(surfaceGeo, glassMat);
      headGroup.add(glassMesh);
    }

    function buildCosmoSurfaceNode() {
      rootMarkerGroup = new THREE.Group();
      rootMarkerGroup.position.copy(SURFACE_POINT);

      // Orient the marker group flush with the surface normal
      const defaultUp = new THREE.Vector3(0, 0, 1);
      const quat = new THREE.Quaternion().setFromUnitVectors(defaultUp, SURFACE_NORMAL);
      rootMarkerGroup.quaternion.copy(quat);

      headGroup.add(rootMarkerGroup);

      // A. THE GLOWING TRANSLUCENT WHITE CORE DISC/SPHERE
      // Radius = 5.2
      const coreGeo = new THREE.CylinderGeometry(5.2, 5.2, 0.8, 48);
      const coreMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: 0xffffff,
        emissiveIntensity: 0.95,
        roughness: 0.2,
        transparent: true,
        opacity: 0.90
      });
      const coreDisc = new THREE.Mesh(coreGeo, coreMat);
      coreDisc.rotation.x = Math.PI * 0.5;
      rootMarkerGroup.add(coreDisc);

      // Soft ethereal glow halo disc
      const haloGeo = new THREE.RingGeometry(5.0, 7.8, 48);
      const haloMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.40,
        side: THREE.DoubleSide
      });
      rootMarkerGroup.add(new THREE.Mesh(haloGeo, haloMat));

      // B. CONCENTRIC PROMINENT RINGS (Like CosmoGraph "planning")
      // Ring 1 (Inner resonant ring)
      const ring1Geo = new THREE.RingGeometry(8.8, 9.2, 64);
      const ringMat1 = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, side: THREE.DoubleSide });
      rootMarkerGroup.add(new THREE.Mesh(ring1Geo, ringMat1));

      // Ring 2 (Middle fine ring)
      const ring2Geo = new THREE.RingGeometry(12.5, 12.8, 64);
      const ringMat2 = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.65, side: THREE.DoubleSide });
      rootMarkerGroup.add(new THREE.Mesh(ring2Geo, ringMat2));

      // Ring 3 (Outer radar horizon ring)
      const ring3Geo = new THREE.RingGeometry(17.2, 17.5, 64);
      const ringMat3 = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.45, side: THREE.DoubleSide });
      rootMarkerGroup.add(new THREE.Mesh(ring3Geo, ringMat3));

      // C. RADIAL COORDINATE RAYS (Emanating outward across 360 degrees)
      const rayCount = 24;
      for (let r = 0; r < rayCount; r++) {
        const angle = (r / rayCount) * Math.PI * 2;
        const p1 = new THREE.Vector3(Math.cos(angle) * 5.4, Math.sin(angle) * 5.4, 0.1);
        const p2 = new THREE.Vector3(Math.cos(angle) * 23.5, Math.sin(angle) * 23.5, 0.1);

        const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const lineMat = new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: 0.32
        });
        rootMarkerGroup.add(new THREE.Line(lineGeo, lineMat));
      }
    }

    function setupToggles() {
      setupToggle('toggle-glass', 'sw-glass', (active) => { glassMesh.visible = active; });
      setupToggle('toggle-contours', 'sw-contours', (active) => { contoursGroup.visible = active; });
      setupToggle('toggle-grid', 'sw-grid', (active) => { meridiansGroup.visible = active; });
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
        headGroup.rotation.y += 0.003;
      }

      // Update Label Position: Anchored cleanly below the outer concentric ring
      if (labelEl) {
        // Offset below the surface point
        const offset = new THREE.Vector3(0, -18.5, 0);
        const labelPos = SURFACE_POINT.clone().add(offset);
        labelPos.applyMatrix4(headGroup.matrixWorld);
        labelPos.project(camera);

        const x = (labelPos.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-(labelPos.y * 0.5) + 0.5) * window.innerHeight;

        labelEl.style.left = `${x}px`;
        labelEl.style.top = `${y}px`;

        // Smooth distance fade (LOD)
        const camDist = camera.position.distanceTo(new THREE.Vector3(0, 14, 0));
        if (camDist > 340) {
          labelEl.style.opacity = '0';
        } else if (camDist > 220) {
          const t = 1 - (camDist - 220) / 120;
          labelEl.style.opacity = t.toFixed(2);
        } else {
          labelEl.style.opacity = '1';
        }

        if (labelPos.z > 1) {
          labelEl.style.display = 'none';
        } else {
          labelEl.style.display = 'block';
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
    print(f"CosmoGraph-style surface node built successfully: {out_path} ({len(html_content)} bytes)")

if __name__ == '__main__':
    build()
