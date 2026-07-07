import React, { useEffect } from 'react';
import { useAppStore } from './store';
import { SectionHeader } from './components/InfoPopover';
import { MessageSquare, Paperclip, Send, Plus } from 'lucide-react';

const CHATS = [
  { id: 'conv-1', title: 'React Form Debug Investigation' },
  { id: 'conv-2', title: 'Cover Letter — Lumen' },
  { id: 'conv-3', title: 'Newsletter Angle — Brainstorm' },
];

export const App: React.FC = () => {
  const {
    // selectedPairIdx,
    // panelBundle,
    setPanelBundle,
    dialogue,
    setDialogue,
  } = useAppStore();

  // Load static fixture data synced from S3 (via npm run sync-fixture)
  useEffect(() => {
    async function loadFixture() {
      try {
        const bundleRes = await fetch('/fixture/panel_bundle.json');
        if (bundleRes.ok) {
          const bundleData = await bundleRes.json();
          setPanelBundle(bundleData);
        }

        const dialogueRes = await fetch('/fixture/dialogue.json');
        if (dialogueRes.ok) {
          const dialogueData = await dialogueRes.json();
          setDialogue(dialogueData);
        }
      } catch (error) {
        console.error('Error loading fixture data:', error);
      }
    }
    loadFixture();
  }, [setPanelBundle, setDialogue]);

  // const activePair = panelBundle?.pairs?.[selectedPairIdx] || null;

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        fontFamily: 'var(--font-sans)',
        backgroundColor: 'var(--bg)',
      }}
    >
      {/* 1. Sidebar */}
      <aside
        id="sidebar"
        style={{
          width: '240px',
          height: '100%',
          flexShrink: 0,
          backgroundColor: 'var(--panel)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Sidebar Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            Chats
          </span>
          <button
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              backgroundColor: 'var(--card-bg)',
              color: 'var(--text-primary)',
              cursor: 'not-allowed',
            }}
            disabled
          >
            <Plus size={14} />
          </button>
        </div>

        {/* Sidebar Chat List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {CHATS.map((chat) => {
            const isActive = chat.id === 'conv-1';
            return (
              <div
                key={chat.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  backgroundColor: isActive ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
                  cursor: isActive ? 'default' : 'not-allowed',
                  marginBottom: '4px',
                }}
              >
                <MessageSquare size={14} style={{ color: 'var(--text-muted)' }} />
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: isActive ? 500 : 400,
                    color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {chat.title}
                </span>
              </div>
            );
          })}
        </div>

        {/* Sidebar Footer */}
        <div
          style={{
            padding: '16px',
            borderTop: '1px solid var(--border)',
            fontSize: '11px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            textAlign: 'left',
          }}
        >
          AI Assistant · v1.0
        </div>
      </aside>

      {/* 2. Middle Chat Column */}
      <main
        style={{
          flex: 1,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        {/* Chat Header */}
        <div
          style={{
            height: '48px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 24px',
          }}
        >
          <span style={{ fontSize: '13px', fontWeight: 500 }}>
            React Form Debug Investigation
          </span>
        </div>

        {/* Chat History Viewport */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          {dialogue.map((turn, index) => {
            const isUser = turn.speaker === 'user';
            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isUser ? 'flex-end' : 'flex-start',
                  gap: '4px',
                }}
              >
                <span
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {isUser ? 'you' : 'assistant'} · {turn.ts}
                </span>
                <div
                  style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    lineHeight: 1.5,
                    whiteSpace: 'pre-wrap',
                    textAlign: 'left',
                    backgroundColor: isUser ? '#1a1a1a' : 'var(--card-bg)',
                    color: isUser ? '#ffffff' : 'var(--text-primary)',
                    border: isUser ? 'none' : '1px solid var(--border)',
                  }}
                >
                  {turn.text}
                </div>
              </div>
            );
          })}
        </div>

        {/* Chat Input Bar */}
        <div
          style={{
            padding: '16px 24px 24px',
            borderTop: '1px solid var(--border)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'var(--card-bg)',
              border: '1px solid var(--border)',
              borderRadius: '24px',
              padding: '8px 16px',
              gap: '12px',
            }}
          >
            <Paperclip size={16} style={{ color: 'var(--text-muted)', cursor: 'not-allowed' }} />
            <input
              type="text"
              placeholder="Message..."
              disabled
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                fontSize: '13px',
                backgroundColor: 'transparent',
                cursor: 'not-allowed',
              }}
            />
            <button
              disabled
              style={{
                border: 'none',
                background: 'transparent',
                color: 'var(--text-muted)',
                cursor: 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Send size={14} />
            </button>
          </div>
          <div
            style={{
              fontSize: '10px',
              color: 'var(--text-muted)',
              marginTop: '6px',
              textAlign: 'center',
            }}
          >
            Enter to send · Shift+Enter for new line
          </div>
        </div>
      </main>

      {/* 3. Right Agency Panel Rail */}
      <section
        id="rail"
        style={{
          width: '360px',
          height: '100%',
          flexShrink: 0,
          borderLeft: '1px solid var(--border)',
          backgroundColor: 'var(--panel)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Rail Top Status Strip */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px 8px',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '12px',
              padding: '2px 8px',
              fontSize: '9px',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              textTransform: 'uppercase',
              backgroundColor: 'rgba(34, 160, 90, 0.12)',
              color: '#1f8f4e',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: '#22a05a',
                display: 'inline-block',
              }}
            />
            Live
          </span>
          <span
            style={{
              fontSize: '9px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            1/1
          </span>
        </div>

        {/* Panel Section Cards Container */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {/* Section 1: GOAL */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Goal" sectionKey="GOAL" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              {/* Goal container shell placeholder */}
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Loading goal tree...
              </div>
            </div>
          </div>

          {/* Section 2: DIRECTION */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Direction" sectionKey="DIRECTION" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Loading direction odometer...
              </div>
            </div>
          </div>

          {/* Section 3: DECISIONS */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Decisions" sectionKey="DECISIONS" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Loading decisions...
              </div>
            </div>
          </div>

          {/* Section 4: TIMELINE */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Timeline" sectionKey="TIMELINE" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Loading timeline...
              </div>
            </div>
          </div>

          {/* Section 5: HOW */}
          <div>
            <SectionHeader label="How You're Working" sectionKey="HOW" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Loading collaboration mode...
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default App;
