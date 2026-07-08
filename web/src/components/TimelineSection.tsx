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

export const TimelineSection: React.FC<TimelineSectionProps> = ({
  pairs,
  selectedPairIdx,
  onSelectPair,
}) => {
  const [drawerOpen, setDrawerOpen] = useState<boolean>(true);

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

            {/* Expanded Turn Drawer */}
            {drawerOpen && (
              <div
                style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.015)',
                  borderTop: '1px solid var(--border)',
                  borderBottom: '1px solid var(--border)',
                  padding: '12px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                {/* Requirements Sub-section */}
                {pair.drawer.requirements.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div
                      style={{
                        fontSize: '9px',
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                        textTransform: 'uppercase',
                        fontWeight: 600,
                        textAlign: 'left',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Requirements Changed
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', position: 'relative', paddingLeft: '22px' }}>
                      {/* Vertical spine timeline line */}
                      <div
                        style={{
                          position: 'absolute',
                          left: '8px',
                          top: '6px',
                          bottom: '6px',
                          width: '1.5px',
                          backgroundColor: 'rgba(0, 0, 0, 0.08)',
                        }}
                      />

                      {pair.drawer.requirements.map((req, rIdx) => {
                        const chipColor =
                          req.chip === 'blue'
                            ? 'var(--you)'
                            : req.chip === 'orange'
                            ? 'var(--ai)'
                            : '#9aa0a6'; // grey

                        // Draw visual influence bars representing delta mass
                        const reqMax = 55.0; // max delta in individual req lists
                        const reqLeftW = Math.max(1, Math.min(24, (req.delta_you / reqMax) * 24));
                        const reqRightW = Math.max(1, Math.min(24, (req.delta_ai / reqMax) * 24));

                        return (
                          <div
                            key={`${req.req_id}-${rIdx}`}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              minHeight: '26px',
                              position: 'relative',
                              marginBottom: rIdx < pair.drawer.requirements.length - 1 ? '4px' : 0,
                            }}
                          >
                            {/* R-chip centered on the timeline spine */}
                            <div
                              style={{
                                position: 'absolute',
                                left: '-22px',
                                width: '18px',
                                height: '18px',
                                borderRadius: '4px',
                                backgroundColor: chipColor,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '8px',
                                fontWeight: 700,
                                color: '#ffffff',
                                fontFamily: 'var(--font-mono)',
                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                              }}
                            >
                              {req.label}
                            </div>

                            {/* Label: req_id / outcome context */}
                            <span
                              style={{
                                fontSize: '10px',
                                fontFamily: 'var(--font-mono)',
                                color: 'var(--text-primary)',
                                width: '56px',
                                textAlign: 'left',
                                flexShrink: 0,
                                paddingLeft: '4px',
                              }}
                            >
                              {req.label} {req.op === 'create' ? 'new' : 'rev'}
                            </span>

                            {/* Influence Bars */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flex: 1 }}>
                              <div style={{ display: 'flex', width: '56px', height: '6px', backgroundColor: 'rgba(0,0,0,0.03)', borderRadius: '2px', overflow: 'hidden' }}>
                                {/* User segment (blue, left-aligned) */}
                                <div style={{ width: `${(reqLeftW / 48) * 100}%`, backgroundColor: 'var(--you)' }} />
                                {/* AI segment (orange, right-aligned) */}
                                <div style={{ flex: 1 }} />
                                <div style={{ width: `${(reqRightW / 48) * 100}%`, backgroundColor: 'var(--ai)' }} />
                              </div>

                              {/* Numeric labels for mass delta details */}
                              <span
                                style={{
                                  fontSize: '9px',
                                  fontFamily: 'var(--font-mono)',
                                  color: 'var(--text-muted)',
                                  marginLeft: '4px',
                                }}
                              >
                                {req.delta_you > 0 ? `+${req.delta_you}` : '0'} / {req.delta_ai > 0 ? `+${req.delta_ai}` : '0'}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Open slots sub-section */}
                {pair.drawer.slots.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderTop: '1px dashed var(--border)', paddingTop: '10px' }}>
                    <div
                      style={{
                        fontSize: '9px',
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                        textTransform: 'uppercase',
                        fontWeight: 600,
                        textAlign: 'left',
                        letterSpacing: '0.04em',
                      }}
                    >
                      Open Questions
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', paddingLeft: '4px' }}>
                      {pair.drawer.slots.map((slot, sIdx) => {
                        const label = `S${sIdx + 1}`;
                        const isAi = slot.origin === 'AI';
                        const themeColor = isAi ? 'var(--ai)' : 'var(--you)';

                        return (
                          <div
                            key={`${slot.slot_id}-${sIdx}`}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              width: '26px',
                              height: '26px',
                              borderRadius: '50%',
                              border: `1.5px dashed ${themeColor}`,
                              fontSize: '10px',
                              fontFamily: 'var(--font-mono)',
                              fontWeight: 700,
                              color: themeColor,
                              backgroundColor: isAi ? 'rgba(232, 90, 10, 0.02)' : 'rgba(0, 87, 255, 0.02)',
                              cursor: 'default',
                            }}
                            title={`${label} raised by ${slot.origin}`}
                          >
                            {label}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
