# Mockup Scaffold Guide (`mockups/SCAFFOLD.md`)

This scaffold is repo-global. Every rendered mockup in `mockups/` links this shared harness.

---

## 1. What the Scaffold Provides

1. **`mockups/_theme.css`**:
   - Universal CSS custom properties for background, text, borders, party colors (`--party-user`, `--party-ai`), and spacing.
   - Dynamic mode attributes on `<html>`:
     - `data-theme="light"` (Paper)
     - `data-theme="dark"` (Obsidian)
     - `data-theme="high-contrast"`
     - `data-density="comfortable"` | `data-density="compact"`
2. **`mockups/_shell.js`**:
   - Injects the top control bar (`renderMockBar()`).
   - SVG filters for real-time **Color-Vision Deficiency (CVD)** simulation (Deuteranopia, Protanopia, Tritanopia).
   - Async capture loader (`loadCapture('c05')`) providing real 7-pair chat data.
   - URL parameter sync for deep linking (`?theme=dark&density=compact&pair=2&cvd=deuteranopia`).
3. **`mockups/captures/*.json`**:
   - Sanitized chat fixtures generated from real pipeline runs under DDR-000a.

---

## 2. Standard Boilerplate for New Mockups

Copy this template when creating any new variant (`mockups/<surface>-<concept>.html`):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Surface Name · Concept Name</title>
  <link rel="stylesheet" href="_theme.css">
  <style>
    /* Concept-specific layout styles go here */
    .mock-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: var(--space-6);
    }
  </style>
</head>
<body>
  <div class="mock-container" id="app">
    <!-- Concept markup rendered here -->
  </div>

  <script type="module">
    import { renderMockBar, loadCapture, resolveColors } from './_shell.js';

    // 1. Load real data fixture
    const capture = await loadCapture('c05');

    // 2. Render standard control bar
    const shell = renderMockBar({
      title: 'Surface Name — Concept Name',
      status: 'draft',
      capture: capture,
      onStateChange: ({ theme, density, pair }) => {
        render(pair || shell.getPair());
      }
    });

    // 3. Render concept with active pair
    function render(pairIdx) {
      const activePair = capture.pairs[pairIdx - 1];
      const colors = resolveColors();
      // Render logic...
    }

    render(shell.getPair());
  </script>
</body>
</html>
```

---

## 3. Author Responsibilities

- **Do not fork `_shell.js` or `_theme.css`**. Extend them if new global controls are needed.
- **Always ground in real data**: Use `loadCapture()` rather than hardcoded mock strings.
- **Respect density**: Ensure components react gracefully to `[data-density="compact"]` (e.g. side-panel mode).
- **Test under CVD**: Switch vision to Deuteranopia and Protanopia to confirm party colors stay distinct.
