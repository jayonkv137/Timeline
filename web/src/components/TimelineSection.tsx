import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { SectionHeader } from './InfoPopover';

interface RequirementItem {
  outcome_id: string;
  req_id: string;
  label: string;
  op: 'create' | 'revise' | 'delete';
  delta_you: number;
  delta_ai: number;
  chip: 'blue' | 'grey' | 'orange';
}

interface SlotItem {
  slot_id: string;
  origin: 'user' | 'AI';
  status: 'open' | 'resolved' | 'abandoned';
  resolved_into: string | null;
}

interface TimelinePair {
  pair: number;
  delta_you: number;
  delta_ai: number;
  summary: string;
  drawer: {
    requirements: RequirementItem[];
    slots: SlotItem[];
  };
}

interface TimelineSectionProps {
  pairs: TimelinePair[];
  selectedPairIdx: number;
  onSelectPair: (idx: number) => void;
}

// Full requirement details for Level-2 expansion
const REQ_DETAILS: Record<string, { title: string; text: string; rationale: string }> = {
  'R1': {
    title: 'R1 · 3D Interactive Scene',
    text: 'Implement a 3D interactive viewport using Three.js / WebGL.',
    rationale: 'User requested an interactive 3D layout in the initial prompt.'
  },
  'R2': {
    title: 'R2 · Black Box Sandbox',
    text: 'Sandbox the LLM execution environment as a secure black box.',
    rationale: 'Security requirement to isolate untrusted code generation.'
  },
  'R3': {
    title: 'R3 · Squid Animation',
    text: 'Add custom micro-animations for the squid character states.',
    rationale: 'User requested playful character feedback for loading/idle states.'
  },
  'R4': {
    title: 'R4 · Brain Canvas Page',
    text: 'A visual canvas mapping connections between ideas in a brain layout.',
    rationale: 'User wants a visual mapping view for structured ideas.'
  },
  'R5': {
    title: 'R5 · Split Screen Layout',
    text: 'Resizable split viewport between code editor and preview.',
    rationale: 'Developer tool requirement for layout flexibility.'
  },
  'R6': {
    title: 'R6 · Hover Reveal Interaction',
    text: 'Hovering on requirement displays trace connections and evidence quotes.',
    rationale: 'Core visual requirement for trace details Popovers.'
  },
  'R7': {
    title: 'R7 · Dot Grid Background',
    text: 'Subtle dot-grid blueprint background for visual structure.',
    rationale: 'Aesthetic constraint to look like a premium canvas.'
  },
  'R8': {
    title: 'R8 · Graph Grid System',
    text: '2D coordinates grid system for timeline canvas navigation.',
    rationale: 'Required for positioning timeline coordinate nodes.'
  },
  'R9': {
    title: 'R9 · Face → About Page Transition',
    text: 'Smooth morph transition when clicking the author portrait.',
    rationale: 'Micro-animation requirement to wow the user.'
  },
  'R10': {
    title: 'R10 · Figjam Export Integration',
    text: 'Ability to export the workspace state into a Figjam whiteboard format.',
    rationale: 'Collaboration feature requested by the product manager.'
  },
  'R11': {
    title: 'R11 · Workflow Validation Rules',
    text: 'Final production scene generations must use the Style Anchor plus a texture crop plus a color swatch as triple-references.',
    rationale: 'Strict validation constraint set by user to guide LLM styling.'
  },
  'R12': {
    title: 'R12 · Design System Tokens',
    text: 'Centralized token repository in index.css for fonts, borders, and margins.',
    rationale: 'Core styling requirement for premium design alignment.'
  },
  'R13': {
    title: 'R13 · Phased Plan (AI)',
    text: 'AI-generated plan splitting development into distinct checkpoint phases.',
    rationale: 'AI suggestion to organize coding workflow systematically.'
  },
  'R14': {
    title: 'R14 · Deployment Config',
    text: 'Production build configuration for static edge deployments.',
    rationale: 'AI suggestion to ensure clean build distribution.'
  },
};

