import React, { useState, useRef, useEffect } from 'react';

const SECTION_INFO: Record<string, { text: string; bold?: boolean }[]> = {
  GOAL: [
    { text: "Gives you an idea what you are currently working on, and a bit of context on the goal you are working towards." },
    { text: "You can expand to see the full structure of your goals." },
  ],
  DIRECTION: [
    { text: "Shows how much of this chat's direction has come from you versus the AI, added up so far." },
    { text: "Updates as you keep talking." },
  ],
  DECISIONS: [
    { text: "A count of who introduced what." },
    { text: "Each time a new requirement or idea gets set for this chat, it's counted here under whoever introduced it first." },
  ],
  TIMELINE: [
    { text: "The record of what actually happened — one row per exchange." },
    { text: "Tap a row to see what was decided and why." },
  ],
  HOW: [
    { text: "Shows how you and the AI worked together this exchange." },
    { text: "You're driving", bold: true },
    { text: " — you're setting the direction, AI helps when asked." },
    { text: "Copiloting", bold: true },
    { text: " — you and the AI are shaping the work together." },
    { text: "Autopilot", bold: true },
    { text: " — the AI is mostly deciding and doing." },
  ],
  REQUIREMENTS: [
    { text: "Displays the design decisions and requirements shaped during this turn." },
    { text: "Blue bars show user shaping effort; orange bars show AI shaping effort. Tap any row to view its exact text and extraction rationale." }
  ],
};

interface InfoPopoverProps {
  sectionKey: string;
}

export const InfoPopover: React.FC<InfoPopoverProps> = ({ sectionKey }) => {
  const [open, setOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const popId = `infopop-${sectionKey.toLowerCase()}`;

  // Close on click-outside
  useEffect(() => {
    if (!open) return;
    function onMouseDown(e: MouseEvent) {
      if (
        popRef.current && !popRef.current.contains(e.target as Node) &&
        btnRef.current && !btnRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, [open]);

  // Close on Escape (accessibility)
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setOpen(false);
        btnRef.current?.focus();
      }
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  const toggle = () => setOpen((prev) => !prev);

  const renderInfoLines = () => {
    const lines = SECTION_INFO[sectionKey] || [];
    if (sectionKey !== 'HOW') {
      return lines.map((l, i) => (
        <p
          key={i}
          style={{
            margin: 0,
            fontSize: '11px',
            lineHeight: 1.6,
            color: i === 0 ? 'var(--text-primary)' : 'var(--text-muted)',
            textAlign: 'left',
          }}
        >
          {l.text}
        </p>
      ));
    }
    
    // HOW: first line plain, then 3 bold+description pairs
    const [intro, ...rest] = lines;
    const pairs: React.ReactNode[] = [];
    for (let i = 0; i < rest.length; i += 2) {
      const label = rest[i];
      const desc = rest[i + 1];
      pairs.push(
        <p
          key={i}
          style={{
            margin: 0,
            fontSize: '11px',
            lineHeight: 1.6,
            color: 'var(--text-muted)',
            textAlign: 'left',
          }}
        >
          <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
            {label?.text}
          </strong>
          {desc?.text}
        </p>
      );
    }
    return [
      <p
        key="intro"
        style={{
          margin: '0 0 4px 0',
          fontSize: '11px',
          lineHeight: 1.6,
          color: 'var(--text-primary)',
          textAlign: 'left',
        }}
      >
        {intro.text}
      </p>,
      ...pairs,
    ];
  };

  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      <button
        ref={btnRef}
        onClick={toggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggle();
          }
        }}
        aria-label={`Learn more about ${sectionKey}`}
        aria-expanded={open}
        aria-controls={popId}
        style={{
          width: '14px',
          height: '14px',
          borderRadius: '50%',
          border: '1.5px solid var(--text-muted)',
          background: 'transparent',
          color: 'var(--text-muted)',
          fontSize: '8px',
          fontWeight: 700,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          flexShrink: 0,
          lineHeight: 1,
          opacity: open ? 1 : 0.5,
          transition: 'opacity 0.15s',
          outline: 'none',
        }}
        onFocus={(e) => (e.currentTarget.style.opacity = '1')}
        onBlur={(e) => {
          if (!open) e.currentTarget.style.opacity = '0.5';
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
        onMouseLeave={(e) => {
          if (!open) e.currentTarget.style.opacity = '0.5';
        }}
      >
        i
      </button>

      {open && (
        <div
          id={popId}
          ref={popRef}
          role="dialog"
          aria-label={`Info: ${sectionKey}`}
          style={{
            position: 'absolute',
            zIndex: 999,
            top: '20px',
            right: 0,
            width: '240px',
            backgroundColor: 'var(--card-bg)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            boxShadow: '0 6px 24px rgba(0,0,0,0.12)',
            padding: '12px 14px',
          }}
        >
          <button
            onClick={() => {
              setOpen(false);
              btnRef.current?.focus();
            }}
            aria-label="Close Popover"
            style={{
              position: 'absolute',
              top: '6px',
              right: '8px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              fontSize: '14px',
              lineHeight: 1,
              opacity: 0.6,
              padding: '4px',
            }}
          >
            ×
          </button>
          <div
            style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
            aria-describedby={popId}
          >
            {renderInfoLines()}
          </div>
        </div>
      )}
    </span>
  );
};

interface SectionHeaderProps {
  label: string;
  sectionKey: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ label, sectionKey }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'between',
        padding: '12px 16px 6px',
        width: '100%',
      }}
    >
      <span
        style={{
          flexGrow: 1,
          fontSize: '9px',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontWeight: 500,
          textAlign: 'left',
        }}
      >
        {label}
      </span>
      <InfoPopover sectionKey={sectionKey} />
    </div>
  );
};
