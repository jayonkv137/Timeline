import json
import os

def build_root_studio():
    # Load sample chats for dropdown infrastructure
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
  <title>CoTrace 3D · Root Goal Anchor</title>
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

    /* Authentic Obsidian Floating Label: ALWAYS VISIBLE across all zoom levels */
    .obsidian-root-label {
      position: absolute;
      transform: translate(-50%, 0);
      pointer-events: auto;
      cursor: default;
      text-align: center;
      white-space: nowrap;
      z-index: 5;
    }
    .root-text {
      font-size: 15px;
      font-weight: 500;
      color: #ffffff;
      letter-spacing: -0.2px;
      text-shadow: 
        0 0 16px rgba(255, 255, 255, 0.9),
        0 0 32px rgba(255, 255, 255, 0.45),
        0 2px 10px rgba(0, 0, 0, 0.95);
      transition: font-size 0.15s ease;
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
      max-width: 420px;
      line-height: 1.4;
    }

    .stats-box {
      pointer-events: auto;
      background: rgba(10, 10, 16, 0.75);
      backdrop-filter: blur(16px);
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
    .stat-val { font-size: 14px; font-weight: 700; color: #ffffff; }
    .mode-pill {
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(255, 255, 255, 0.12);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.25);
    }

    /* Bottom Timeline Bar */
    .bottom-bar {
      position: absolute;
      bottom: 24px; left: 50%;
      transform: translateX(-50%);
      width: min(92%, 760px);
      background: rgba(10, 10, 16, 0.82);
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
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pair-badge .current-pair-txt {
      color: #ffffff;
      text-shadow: 0 0 10px rgba(255, 255, 255, 0.6);
    }
    .step-indicator {
      font-size: 11px;
      color: #94a3b8;
    }

    /* Controls Bottom Right */
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
    <div class="obsidian-root-label" id="root-label">
      <div class="root-text" id="root-text-el">Course assignment strategy and deliverables</div>
    </div>
  </div>

  <div class="top-bar">
    <div class="brand-box">
      <div class="brand-title">CoTrace 3D Universe <span>Root Origin Studio</span></div>
      <div class="brand-desc">Only the starting Root Goal sphere is present: a glowing translucent white sphere radiating outward. Ready to be populated pair by pair.</div>
    </div>

    <div class="stats-box">
      <div class="stat-item">
        <div class="stat-label">Origin State</div>
        <div class="mode-pill">PAIR 1 ESTABLISHED</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Root Mass</div>
        <div class="stat-val">237.0</div>
      </div>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="timeline-header">
      <div class="pair-badge">
        <span>Active State:</span>
        <span class="current-pair-txt">Starting Root Goal Anchor</span>
      </div>
      <div class="step-indicator">Step 1 of Architecture · Clean Stage</div>
    </div>
  </div>

  <button class="btn-reset-view" id="btn-reset">⟲ Reset Camera</button>

  <script>
    const BUNDLED_CHATS = __BUNDLED_CHATS_JSON__;
    const currentChat = BUNDLED_CHATS['c05_research_medium'];

    let scene, camera, renderer, controls;
    let rootGroup, rootSphere, haloMesh1, haloMesh2, radialRaysGroup;
    const labelEl = document.getElementById('root-label');
    const textEl = document.getElementById('root-text-el');

    const ROOT_ORIGIN = new THREE.Vector3(0, 0, 0);

    function init() {
      scene = new THREE.Scene();
      scene.fog = new THREE.FogExp2(0x06060a, 0.0016);

      camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1500);
      camera.position.set(0, 0, 110);

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
        controls.target.copy(ROOT_ORIGIN);
      }

      // Lights: High-end Studio Lighting for Pure Translucent White Glass
      const ambient = new THREE.AmbientLight(0x1e293b, 1.4);
      scene.add(ambient);

      const keyLight = new THREE.DirectionalLight(0xffffff, 1.7);
      keyLight.position.set(60, 80, 70);
      scene.add(keyLight);

      const fillLight = new THREE.DirectionalLight(0xe2e8f0, 1.1);
      fillLight.position.set(-60, -50, -50);
      scene.add(fillLight);

      // Localized soft white light radiating outward from the root sphere
      const coreLight = new THREE.PointLight(0xffffff, 3.2, 160);
      coreLight.position.copy(ROOT_ORIGIN);
      scene.add(coreLight);

      // Build the Root Goal Translucent Glowing Sphere
      buildRootSphere();

      // Subtle Background Celestial Particles for 3D Depth
      buildSpaceParticles();

      window.addEventListener('resize', onWindowResize);
      document.getElementById('btn-reset').addEventListener('click', () => {
        camera.position.set(0, 0, 110);
        if (controls) controls.target.copy(ROOT_ORIGIN);
      });

      animate();
    }

    function buildRootSphere() {
      rootGroup = new THREE.Group();
      rootGroup.position.copy(ROOT_ORIGIN);
      scene.add(rootGroup);

      // 1. OUTER TRANSLUCENT GLOWING WHITE SPHERE (Volumetric Glass/Energy)
      // Radius = 9.5
      const sphereGeo = new THREE.SphereGeometry(9.5, 64, 64);
      const outerMat = new THREE.MeshPhysicalMaterial({
        color: 0xffffff,
        emissive: 0xffffff,
        emissiveIntensity: 0.88,
        roughness: 0.10,
        metalness: 0.05,
        transparent: true,
        opacity: 0.88,
        transmission: 0.40,
        ior: 1.35,
        clearcoat: 1.0,
        clearcoatRoughness: 0.08
      });
      rootSphere = new THREE.Mesh(sphereGeo, outerMat);
      rootGroup.add(rootSphere);

      // 2. INNER LUMINOUS NUCLEUS
      const coreGeo = new THREE.SphereGeometry(6.0, 32, 32);
      const coreMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.98
      });
      rootGroup.add(new THREE.Mesh(coreGeo, coreMat));

      // 3. RADIAL OUTWARD GLOW HALOS (Soft atmospheric radiance falloff)
      // Halo 1 (Immediate aura)
      const halo1Geo = new THREE.RingGeometry(9.3, 14.5, 64);
      const halo1Mat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.32,
        side: THREE.DoubleSide
      });
      haloMesh1 = new THREE.Mesh(halo1Geo, halo1Mat);
      rootGroup.add(haloMesh1);

      // Halo 2 (Outer soft atmospheric gradient)
      const halo2Geo = new THREE.RingGeometry(14.0, 21.0, 64);
      const halo2Mat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.16,
        side: THREE.DoubleSide
      });
      haloMesh2 = new THREE.Mesh(halo2Geo, halo2Mat);
      rootGroup.add(haloMesh2);

      // 4. RADIAL COORDINATE RAYS (Subtle outward lines)
      radialRaysGroup = new THREE.Group();
      rootGroup.add(radialRaysGroup);

      const rayCount = 24;
      for (let r = 0; r < rayCount; r++) {
        const angle = (r / rayCount) * Math.PI * 2;
        const p1 = new THREE.Vector3(Math.cos(angle) * 9.6, Math.sin(angle) * 9.6, 0);
        const p2 = new THREE.Vector3(Math.cos(angle) * 28.0, Math.sin(angle) * 28.0, 0);
        const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const lineMat = new THREE.LineBasicMaterial({
          color: 0xffffff,
          transparent: true,
          opacity: 0.22
        });
        radialRaysGroup.add(new THREE.Line(lineGeo, lineMat));
      }

      // Tilt slightly in 3D space
      rootGroup.rotation.x = Math.PI * 0.12;
      rootGroup.rotation.y = Math.PI * 0.08;
    }

    function buildSpaceParticles() {
      const starCount = 350;
      const positions = new Float32Array(starCount * 3);
      for (let i = 0; i < starCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 550;
        positions[i + 1] = (Math.random() - 0.5) * 550;
        positions[i + 2] = (Math.random() - 0.5) * 550;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const mat = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 1.1,
        transparent: true,
        opacity: 0.35
      });
      scene.add(new THREE.Points(geo, mat));
    }

    function onWindowResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    function animate() {
      requestAnimationFrame(animate);

      if (controls) controls.update();

      // Subtle breathing pulse on the radial halos
      const time = Date.now() * 0.0015;
      const pulse = 1.0 + Math.sin(time) * 0.03;
      if (haloMesh1) haloMesh1.scale.set(pulse, pulse, pulse);
      if (haloMesh2) haloMesh2.scale.set(pulse * 1.02, pulse * 1.02, pulse * 1.02);

      // Keep halos billboarded towards the camera for optimal radial radiance
      if (haloMesh1) haloMesh1.quaternion.copy(camera.quaternion);
      if (haloMesh2) haloMesh2.quaternion.copy(camera.quaternion);

      // ─────────────────────────────────────────────────────────────
      // OBSIDIAN LAW: The Root Goal text is ALWAYS VISIBLE across all zoom levels
      // ─────────────────────────────────────────────────────────────
      if (labelEl && rootGroup) {
        // Positioned directly below the outward radial glow
        const anchor = new THREE.Vector3(0, -18.5, 0);
        anchor.applyMatrix4(rootGroup.matrixWorld);
        anchor.project(camera);

        const x = (anchor.x * 0.5 + 0.5) * window.innerWidth;
        const y = (-(anchor.y * 0.5) + 0.5) * window.innerHeight;

        labelEl.style.left = `${x}px`;
        labelEl.style.top = `${y}px`;

        // GUARANTEE: Never fades to 0 opacity. Always 100% visible!
        labelEl.style.opacity = '1';

        // Dynamic scale compensation so it stays perfectly readable even when zoomed far out
        const camDist = camera.position.distanceTo(ROOT_ORIGIN);
        if (camDist > 250) {
          textEl.style.fontSize = '14px'; // Clamped readable minimum
        } else if (camDist < 60) {
          textEl.style.fontSize = '17px';
        } else {
          textEl.style.fontSize = '15px';
        }

        if (anchor.z > 1) {
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

    final_html = template.replace('__BUNDLED_CHATS_JSON__', json_str)
    
    # Write to primary playground
    out_path = 'design_pack/playground_3d.html'
    with open(out_path, 'w') as f:
        f.write(final_html)
    print(f"Root Goal Studio built successfully: {out_path} ({len(final_html)} bytes)")

if __name__ == '__main__':
    build_root_studio()