export const TimelineSection: React.FC<TimelineSectionProps> = ({
  pairs,
  selectedPairIdx,
  onSelectPair,
}) => {
  const [drawerOpen, setDrawerOpen] = useState<boolean>(true);
  const [expandedReq, setExpandedReq] = useState<string | null>(null);

  if (pairs.length === 0) {
    return (
      <div style={{ borderBottom: '1px solid var(--border)' }}>
        <SectionHeader label="Timeline" sectionKey="TIMELINE" />
        <div style={{ padding: '0 16px 12px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Your conversation map will build as you chat.
        </div>
      </div>
    );
  }

  // Visual constants
  const CANVAS_W = 40;
  const TICK_X = CANVAS_W / 2;
  const BAR_GAP = 2;
  const MAX_DELTA = 314.0; // scale reference max value

  return (
    <div style={{ borderBottom: '1px solid var(--border)' }}>
      <SectionHeader label="Timeline" sectionKey="TIMELINE" />

      {pairs.map((pair, idx) => {
        const isActive = idx === selectedPairIdx;
        
        // Calculate proportional widths for collapsed turn delta bars
        const leftW = Math.max(1, Math.min(18, (pair.delta_you / MAX_DELTA) * 18));
        const rightW = Math.max(1, Math.min(18, (pair.delta_ai / MAX_DELTA) * 18));

        return (
          <div key={pair.pair} style={{ display: 'flex', flexDirection: 'column' }}>
            {/* Collapsed Turn Row */}
            <div
              onClick={() => onSelectPair(idx)}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '8px 16px',
                cursor: 'pointer',
                backgroundColor: isActive ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--you)' : '3px solid transparent',
                transition: 'background-color 0.2s, border-color 0.2s',
              }}
            >
              {/* Pair Label */}
              <span
                style={{
                  width: '28px',
                  fontSize: '10px',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: isActive ? 600 : 400,
                  textAlign: 'left',
                }}
              >
                P{pair.pair}
              </span>

              {/* Turn-Delta Micro-Spine Bar Canvas */}
              <svg width={CANVAS_W} height={16} style={{ flexShrink: 0, overflow: 'visible', marginLeft: '4px' }}>
                {/* Center spine marker */}
                <line x1={TICK_X} y1={0} x2={TICK_X} y2={16} stroke="var(--border)" strokeWidth={1.5} />
                {/* User delta bar (growing left) */}
                {pair.delta_you > 0 && (
                  <rect
                    x={TICK_X - BAR_GAP - leftW}
                    y={4}
                    width={leftW}
                    height={8}
                    rx={1.5}
                    fill="var(--you)"
                    opacity={isActive ? 0.95 : 0.6}
                  />
                )}
                {/* AI delta bar (growing right) */}
                {pair.delta_ai > 0 && (
                  <rect
                    x={TICK_X + BAR_GAP}
                    y={4}
                    width={rightW}
                    height={8}
                    rx={1.5}
                    fill="var(--ai)"
                    opacity={isActive ? 0.95 : 0.6}
                  />
                )}
              </svg>

              {/* Summary description */}
              <span
                style={{
                  flex: 1,
                  marginLeft: '12px',
                  fontSize: '11px',
                  fontWeight: isActive ? 500 : 400,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                  textAlign: 'left',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
                title={pair.summary}
              >
                {pair.summary}
              </span>

              {/* Expand/Collapse Chevron */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDrawerOpen(!drawerOpen);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '2px',
                  borderRadius: '4px',
                }}
              >
                {drawerOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>

            {/* Expanded Turn Drawer (Diverging Bar Chart in Light Theme) */}
            {drawerOpen && (
              <div
                style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.01)',
                  borderTop: '1px solid var(--border)',
                  borderBottom: '1px solid var(--border)',
                  padding: '12px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  position: 'relative',
                  overflowX: 'hidden',
                }}
              >
                {/* Visual SVG Diverging Bar Chart */}
                <svg
                  viewBox="0 0 328 385"
                  width="100%"
                  height="100%"
                  style={{
                    overflow: 'visible',
                    backgroundColor: 'transparent',
                    userSelect: 'none',
                  }}
                >
                  {/* Central axis spine (dashed vertical line) */}
                  <line
                    x1={145}
                    y1={5}
                    x2={145}
                    y2={375}
                    stroke="var(--border)"
                    strokeWidth={1.5}
                    strokeDasharray="3,3"
                  />

                  {/* Diverging Rows (R1 through R14) */}
                  {pair.drawer.requirements.map((req, rIdx) => {
                    const centerY = 16 + rIdx * 26;
                    
                    // Chip Background Colors
                    const chipColor =
                      req.chip === 'blue'
                        ? '#0057FF'
                        : req.chip === 'orange'
                        ? '#E85A0A'
                        : '#777777'; // Straddling Grey

                    // Proportional scaling for diverging bars (Max delta = 55px width)
                    const reqMaxVal = 55.0;
                    const leftBarW = Math.min(65, (req.delta_you / reqMaxVal) * 65);
                    const rightBarW = Math.min(65, (req.delta_ai / reqMaxVal) * 65);
                    
                    // Check if selected for details highlight
                    const isExpanded = expandedReq === req.label;

                    return (
                      <g
                        key={req.req_id + rIdx}
                        onClick={() => setExpandedReq(isExpanded ? null : req.label)}
                        style={{ cursor: 'pointer' }}
                        opacity={expandedReq && !isExpanded ? 0.35 : 1}
                      >
                        {/* Hover/Selection background highlight */}
                        {isExpanded && (
                          <rect
                            x={2}
                            y={centerY - 12}
                            width={324}
                            height={24}
                            rx={4}
                            fill="rgba(0, 0, 0, 0.03)"
                            stroke="var(--border)"
                            strokeWidth={0.5}
                          />
                        )}

                        {/* Left side text label (ends right-aligned to user's blue bar) */}
                        {req.delta_you > 0 && (
                          <text
                            x={145 - leftBarW - 16}
                            y={centerY + 3}
                            textAnchor="end"
                            fill={isExpanded ? 'var(--text-primary)' : 'var(--text-muted)'}
                            fontSize="9"
                            fontFamily="var(--font-sans)"
                          >
                            {REQ_DETAILS[req.label]?.text ? `${req.label} ${REQ_DETAILS[req.label].text}` : req.label}
                          </text>
                        )}

                        {/* Left Blue Bar (User Delta) */}
                        {req.delta_you > 0 && (
                          <rect
                            x={145 - 10 - leftBarW}
                            y={centerY - 5}
                            width={leftBarW}
                            height={10}
                            rx={2}
                            fill="#0057FF"
                          />
                        )}

                        {/* Centered R-badge Circle */}
                        <circle
                          cx={145}
                          cy={centerY}
                          r={10}
                          fill={chipColor}
                          stroke="var(--card-bg)"
                          strokeWidth={1.5}
                        />
                        <text
                          x={145}
                          y={centerY + 3}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="8"
                          fontWeight={700}
                          fontFamily="var(--font-mono)"
                        >
                          {req.label}
                        </text>

                        {/* Right Orange Bar (AI Delta) */}
                        {req.delta_ai > 0 && (
                          <rect
                            x={145 + 10}
                            y={centerY - 5}
                            width={rightBarW}
                            height={10}
                            rx={2}
                            fill="#E85A0A"
                          />
                        )}

                        {/* Right side text label (if AI-authored only, sits right of orange bar) */}
                        {req.delta_you === 0 && (
                          <text
                            x={145 + rightBarW + 16}
                            y={centerY + 3}
                            textAnchor="start"
                            fill={isExpanded ? 'var(--text-primary)' : 'var(--text-muted)'}
                            fontSize="9"
                            fontFamily="var(--font-sans)"
                          >
                            {REQ_DETAILS[req.label]?.text ? `${req.label} ${REQ_DETAILS[req.label].text}` : req.label}
                          </text>
                        )}
                      </g>
                    );
                  })}
                </svg>

                {/* Level-2 expanded detail container (Dynamic on row tap) */}
                {expandedReq && REQ_DETAILS[expandedReq] && (
                  <div
                    style={{
                      marginTop: '8px',
                      backgroundColor: 'var(--card-bg)',
                      border: '1px solid var(--border)',
                      borderRadius: '6px',
                      padding: '12px',
                      textAlign: 'left',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
                      animation: 'fadeIn 0.2s ease-in-out',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: expandedReq === 'R11' ? '#E85A0A' : '#0057FF',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {REQ_DETAILS[expandedReq].title}
                      </span>
                      <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        Mass: {pair.drawer.requirements.find(r => r.label === expandedReq)?.delta_you} you / {pair.drawer.requirements.find(r => r.label === expandedReq)?.delta_ai} AI
                      </span>
                    </div>

                    <p style={{ fontSize: '11px', color: 'var(--text-primary)', lineHeight: '1.4', margin: '0 0 6px 0' }}>
                      {REQ_DETAILS[expandedReq].text}
                    </p>

                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '6px', fontStyle: 'italic' }}>
                      <strong>Rationale:</strong> {REQ_DETAILS[expandedReq].rationale}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};
