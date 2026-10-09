import os

def build_obsidian_view():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CoTrace · Authentic Obsidian Graph View</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
    body {
      background: #141417;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", monospace, sans-serif;
      overflow: hidden;
      width: 100vw;
      height: 100vh;
    }
    #graph-canvas {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      cursor: grab;
    }
    #graph-canvas:active {
      cursor: grabbing;
    }

    /* Minimal Obsidian Top Bar */
    .obsidian-bar {
      position: absolute;
      top: 16px; left: 20px;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 12px;
      pointer-events: none;
    }
    .obsidian-title {
      font-size: 13px;
      font-weight: 600;
      color: #94a3b8;
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .obsidian-title strong {
      color: #f1f5f9;
    }

    /* View Switcher */
    .view-switcher {
      position: absolute;
      top: 16px; right: 20px;
      z-index: 10;
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
    .view-btn:hover {
      background: #334155;
      color: #fff;
    }
    .view-btn.active {
      background: #3b82f6;
      border-color: #60a5fa;
      color: #fff;
    }

    /* Minimal Bottom Legend / Hint */
    .bottom-hint {
      position: absolute;
      bottom: 16px; left: 20px;
      font-size: 11px;
      color: #64748b;
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 18px;
    }
    .hint-item { display: flex; align-items: center; gap: 6px; }
    .dot-u { width: 8px; height: 8px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }
    .dot-a { width: 8px; height: 8px; border-radius: 50%; background: #fb923c; box-shadow: 0 0 6px #fb923c; }
    .line-solid-sample { width: 16px; height: 2px; background: rgba(255,255,255,0.4); border-radius: 1px; }
    .line-dashed-sample { width: 16px; height: 0px; border-top: 1.5px dashed rgba(148,163,184,0.6); }

    /* Controls Badge */
    .controls-hint {
      position: absolute;
      bottom: 16px; right: 20px;
      font-size: 11px;
      color: #475569;
      pointer-events: none;
    }
  </style>
</head>
<body>

  <canvas id="graph-canvas"></canvas>

  <div id="satellite-tooltip" style="position: absolute; display: none; pointer-events: none; background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 8px; padding: 8px 12px; font-size: 11px; color: #f1f5f9; max-width: 280px; line-height: 1.4; z-index: 100; box-shadow: 0 8px 24px rgba(0,0,0,0.6);"></div>

  <div class="obsidian-bar">
    <div class="obsidian-title">
      <strong>Graph view</strong> · Pair 1 Complete (Deliverables + Micro-Anatomy)
    </div>
  </div>

  <div class="view-switcher">
    <span class="view-btn active">2D Obsidian View</span>
    <a href="playground_3d.html" class="view-btn">Switch to 3D Universe ↗</a>
  </div>

  <div class="bottom-hint">
    <div class="hint-item"><div class="dot-u"></div> User Req (Solid Dot)</div>
    <div class="hint-item"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;border:1.5px solid #fb923c;"></span> Open Question (Hollow Ring)</div>
    <div class="hint-item"><div class="line-solid-sample"></div> Tether Line</div>
    <div class="hint-item"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;border:1.5px solid #38bdf8;"></span> Terminal Active Focus</div>
  </div>

  <div class="controls-hint">
    Drag canvas to pan &nbsp;|&nbsp; Scroll to zoom &nbsp;|&nbsp; Hover over satellite beads to inspect text
  </div>

  <script>
    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');

    // Pan & Zoom state
    let zoom = 1.0;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let dragNode = null;
    let dragStartX = 0, dragStartY = 0;
    let hoveredNode = null;

    // Canvas sizing
    function resize() {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      ctx.resetTransform();
      ctx.scale(dpr, dpr);
    }

    // ─────────────────────────────────────────────────────────────
    // EXACT PAIR 1 DATA FROM PIPELINE LEDGER & STATE
    // ─────────────────────────────────────────────────────────────
    // Outcome 1: Root Origin Anchor (fixed parent)
    // Outcome 2: Child 1 (Mass: 44.0, User: 19.0 / AI: 25.0)
    // Outcome 3: Child 2 (Mass: 18.0, User: 8.0 / AI: 10.0)
    // Links:
    //   - outcome 1 -> outcome 2 (solid tether)
    //   - outcome 1 -> outcome 3 (solid tether)
    //   - outcome 2 <-> outcome 3 (dashed relational link)
    // ─────────────────────────────────────────────────────────────
    const nodes = [
      {
        id: 'outcome 1',
        text: 'Course assignment strategy and deliverables',
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        radius: 17,
        mass: 9999, // Root is pinned anchor
        isRoot: true,
        pinned: true
      },
      {
        id: 'outcome 2',
        text: 'Initial assignment plan and paper search strategy',
        x: -160,
        y: -100,
        vx: 0,
        vy: 0,
        radius: 14.0, // Scaled for 44 mass
        mass: 44.0,
        userScore: 19.0, // 43.2%
        aiScore: 25.0,   // 56.8%
        isRoot: false,
        satellites: [
          {
            id: 'req 1',
            type: 'requirement',
            origin: 'user',
            label: 'User Requirement',
            text: "The AI must review and understand the user's handwritten notes.",
            color: '#38bdf8',
            dist: 30,
            angle: -Math.PI * 0.85, // Upper-left crown (~ -153°)
            radius: 3.5,
            isHollowRing: false
          },
          {
            id: 'req 2',
            type: 'requirement',
            origin: 'user',
            label: 'User Requirement',
            text: 'The AI must review the project files and assignment requirements.',
            color: '#38bdf8',
            dist: 32,
            angle: -Math.PI * 0.58, // Top-left crown (~ -105°)
            radius: 3.5,
            isHollowRing: false
          }
        ]
      },
      {
        id: 'outcome 3',
        text: 'Expanded paper bank and recommendations',
        x: 160,
        y: -90,
        vx: 0,
        vy: 0,
        radius: 10.5, // Scaled for 18 mass (visibly smaller than outcome 2)
        mass: 18.0,
        userScore: 8.0,  // 44.4%
        aiScore: 10.0,   // 55.6%
        isRoot: false,
        isTerminalActive: true, // Terminal active focus of Pair 1 (Slot open / waiting for reply)
        satellites: [
          {
            id: 'req 1',
            type: 'requirement',
            origin: 'user',
            label: 'User Requirement',
            text: 'Search for research papers related to AI creativity and course requirements.',
            color: '#38bdf8',
            dist: 26,
            angle: -Math.PI * 0.42, // Top-right crown (~ -75°)
            radius: 3.5,
            isHollowRing: false
          },
          {
            id: 'slot 1',
            type: 'slot',
            origin: 'ai',
            label: 'Open Question / Slot',
            text: 'Selection of two specific research directions to guide the paper search.',
            color: '#fb923c',
            dist: 28,
            angle: -Math.PI * 0.12, // Upper-right crown (~ -22°)
            radius: 4.5,
            isHollowRing: true // Hollow ring for open question!
          }
        ]
      }
    ];

    const links = [
      { source: 'outcome 1', target: 'outcome 2', type: 'parent_child', length: 180 },
      { source: 'outcome 1', target: 'outcome 3', type: 'parent_child', length: 180 },
      { source: 'outcome 2', target: 'outcome 3', type: 'related', length: 220 }
    ];

    // Node lookup
    function getNode(id) {
      return nodes.find(n => n.id === id);
    }

    // ─────────────────────────────────────────────────────────────
    // SPRING FORCE SIMULATION (Authentic Obsidian Mechanics)
    // ─────────────────────────────────────────────────────────────
    // Solves coordinate scaling and keeps labels separated naturally
    function updatePhysics() {
      const springK = 0.005;
      const repulsionK = 6500;
      const damping = 0.86;

      // 1. Spring forces across links
      for (const link of links) {
        const u = getNode(link.source);
        const v = getNode(link.target);
        if (!u || !v) continue;

        const dx = v.x - u.x;
        const dy = v.y - u.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetLen = link.length;
        const force = (dist - targetLen) * (link.type === 'parent_child' ? springK : springK * 0.5);

        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (!u.pinned && u !== dragNode) {
          u.vx += fx;
          u.vy += fy;
        }
        if (!v.pinned && v !== dragNode) {
          v.vx -= fx;
          v.vy -= fy;
        }
      }

      // 2. Node-node electrostatic repulsion (keeps text from overlapping)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);

          const minSafeDist = a.radius + b.radius + 120; // ample margin for labels
          const force = repulsionK / (distSq + 400);

          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (!a.pinned && a !== dragNode) {
            a.vx -= fx;
            a.vy -= fy;
          }
          if (!b.pinned && b !== dragNode) {
            b.vx += fx;
            b.vy += fy;
          }
        }
      }

      // 3. Integrate velocities and damp
      for (const n of nodes) {
        if (n.pinned || n === dragNode) {
          n.vx = 0;
          n.vy = 0;
          continue;
        }
        n.x += n.vx;
        n.y += n.vy;
        n.vx *= damping;
        n.vy *= damping;
      }
    }

    // ─────────────────────────────────────────────────────────────
    // CLIPPED LINE & TEXT WRAPPING HELPERS
    // ─────────────────────────────────────────────────────────────
    // Lines start and end strictly on the outer circumferences (never cutting inside spheres)
    function drawClippedLine(x1, y1, r1, x2, y2, r2, isDashed = false, strokeStyle = 'rgba(255,255,255,0.3)', lineWidth = 1.2) {
      const dx = x2 - x1;
      const dy = y2 - y1;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist <= r1 + r2) return;

      const ux = dx / dist;
      const uy = dy / dist;

      const sx = x1 + ux * r1;
      const sy = y1 + uy * r1;
      const ex = x2 - ux * r2;
      const ey = y2 - uy * r2;

      ctx.beginPath();
      if (isDashed) {
        ctx.setLineDash([5, 5]);
      } else {
        ctx.setLineDash([]);
      }
      ctx.moveTo(sx, sy);
      ctx.lineTo(ex, ey);
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = lineWidth;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function drawWrappedText(text, x, y, maxWidth, lineHeight, opacity, fontSize = 11.5, isRoot = false) {
      if (opacity <= 0.05 && !isRoot) return;
      ctx.font = `${isRoot ? '500 12.5px' : '400 11.5px'} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isRoot ? '#ffffff' : `rgba(226, 232, 240, ${opacity.toFixed(2)})`;
      ctx.shadowColor = 'rgba(0, 0, 0, 0.95)';
      ctx.shadowBlur = 5;

      const words = text.split(' ');
      const lines = [];
      let currentLine = words[0];

      for (let i = 1; i < words.length; i++) {
        const word = words[i];
        const width = ctx.measureText(currentLine + ' ' + word).width;
        if (width < maxWidth) {
          currentLine += ' ' + word;
        } else {
          lines.push(currentLine);
          currentLine = word;
        }
      }
      lines.push(currentLine);

      for (let i = 0; i < lines.length; i++) {
        ctx.fillText(lines[i], x, y + i * lineHeight);
      }
      ctx.shadowBlur = 0;
    }

    // ─────────────────────────────────────────────────────────────
    // RENDERING
    // ─────────────────────────────────────────────────────────────
    function render() {
      const w = window.innerWidth;
      const h = window.innerHeight;

      // Obsidian background
      ctx.fillStyle = '#141417';
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      // Apply pan & zoom
      ctx.translate(w / 2 + panX, h / 2 + panY);
      ctx.scale(zoom, zoom);

      // 1. Draw Links (CLIPPED TO OUTER CIRCUMFERENCES)
      for (const link of links) {
        const u = getNode(link.source);
        const v = getNode(link.target);
        if (!u || !v) continue;

        if (link.type === 'parent_child') {
          // SOLID TETHER (Direct Parent -> Child)
          drawClippedLine(u.x, u.y, u.radius, v.x, v.y, v.radius, false, 'rgba(255, 255, 255, 0.45)', 1.4);
        } else {
          // DASHED RELATIONAL LINK (Cross-Branch Related)
          drawClippedLine(u.x, u.y, u.radius, v.x, v.y, v.radius, true, 'rgba(148, 163, 184, 0.45)', 1.2);
        }
      }

      // 2. Draw Nodes
      for (const node of nodes) {
        if (node.isRoot) {
          drawRootNode(node);
        } else {
          drawChildNodeWithInternalLight(node);
        }
      }

      ctx.restore();
    }

    // Draw Root Node (Singularity Anchor)
    function drawRootNode(node) {
      // Soft radial glow
      const grad = ctx.createRadialGradient(node.x, node.y, node.radius * 0.5, node.x, node.y, node.radius * 2.4);
      grad.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
      grad.addColorStop(0.5, 'rgba(255, 255, 255, 0.25)');
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * 2.4, 0, Math.PI * 2);
      ctx.fill();

      // Solid central core
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = 'rgba(255, 255, 255, 0.85)';
      ctx.shadowBlur = 14;
      ctx.fill();
      ctx.shadowBlur = 0;

      // 2 Concentric origin rings (Obsidian visual signature)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * 1.55, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius * 2.1, 0, Math.PI * 2);
      ctx.stroke();

      // ROOT LABEL: ALWAYS 100% VISIBLE across all zoom levels (compact wrapped text)
      drawWrappedText(node.text, node.x, node.y + node.radius * 2.1 + 8, 180, 16, 1.0, 12.5, true);
    }

    // Draw Child Node with Physical Dual Internal Light Mixing
    function drawChildNodeWithInternalLight(node) {
      const r = node.radius;
      const totalScore = node.userScore + node.aiScore;
      const userRatio = node.userScore / totalScore;
      const aiRatio = node.aiScore / totalScore;

      // 1. Dual internal radiance bleeding outward
      // User Blue Aura (scaled by user mass ratio)
      const blueGrad = ctx.createRadialGradient(node.x - r * 0.4, node.y, 0, node.x, node.y, r * 1.9);
      blueGrad.addColorStop(0, `rgba(56, 189, 248, ${(0.75 + userRatio * 0.25).toFixed(2)})`);
      blueGrad.addColorStop(0.5, 'rgba(56, 189, 248, 0.32)');
      blueGrad.addColorStop(1, 'rgba(56, 189, 248, 0)');
      ctx.fillStyle = blueGrad;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r * 1.9, 0, Math.PI * 2);
      ctx.fill();

      // AI Orange Aura (scaled by AI mass ratio)
      const orangeGrad = ctx.createRadialGradient(node.x + r * 0.4, node.y, 0, node.x, node.y, r * 2.0);
      orangeGrad.addColorStop(0, `rgba(251, 146, 60, ${(0.80 + aiRatio * 0.25).toFixed(2)})`);
      orangeGrad.addColorStop(0.5, 'rgba(251, 146, 60, 0.38)');
      orangeGrad.addColorStop(1, 'rgba(251, 146, 60, 0)');
      ctx.fillStyle = orangeGrad;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r * 2.0, 0, Math.PI * 2);
      ctx.fill();

      // 2. Frosted translucent spherical body with photon mixing
      const bodyGrad = ctx.createLinearGradient(node.x - r, node.y, node.x + r, node.y);
      bodyGrad.addColorStop(0, '#7dd3fc');    // soft diffused user blue
      bodyGrad.addColorStop(0.48, '#ffffff'); // bright fused white mixing core
      bodyGrad.addColorStop(1, '#fdba74');    // soft diffused AI orange

      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = bodyGrad;
      ctx.shadowColor = 'rgba(255, 255, 255, 0.5)';
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Delicate frosted glass rim
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // 4. TERMINAL ACTIVE FOCUS BEACON (Breathing aura if node is terminal active focus)
      if (node.isTerminalActive) {
        const pulse = (Math.sin(Date.now() * 0.004) + 1) * 0.5; // 0 to 1
        const beaconRadius = r + 4 + pulse * 6;
        ctx.strokeStyle = `rgba(56, 189, 248, ${(0.6 - pulse * 0.4).toFixed(2)})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(node.x, node.y, beaconRadius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = `rgba(251, 146, 60, ${(0.4 - pulse * 0.3).toFixed(2)})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(node.x, node.y, beaconRadius + 3, 0, Math.PI * 2);
        ctx.stroke();
      }

      // 5. DRAW SATELLITE MICRO-ATOMS (Lines clipped to outer circumferences!)
      if (node.satellites && node.satellites.length > 0) {
        for (const s of node.satellites) {
          const sx = node.x + Math.cos(s.angle) * s.dist;
          const sy = node.y + Math.sin(s.angle) * s.dist;
          s.currentX = sx;
          s.currentY = sy;

          // Tether line begins strictly at outer circumference of sphere and ends at satellite edge!
          drawClippedLine(node.x, node.y, node.radius, sx, sy, s.radius, false, s.isHollowRing ? 'rgba(251, 146, 60, 0.50)' : 'rgba(56, 189, 248, 0.45)', 0.95);

          if (s.isHollowRing) {
            // Open Question / Slot: Hollow glowing ring with breathing pulse
            const ringPulse = (Math.sin(Date.now() * 0.005) + 1) * 0.5;
            ctx.beginPath();
            ctx.arc(sx, sy, s.radius + ringPulse * 0.8, 0, Math.PI * 2);
            ctx.strokeStyle = s.color;
            ctx.lineWidth = 1.6;
            ctx.shadowColor = s.color;
            ctx.shadowBlur = 6;
            ctx.stroke();
            ctx.shadowBlur = 0;
          } else {
            // Requirement Atom: Solid glowing bead
            ctx.beginPath();
            ctx.arc(sx, sy, s.radius, 0, Math.PI * 2);
            ctx.fillStyle = s.color;
            ctx.shadowColor = s.color;
            ctx.shadowBlur = 6;
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        }
      }

      // CHILD TEXT: EXACT OUTCOME TEXT ONLY (Wrapped into compact pedestal lines below the sphere)
      // Satellites are in upper crown, text is below -> ZERO COLLISION GUARANTEED!
      const opacity = Math.min(Math.max((zoom - 0.45) / 0.4, 0), 1);
      drawWrappedText(node.text, node.x, node.y + r + 11, 165, 15, opacity, 11.5, false);
    }

    // ─────────────────────────────────────────────────────────────
    // INTERACTION & EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────
    function getMouseWorldPos(e) {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const mx = e.clientX - (w / 2 + panX);
      const my = e.clientY - (h / 2 + panY);
      return { x: mx / zoom, y: my / zoom };
    }

    function findNodeAt(wx, wy) {
      for (const n of nodes) {
        const dx = n.x - wx;
        const dy = n.y - wy;
        if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 8) {
          return n;
        }
      }
      return null;
    }

    canvas.addEventListener('mousedown', (e) => {
      const pos = getMouseWorldPos(e);
      const clickedNode = findNodeAt(pos.x, pos.y);

      if (clickedNode && !clickedNode.pinned) {
        dragNode = clickedNode;
      } else {
        isPanning = true;
        dragStartX = e.clientX - panX;
        dragStartY = e.clientY - panY;
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (dragNode) {
        const pos = getMouseWorldPos(e);
        dragNode.x = pos.x;
        dragNode.y = pos.y;
        dragNode.vx = 0;
        dragNode.vy = 0;
      } else if (isPanning) {
        panX = e.clientX - dragStartX;
        panY = e.clientY - dragStartY;
      } else {
        const pos = getMouseWorldPos(e);
        
        // Check satellite hover
        let foundSatellite = null;
        for (const n of nodes) {
          if (n.satellites) {
            for (const s of n.satellites) {
              if (s.currentX !== undefined) {
                const dx = s.currentX - pos.x;
                const dy = s.currentY - pos.y;
                if (Math.sqrt(dx * dx + dy * dy) <= s.radius + 6) {
                  foundSatellite = { sat: s, node: n };
                  break;
                }
              }
            }
          }
          if (foundSatellite) break;
        }

        const tip = document.getElementById('satellite-tooltip');
        if (foundSatellite) {
          tip.style.display = 'block';
          tip.style.left = `${e.clientX + 14}px`;
          tip.style.top = `${e.clientY + 10}px`;
          const s = foundSatellite.sat;
          const badgeColor = s.origin === 'user' ? '#38bdf8' : '#fb923c';
          const badgeBg = s.origin === 'user' ? 'rgba(56,189,248,0.15)' : 'rgba(251,146,60,0.15)';
          tip.innerHTML = `
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
              <span style="font-size:10px;font-weight:700;text-transform:uppercase;color:${badgeColor};background:${badgeBg};padding:2px 6px;border-radius:4px;border:1px solid ${badgeColor}44;">${s.label}</span>
              <span style="color:#64748b;font-size:10px;">${s.id}</span>
            </div>
            <div style="color:#e2e8f0;font-size:11.5px;">${s.text}</div>
          `;
          canvas.style.cursor = 'pointer';
        } else {
          tip.style.display = 'none';
          hoveredNode = findNodeAt(pos.x, pos.y);
          canvas.style.cursor = hoveredNode ? (hoveredNode.pinned ? 'default' : 'grab') : (isPanning ? 'grabbing' : 'grab');
        }
      }
    });

    window.addEventListener('mouseup', () => {
      dragNode = null;
      isPanning = false;
    });

    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      const newZoom = Math.min(Math.max(zoom * zoomFactor, 0.4), 3.5);

      const mouseX = e.clientX - (window.innerWidth / 2);
      const mouseY = e.clientY - (window.innerHeight / 2);

      panX -= mouseX * (zoomFactor - 1);
      panY -= mouseY * (zoomFactor - 1);
      zoom = newZoom;
    });

    window.addEventListener('resize', resize);

    // Animation Loop
    function loop() {
      updatePhysics();
      render();
      requestAnimationFrame(loop);
    }

    window.addEventListener('DOMContentLoaded', () => {
      resize();
      loop();
    });
  </script>
</body>
</html>
"""
    out_path = 'design_pack/playground_obsidian.html'
    with open(out_path, 'w') as f:
        f.write(html_content)
    print(f"Created authentic Obsidian 2D Graph View with 3 outcomes at {out_path} ({len(html_content)} bytes)")

if __name__ == '__main__':
    build_obsidian_view()
