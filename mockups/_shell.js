/**
 * mockups/_shell.js
 * Universal Mockup Shell Harness
 * Provides capture loading, interactive mock bar, theme/density toggles,
 * and SVG-based Color-Vision Deficiency (CVD) simulation filters.
 */

// SVG Matrix Filters for Color Vision Deficiency simulation
const CVD_SVG_FILTERS = `
<svg id="cvd-filters" style="display:none;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Deuteranopia (Green-blind / 6% of males) -->
    <filter id="filter-deuteranopia">
      <feColorMatrix type="matrix" values="
        0.625, 0.375, 0,   0, 0
        0.700, 0.300, 0,   0, 0
        0,     0.300, 0.7, 0, 0
        0,     0,     0,   1, 0" />
    </filter>
    <!-- Protanopia (Red-blind / 1% of males) -->
    <filter id="filter-protanopia">
      <feColorMatrix type="matrix" values="
        0.567, 0.433, 0,     0, 0
        0.558, 0.442, 0,     0, 0
        0,     0.242, 0.758, 0, 0
        0,     0,     0,     1, 0" />
    </filter>
    <!-- Tritanopia (Blue-blind / rare, 0.01%) -->
    <filter id="filter-tritanopia">
      <feColorMatrix type="matrix" values="
        0.95, 0.05,  0,     0, 0
        0,    0.433, 0.567, 0, 0
        0,    0.475, 0.525, 0, 0
        0,    0,     0,     1, 0" />
    </filter>
  </defs>
</svg>
`;

/**
 * Fetch and load sanitized capture fixture
 */
export async function loadCapture(shortId = 'c05') {
  try {
    const res = await fetch(`captures/${shortId}.json`);
    if (!res.ok) {
      throw new Error(`Failed to load capture: captures/${shortId}.json (${res.status})`);
    }
    return await res.json();
  } catch (err) {
    console.error('Error loading capture fixture:', err);
    return null;
  }
}

/**
 * Get current computed colors for canvas or chart renderers
 */
export function resolveColors() {
  const root = getComputedStyle(document.documentElement);
  return {
    graphBg: root.getPropertyValue('--graph-bg').trim() || '#141417',
    partyUser: root.getPropertyValue('--party-user').trim() || '#38bdf8',
    partyAi: root.getPropertyValue('--party-ai').trim() || '#fb923c',
    nodeRootFill: root.getPropertyValue('--node-root-fill').trim() || '#ffffff',
    labelColor: root.getPropertyValue('--label-color').trim() || '#f1f5f9',
    labelMuted: root.getPropertyValue('--label-muted').trim() || '#64748b',
    tetherActive: root.getPropertyValue('--tether-active').trim() || 'rgba(255, 255, 255, 0.70)',
    tetherDormant: root.getPropertyValue('--tether-dormant').trim() || 'rgba(71, 85, 105, 0.32)',
    tooltipBg: root.getPropertyValue('--tooltip-bg').trim() || '#090a0f',
    tooltipBorder: root.getPropertyValue('--tooltip-border').trim() || 'rgba(255, 255, 255, 0.12)',
    bgApp: root.getPropertyValue('--bg-app').trim(),
    bgSurface: root.getPropertyValue('--bg-surface').trim(),
    textPrimary: root.getPropertyValue('--text-primary').trim(),
    textSecondary: root.getPropertyValue('--text-secondary').trim(),
    borderSubtle: root.getPropertyValue('--border-subtle').trim()
  };
}

/**
 * Injects mock bar controls at top of page
 */
