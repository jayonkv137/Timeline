import json
import os

def build_step_1():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace 3D · Step 1: The Root Goal</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #0a0a0f;
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

    /* Pure Obsidian-style floating label: zero pill background, zero border */
    .obsidian-floating-label {
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
      font-size: 9px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #f472b6;
      opacity: 0.85;
      margin-bottom: 3px;
      text-shadow: 0 0 12px rgba(244, 114, 182, 0.6);
    }
    .main-text {
      font-size: 13px;
      font-weight: 500;
      color: #f8fafc;
      letter-spacing: -0.2px;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.9), 0 0 20px rgba(10, 10, 15, 0.8);
      max-width: 320px;
      line-height: 1.35;
    }

    /* Minimal Top HUD */
    .top-hud {
      position: absolute;
      top: 20px; left: 24px;
      z-index: 10;
      display: flex;
      flex-direction: column;
      gap: 6px;
      pointer-events: none;
    }
    .hud-title {
      font-size: 14px;
      font-weight: 700;
      color: #f8fafc;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .hud-step-badge {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 8px;
      border-radius: 9999px;
      background: rgba(244, 114, 182, 0.2);
      color: #f472b6;
      border: 1px solid rgba(244, 114, 182, 0.4);
    }
    .hud-desc {
      font-size: 12px;
      color: #94a3b8;
      max-width: 360px;
      line-height: 1.4;
    }

    /* Controls HUD */
    .controls-hint {
      position: absolute;
      bottom: 24px; left: 24px;
      z-index: 10;
      font-size: 11px;
      color: #64748b;
      display: flex;
      flex-direction: column;
      gap: 4px;
      pointer-events: none;
    }
    .controls-hint span {
      color: #94a3b8;
    }

    .btn-reset-view {
      position: absolute;
      bottom: 24px; right: 24px;
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
    <div class="obsidian-floating-label" id="root-label">
      <div class="kicker">ROOT GOAL · ORIGIN U(1,1)</div>
      <div class="main-text">Course assignment strategy and deliverables</div>
    </div>
  </div>

  <div class="top-hud">
    <div class="hud-title">CoTrace 3D Canvas <span class="hud-step-badge">Step 1: Root Goal Origin</span></div>
    <div class="hud-desc">Blank canvas initialized. Only the central origin goal is established at (0, 0, 0) with celestial coordinate rings.</div>
  </div>

  <div class="controls-hint">
    <div>Left-click drag: <span>Rotate 3D space</span></div>
    <div>Scroll: <span>Zoom in / out</span></div>
    <div>Right-click drag: <span>Pan camera</span></div>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    let scene, camera, renderer, controls;
    let rootSphere, innerCore, ringsGroup, raysGroup;
    const labelEl = document.getElementById('root-label');

    function init() {
      // Scene with cosmic depth fog
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x0a0a0f, 0.002);

      // Camera
      camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, -10, 110);

      // Renderer
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      document.getElementById('canvas-container').appendChild(renderer.domElement);

      // OrbitControls with smooth damping
      if (typeof THREE.OrbitControls !== 'undefined') {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.minDistance = 25;
        controls.maxDistance = 450;
      }

      // Lights
      const ambient = new THREE.AmbientLight(0x2d1b38, 1.2);
      scene.add(ambient);

      const topLight = new THREE.DirectionalLight(0xffffff, 1.0);
      topLight.position.set(40, 80, 60);
      scene.add(topLight);

      // Center point light matching sphere hue for realistic local lighting
      const coreLight = new THREE.PointLight(0xf472b6, 2.8, 180);
      coreLight.position.set(0, 0, 0);
      scene.add(coreLight);

      // Build the Step 1 celestial origin
      createRootOrigin();

      // Events
      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, -10, 110);
        if (controls) controls.target.set(0, 0, 0);
      });

      animate();
    }

    function createRootOrigin() {
      const rootGroup = new THREE.Group();
      rootGroup.name = "rootGroup";
      scene.add(rootGroup);

      // 1. OUTER TRANSLUCENT SPHERE (Volumetric 3D Glass / Energy)
      // Radius = 13.5
      const sphereGeo = new THREE.SphereGeometry(13.5, 64, 64);
      const outerMat = new THREE.MeshPhysicalMaterial({
        color: 0xf472b6,
        emissive: 0xdb2777,
        emissiveIntensity: 0.55,
        roughness: 0.12,
        metalness: 0.1,
        transparent: true,
        opacity: 0.72,
        transmission: 0.35,
        ior: 1.35,
        clearcoat: 0.8,
        clearcoatRoughness: 0.1
      });
      rootSphere = new THREE.Mesh(sphereGeo, outerMat);
      rootGroup.add(rootSphere);

      // 2. INNER LUMINOUS NUCLEUS (Gives internal volumetric light)
      const coreGeo = new THREE.SphereGeometry(9.0, 32, 32);
      const coreMat = new THREE.MeshStandardMaterial({
        color: 0xfbcfe8,
        emissive: 0xf472b6,
        emissiveIntensity: 0.9,
        roughness: 0.3,
        transparent: true,
        opacity: 0.85
      });
      innerCore = new THREE.Mesh(coreGeo, coreMat);
      rootGroup.add(innerCore);

      // 3. CONCENTRIC CELESTIAL RINGS (Astrolabe / Origin Coordinates)
      ringsGroup = new THREE.Group();
      rootGroup.add(ringsGroup);

      // Ring 1 (Inner equatorial ring)
      const ring1Geo = new THREE.TorusGeometry(19.0, 0.22, 16, 128);
      const ring1Mat = new THREE.MeshStandardMaterial({
        color: 0xf472b6,
        emissive: 0xf472b6,
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.85
      });
      const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
      ringsGroup.add(ring1);

      // Ring 2 (Middle delicate ring)
      const ring2Geo = new THREE.TorusGeometry(26.5, 0.16, 16, 128);
      const ring2Mat = new THREE.MeshStandardMaterial({
        color: 0xf472b6,
        emissive: 0xec4899,
        emissiveIntensity: 0.6,
        transparent: true,
        opacity: 0.65
      });
      const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
      ringsGroup.add(ring2);

      // Ring 3 (Outer subtle horizon ring)
      const ring3Geo = new THREE.TorusGeometry(36.0, 0.12, 16, 128);
      const ring3Mat = new THREE.MeshStandardMaterial({
        color: 0xa855f7,
        emissive: 0x8b5cf6,
        emissiveIntensity: 0.4,
        transparent: true,
        opacity: 0.45
      });
      const ring3 = new THREE.Mesh(ring3Geo, ring3Mat);
      ringsGroup.add(ring3);

      // Slight tilt on rings to showcase 3D depth
      ringsGroup.rotation.x = Math.PI * 0.18;
      ringsGroup.rotation.y = Math.PI * 0.08;

      // 4. RADIAL COORDINATE RAYS (Faint lines radiating outward like an origin chart)
      raysGroup = new THREE.Group();
      rootGroup.add(raysGroup);

      const rayCount = 16;
      for (let i = 0; i < rayCount; i++) {
        const angle = (i / rayCount) * Math.PI * 2;
        const p1 = new THREE.Vector3(Math.cos(angle) * 14.5, Math.sin(angle) * 14.5, 0);
        const p2 = new THREE.Vector3(Math.cos(angle) * 65.0, Math.sin(angle) * 65.0, 0);
        
        const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const lineMat = new THREE.LineBasicMaterial({
          color: 0xf472b6,
          transparent: true,
          opacity: 0.16
        });
        const rayLine = new THREE.Line(lineGeo, lineMat);
        raysGroup.add(rayLine);
      }
      raysGroup.rotation.copy(ringsGroup.rotation);

      // 5. SUBTLE CELESTIAL BACKGROUND PARTICLES (Depth cues)
      const starGeo = new THREE.BufferGeometry();
      const starCount = 350;
      const starPositions = new Float32Array(starCount * 3);
      for (let i = 0; i < starCount * 3; i += 3) {
        starPositions[i] = (Math.random() - 0.5) * 600;
        starPositions[i + 1] = (Math.random() - 0.5) * 600;
        starPositions[i + 2] = (Math.random() - 0.5) * 600;
      }
      starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
      const starMat = new THREE.PointsMaterial({
        color: 0xe0e7ff,
        size: 1.2,
        transparent: true,
        opacity: 0.4
      });
      const stars = new THREE.Points(starGeo, starMat);
      scene.add(stars);
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
      requestAnimationFrame(animate);

      if (controls) controls.update();

      // Gentle celestial idle rotation
      if (ringsGroup) {
        ringsGroup.rotation.z += 0.0015;
      }
      if (raysGroup) {
        raysGroup.rotation.z += 0.0015;
      }
      if (rootSphere) {
        rootSphere.rotation.y += 0.0025;
      }

      // Update Obsidian floating label position (anchored below the sphere and rings)
      if (labelEl && rootSphere) {
        const anchorPos = new THREE.Vector3(0, -22.5, 0);
        anchorPos.project(camera);

        const x = (anchorPos.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-(anchorPos.y * 0.5) + 0.5) * window.innerHeight;

        labelEl.style.left = `${x}px`;
        labelEl.style.top = `${y}px`;

        // Smooth distance fade based on camera distance (Obsidian LOD curve)
        const camDist = camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
        if (camDist > 320) {
          labelEl.style.opacity = '0';
        } else if (camDist > 200) {
          const t = 1 - (camDist - 200) / 120;
          labelEl.style.opacity = t.toFixed(2);
        } else {
          labelEl.style.opacity = '1';
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
    print(f"Step 1 applied successfully: {out_path} ({len(html_content)} bytes)")

if __name__ == '__main__':
    build_step_1()
