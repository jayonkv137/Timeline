import React from 'react';

interface HowData {
  mode: 'CENTAUR' | 'COPILOT' | 'AUTOPILOT' | 'QUIET';
  signals: {
    w_you: number;
    w_ai: number;
    h_you: number;
    h_ai: number;
    substantive_user: boolean;
  };
  split: {
    centaur_pct: number;
    copilot_pct: number;
    autopilot_pct: number;
  };
}

interface HowSectionProps {
  howData: HowData | null | undefined;
}

export const HowSection: React.FC<HowSectionProps> = ({ howData }) => {
  if (!howData) {
    return (
      <div style={{ padding: '0 16px 12px', fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
        Collaboration mode will build as you chat.
      </div>
    );
  }

  // Locked sentences per PANEL_SPEC §5
  const getModeSentence = (mode: HowData['mode']) => {
    switch (mode) {
      case 'CENTAUR':
        return "You're driving — the AI assists when asked.";
      case 'COPILOT':
        return "Copilot — you're flying this together.";
      case 'AUTOPILOT':
        return "Autopilot — the AI is flying; you're along for the ride.";
      case 'QUIET':
        return "Quiet exchange — no requirements shaped.";
      default:
        return "Quiet exchange — no requirements shaped.";
    }
  };

  const { centaur_pct = 0, copilot_pct = 0, autopilot_pct = 0 } = howData.split || {};
  const totalPct = centaur_pct + copilot_pct + autopilot_pct;

  return (
    <div style={{ padding: '0 16px 12px', display: 'flex', flexDirection: 'column', gap: '10px', textAlign: 'left' }}>
      {/* Mode Sentence (Bold, zero preaching) */}
      <div
        style={{
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--text-primary)',
          lineHeight: '1.4',
        }}
      >
        {getModeSentence(howData.mode)}
      </div>

      {/* Running Distribution Section */}
      {totalPct > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
          {/* Section subtitle */}
          <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            Running Distribution
          </span>

          {/* Segmented distribution progress bar */}
          <div
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              display: 'flex',
              overflow: 'hidden',
              backgroundColor: 'var(--border)',
            }}
          >
            {centaur_pct > 0 && (
              <div
                style={{
                  width: `${centaur_pct}%`,
                  backgroundColor: '#0057FF', // You (Blue)
                  height: '100%',
                }}
                title={`Centaur: ${centaur_pct.toFixed(0)}%`}
              />
            )}
            {copilot_pct > 0 && (
              <div
                style={{
                  width: `${copilot_pct}%`,
                  backgroundColor: '#777777', // Copilot (Grey)
                  height: '100%',
                }}
                title={`Copilot: ${copilot_pct.toFixed(0)}%`}
              />
            )}
            {autopilot_pct > 0 && (
              <div
                style={{
                  width: `${autopilot_pct}%`,
                  backgroundColor: '#E85A0A', // Autopilot (Orange)
                  height: '100%',
                }}
                title={`Autopilot: ${autopilot_pct.toFixed(0)}%`}
              />
            )}
          </div>

          {/* Split labels legend */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '2px' }}>
            {centaur_pct > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#0057FF', display: 'inline-block' }} />
                <span style={{ color: 'var(--text-muted)' }}>Driving ({centaur_pct.toFixed(0)}%)</span>
              </div>
            )}
            {copilot_pct > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#777777', display: 'inline-block' }} />
                <span style={{ color: 'var(--text-muted)' }}>Copilot ({copilot_pct.toFixed(0)}%)</span>
              </div>
            )}
            {autopilot_pct > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', fontFamily: 'var(--font-mono)' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#E85A0A', display: 'inline-block' }} />
                <span style={{ color: 'var(--text-muted)' }}>Autopilot ({autopilot_pct.toFixed(0)}%)</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
