import React, { useEffect } from 'react';
import { useAppStore } from './store';
import { SectionHeader } from './components/InfoPopover';
import { GoalSection } from './components/GoalSection';
import { TimelineSection } from './components/TimelineSection';
import { MessageSquare, Paperclip, Send, Plus, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  "want to help you build a website",
  "want to help you plan a trip",
  "wanna help you writing a fantasy story"
];

export const App: React.FC = () => {
  const {
    activeChatId,
    setActiveChatId,
    conversations,
    addConversation,
    selectedPairIdx,
    setSelectedPairIdx,
    panelBundle,
    setPanelBundle,
    dialogue,
    setDialogue,
  } = useAppStore();

  // Load static fixture data
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

  const handleStartChat = () => {
    const newChatId = 'conv-1';
    addConversation({
      id: newChatId,
      title: 'React Form Debug Investigation'
    });
    setActiveChatId(newChatId);
  };

  const hasChatStarted = activeChatId === 'conv-1';
  const activePair = panelBundle?.pairs?.[selectedPairIdx] || null;

  // Formatting timestamp to HH:MM format
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  // Helper to get accent color for the active pair
  const getActiveAccent = () => {
    if (!activePair) return 'var(--you)';
    // In our design, blue always left, orange always right
    if (activePair.direction.you_pct > activePair.direction.ai_pct) {
      return 'var(--you)';
    } else {
      return 'var(--ai)';
    }
  };

  // Truncate text at a clause boundary if it exceeds maxLength
  const truncateClause = (text: string | null) => {
    if (!text) return '';
    const maxLength = 60;
    if (text.length <= maxLength) return text;
    const separators = ['.', ';', ',', '—'];
    let splitIdx = -1;
    for (const sep of separators) {
      const idx = text.lastIndexOf(sep, maxLength);
      if (idx > splitIdx) splitIdx = idx;
    }
    if (splitIdx > 15) {
      return text.substring(0, splitIdx).trim() + '...';
    }
    return text.substring(0, maxLength).trim() + '...';
  };

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
            onClick={() => setActiveChatId(null)}
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
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
            title="Start New Chat"
          >
            <Plus size={14} />
          </button>
        </div>

        {/* Sidebar Chat List (initially completely empty) */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {conversations.map((chat) => {
            const isActive = activeChatId === chat.id;
            return (
              <div
                key={chat.id}
                onClick={() => setActiveChatId(chat.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  backgroundColor: isActive ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
                  cursor: 'pointer',
                  marginBottom: '4px',
                  transition: 'background-color 0.2s',
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
          backgroundColor: 'var(--bg)',
        }}
      >
        {hasChatStarted ? (
          /* Active Chat View */
          <>
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
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        marginBottom: '2px',
                      }}
                    >
                      {isUser && (
                        <span
                          style={{
                            backgroundColor: getActiveAccent(),
                            color: '#ffffff',
                            fontSize: '9px',
                            fontWeight: 600,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontFamily: 'var(--font-mono)',
                            letterSpacing: '0.02em',
                          }}
                        >
                          P{turn.pair}
                        </span>
                      )}
                      <span
                        style={{
                          fontSize: '10px',
                          color: 'var(--text-muted)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {isUser ? 'you' : 'assistant'} · {formatTime(turn.ts)}
                      </span>
                    </div>
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
                        border: isUser ? 'none' : `1.5px solid ${getActiveAccent()}`,
                        borderBottomRightRadius: isUser ? '4px' : '12px',
                        borderBottomLeftRadius: isUser ? '12px' : '4px',
                        boxShadow: isUser ? 'none' : `0 2px 12px rgba(0, 0, 0, 0.03)`,
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
          </>
        ) : (
          /* Premium Empty/Starting View */
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              padding: '40px',
              maxWidth: '800px',
              margin: '0 auto',
              width: '100%',
            }}
          >
            {/* Sparkles Icon */}
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: 'rgba(0, 87, 255, 0.08)',
                color: 'var(--you)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '24px',
              }}
            >
              <Sparkles size={24} />
            </div>

            {/* Prompt Heading */}
            <h1
              style={{
                fontSize: '28px',
                fontWeight: 500,
                color: 'var(--text-primary)',
                marginBottom: '40px',
                textAlign: 'center',
                lineHeight: 1.3,
                letterSpacing: '-0.02em',
              }}
            >
              What do you want to co-create with AI today?
            </h1>

            {/* Suggestion Cards Container */}
            <div style={{ width: '100%', marginBottom: '40px' }}>
              <div
                style={{
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  fontFamily: 'var(--font-mono)',
                  marginBottom: '12px',
                  textAlign: 'left',
                }}
              >
                Suggestions on what to ask Our AI
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  width: '100%',
                }}
              >
                {SUGGESTIONS.map((suggestion, idx) => (
                  <div
                    key={idx}
                    onClick={handleStartChat}
                    style={{
                      backgroundColor: 'var(--card-bg)',
                      border: '1px solid var(--border)',
                      borderRadius: '12px',
                      padding: '16px',
                      fontSize: '12px',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      lineHeight: 1.4,
                      transition: 'all 0.2s ease',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--you)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border)';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.02)';
                    }}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            </div>

            {/* Center Chat Input */}
            <div style={{ width: '100%' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  borderRadius: '24px',
                  padding: '12px 18px',
                  gap: '12px',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
                }}
              >
                <Paperclip size={16} style={{ color: 'var(--text-muted)', cursor: 'not-allowed' }} />
                <input
                  type="text"
                  placeholder="Ask me anything..."
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
                  marginTop: '8px',
                  textAlign: 'center',
                }}
              >
                Enter to send · Shift+Enter for new line
              </div>
            </div>
          </div>
        )}
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
              backgroundColor: hasChatStarted ? 'rgba(34, 160, 90, 0.12)' : 'rgba(0, 0, 0, 0.06)',
              color: hasChatStarted ? '#1f8f4e' : 'var(--text-muted)',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: hasChatStarted ? '#22a05a' : '#888880',
                display: 'inline-block',
              }}
            />
            {hasChatStarted ? 'Live' : 'Idle'}
          </span>
          <span
            style={{
              fontSize: '9px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {hasChatStarted ? '1/1' : '0/0'}
          </span>
        </div>

        {/* Panel Section Cards Container */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {/* Section 1: GOAL */}
          <GoalSection goal={hasChatStarted && activePair ? activePair.goal : null} />

          {/* Section 2: DIRECTION */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Direction" sectionKey="DIRECTION" />
            <div style={{ padding: '0 16px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {hasChatStarted && activePair ? (
                <>
                  {/* Split bar */}
                  <div
                    style={{
                      height: '6px',
                      width: '100%',
                      borderRadius: '3px',
                      overflow: 'hidden',
                      display: 'flex',
                      backgroundColor: 'rgba(0,0,0,0.05)',
                    }}
                  >
                    <div style={{ width: `${activePair.direction.you_pct}%`, backgroundColor: 'var(--you)', transition: 'width 0.3s' }} />
                    <div style={{ width: `${activePair.direction.ai_pct}%`, backgroundColor: 'var(--ai)', transition: 'width 0.3s' }} />
                  </div>
                  {/* Readouts + badge */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--you)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      You — {activePair.direction.you_pct}%
                    </span>
                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      @ P{activePair.pair}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--ai)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      AI — {activePair.direction.ai_pct}%
                    </span>
                  </div>
                </>
              ) : null}
            </div>
          </div>

          {/* Section 3: DECISIONS */}
          <div style={{ borderBottom: '1px solid var(--border)' }}>
            <SectionHeader label="Decisions" sectionKey="DECISIONS" />

            <div style={{ padding: '0 16px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {hasChatStarted && activePair ? (
                <>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {/* User decisions card */}
                    <div
                      style={{
                        flex: 1,
                        backgroundColor: 'rgba(0, 87, 255, 0.04)',
                        border: '1px solid rgba(0, 87, 255, 0.12)',
                        borderRadius: '8px',
                        padding: '10px 6px',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--you)', lineHeight: 1.1 }}>
                        {activePair.decisions.you_count}
                      </div>
                      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                        By You
                      </div>
                    </div>

                    {/* AI decisions card */}
                    <div
                      style={{
                        flex: 1,
                        backgroundColor: 'rgba(232, 90, 10, 0.04)',
                        border: '1px solid rgba(232, 90, 10, 0.12)',
                        borderRadius: '8px',
                        padding: '10px 6px',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--ai)', lineHeight: 1.1 }}>
                        {activePair.decisions.ai_count}
                      </div>
                      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                        By AI
                      </div>
                    </div>
                  </div>

                  {/* Latest AI Decision example */}
                  {activePair.decisions.latest_ai_example && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                      <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', textAlign: 'left' }}>
                        Latest AI Decision
                      </span>
                      <div
                        style={{
                          backgroundColor: 'rgba(0, 0, 0, 0.02)',
                          borderLeft: '3px solid var(--ai)',
                          borderRadius: '4px',
                          padding: '8px 10px',
                          fontSize: '11px',
                          fontStyle: 'italic',
                          color: 'var(--text-primary)',
                          textAlign: 'left',
                          lineHeight: '1.4',
                        }}
                      >
                        "{truncateClause(activePair.decisions.latest_ai_example)}"
                      </div>
                    </div>
                  )}
                </>
              ) : null}
            </div>
          </div>

          {/* Section 4: TIMELINE */}
          <TimelineSection
            pairs={hasChatStarted && panelBundle ? panelBundle.pairs.map((p) => p.timeline) : []}
            selectedPairIdx={selectedPairIdx}
            onSelectPair={setSelectedPairIdx}
          />

          {/* Section 5: HOW */}
          <div>
            <SectionHeader label="How You're Working" sectionKey="HOW" />
            <div style={{ padding: '0 16px 12px', fontSize: '12px', textAlign: 'left' }}>
              {hasChatStarted ? (
                <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  Loading collaboration mode...
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default App;