export function renderMockBar(options = {}) {
  const {
    title = 'Mockup',
    status = 'draft',
    capture = null,
    onStateChange = null
  } = options;

  // Ensure SVG filters are attached
  if (!document.getElementById('cvd-filters')) {
    const div = document.createElement('div');
    div.innerHTML = CVD_SVG_FILTERS;
    document.body.prepend(div.firstElementChild);
  }

  // Parse URL query params
  const urlParams = new URLSearchParams(window.location.search);
  const currentTheme = urlParams.get('theme') || 'light';
  const currentDensity = urlParams.get('density') || 'comfortable';
  const currentCvd = urlParams.get('cvd') || 'none';
  const currentPair = parseInt(urlParams.get('pair') || '1', 10);

  // Apply initial attributes
  document.documentElement.setAttribute('data-theme', currentTheme);
  document.documentElement.setAttribute('data-density', currentDensity);
  applyCvdFilter(currentCvd);

  // Build Mock Bar DOM
  const bar = document.createElement('header');
  bar.className = 'mock-bar';
  bar.innerHTML = `
    <div class="mock-bar-group">
      <a href="index.html" class="mock-control" title="Back to Mockups Index">← Directory</a>
      <span class="mock-bar-title">${title}</span>
      <span class="mock-badge">${status}</span>
    </div>

    <div class="mock-bar-group">
      ${capture && capture.total_pairs ? `
        <label class="mock-control">
          <span>Pair:</span>
          <select id="mock-pair-select" style="background:transparent; border:none; color:inherit; font-size:inherit;">
            ${Array.from({ length: capture.total_pairs }, (_, i) => i + 1).map(p => `
              <option value="${p}" ${p === currentPair ? 'selected' : ''}>P${p}</option>
            `).join('')}
          </select>
        </label>
      ` : ''}

      <label class="mock-control">
        <span>Theme:</span>
        <select id="mock-theme-select" style="background:transparent; border:none; color:inherit; font-size:inherit;">
          <option value="light" ${currentTheme === 'light' ? 'selected' : ''}>Light (Paper)</option>
          <option value="dark" ${currentTheme === 'dark' ? 'selected' : ''}>Dark (Obsidian)</option>
          <option value="high-contrast" ${currentTheme === 'high-contrast' ? 'selected' : ''}>High Contrast</option>
        </select>
      </label>

      <label class="mock-control">
        <span>Density:</span>
        <select id="mock-density-select" style="background:transparent; border:none; color:inherit; font-size:inherit;">
          <option value="comfortable" ${currentDensity === 'comfortable' ? 'selected' : ''}>Comfortable</option>
          <option value="compact" ${currentDensity === 'compact' ? 'selected' : ''}>Compact (Side-Panel)</option>
        </select>
      </label>

      <label class="mock-control" title="Simulate Color-Vision Deficiency">
        <span>Vision:</span>
        <select id="mock-cvd-select" style="background:transparent; border:none; color:inherit; font-size:inherit;">
          <option value="none" ${currentCvd === 'none' ? 'selected' : ''}>Normal</option>
          <option value="deuteranopia" ${currentCvd === 'deuteranopia' ? 'selected' : ''}>Deuteranopia (Green)</option>
          <option value="protanopia" ${currentCvd === 'protanopia' ? 'selected' : ''}>Protanopia (Red)</option>
          <option value="tritanopia" ${currentCvd === 'tritanopia' ? 'selected' : ''}>Tritanopia (Blue-Yellow)</option>
        </select>
      </label>
    </div>
  `;

  document.body.prepend(bar);

  // Wire events & URL sync
  const updateUrlParam = (key, val) => {
    const params = new URLSearchParams(window.location.search);
    params.set(key, val);
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
  };

  const themeSelect = bar.querySelector('#mock-theme-select');
  themeSelect.addEventListener('change', (e) => {
    const theme = e.target.value;
    document.documentElement.setAttribute('data-theme', theme);
    updateUrlParam('theme', theme);
    if (onStateChange) onStateChange({ theme, density: document.documentElement.getAttribute('data-density') });
  });

  const densitySelect = bar.querySelector('#mock-density-select');
  densitySelect.addEventListener('change', (e) => {
    const density = e.target.value;
    document.documentElement.setAttribute('data-density', density);
    updateUrlParam('density', density);
    if (onStateChange) onStateChange({ density });
  });

  const cvdSelect = bar.querySelector('#mock-cvd-select');
  cvdSelect.addEventListener('change', (e) => {
    const cvd = e.target.value;
    applyCvdFilter(cvd);
    updateUrlParam('cvd', cvd);
  });

  const pairSelect = bar.querySelector('#mock-pair-select');
  if (pairSelect) {
    pairSelect.addEventListener('change', (e) => {
      const pair = parseInt(e.target.value, 10);
      updateUrlParam('pair', pair);
      if (onStateChange) onStateChange({ pair });
    });
  }

  function applyCvdFilter(cvdType) {
    document.body.classList.remove('cvd-deuteranopia', 'cvd-protanopia', 'cvd-tritanopia');
    if (cvdType && cvdType !== 'none') {
      document.body.classList.add(`cvd-${cvdType}`);
    }
  }

  return {
    getPair: () => parseInt(bar.querySelector('#mock-pair-select')?.value || '1', 10),
    getTheme: () => document.documentElement.getAttribute('data-theme'),
    getDensity: () => document.documentElement.getAttribute('data-density'),
  };
}
