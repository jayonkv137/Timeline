import React, { useEffect } from 'react';
import { useAppStore } from './store';
import { SectionHeader } from './components/InfoPopover';
import { GoalSection } from './components/GoalSection';
import { TimelineSection } from './components/TimelineSection';
import { HowSection } from './components/HowSection';
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
    setConversations,
    addConversation,
    updateConversationTitle,
    selectedPairIdx,
    setSelectedPairIdx,
    panelBundle,
    setPanelBundle,
    dialogue,
    setDialogue,
  } = useAppStore();

  const isFixtureMode = new URLSearchParams(window.location.search).get('fixture') === '1';

  // 1. Load active chat list/conversations
  useEffect(() => {
    if (isFixtureMode) {
      setConversations([{
        id: 'conv-1',
        title: 'React Form Debug Investigation'
      }]);
      setActiveChatId('conv-1');
    } else {
      async function fetchChats() {
        try {
          const res = await fetch('/chats');
          if (res.ok) {
            const data = await res.json();
            setConversations(data);
          }
        } catch (error) {
          console.error('Error listing chats:', error);
        }
      }
      fetchChats();
    }
  }, [isFixtureMode, setConversations, setActiveChatId]);

  // 2. Load bundle when activeChatId changes
  useEffect(() => {
    if (!activeChatId) {
      setPanelBundle(null);
      setDialogue([]);
      setSelectedPairIdx(0);
      return;
    }

    if (isFixtureMode) {
      if (activeChatId === 'conv-1') {
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
            console.error('Error loading fixture:', error);
          }
        }
        loadFixture();
      }
    } else {
      async function loadChatBundle() {
        try {
          const res = await fetch(`/chats/${activeChatId}/bundle`);
          if (res.ok) {
            const data = await res.json();
            setDialogue(data.dialogue);
            setPanelBundle(data.panel_bundle);
            if (data.panel_bundle && data.panel_bundle.pairs && data.panel_bundle.pairs.length > 0) {
              setSelectedPairIdx(data.panel_bundle.pairs.length - 1);
            } else {
              setSelectedPairIdx(0);
            }
          }
        } catch (error) {
          console.error('Error fetching chat bundle:', error);
        }
      }
      loadChatBundle();
    }
  }, [activeChatId, isFixtureMode, setPanelBundle, setDialogue, setSelectedPairIdx]);

  const handleStartChatWithTemplate = async (template: string) => {
    if (isFixtureMode) {
      const newChatId = 'conv-1';
      addConversation({
        id: newChatId,
        title: 'React Form Debug Investigation'
      });
      setActiveChatId(newChatId);
    } else {
      try {
        const res = await fetch('/chats', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ template })
        });
        if (res.ok) {
          const newChat = await res.json();
          addConversation(newChat);
          setActiveChatId(newChat.id);
        }
      } catch (error) {
        console.error('Error starting chat with template:', error);
      }
    }
  };

  const hasChatStarted = activeChatId !== null;

  // Title editing state
  const [isEditingTitle, setIsEditingTitle] = React.useState(false);
  const [tempTitle, setTempTitle] = React.useState('');

  const activeChat = conversations.find(c => c.id === activeChatId);
  const chatTitle = activeChat ? activeChat.title : 'New Chat';

  // Messaging & Streaming states
  const [inputMessage, setInputMessage] = React.useState('');
  const [isAiTyping, setIsAiTyping] = React.useState(false);
  const [streamingText, setStreamingText] = React.useState('');
  const [isRailLoading, setIsRailLoading] = React.useState(false);
  const [isGenerating, setIsGenerating] = React.useState(false);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    setTimeout(() => {
      const viewport = document.getElementById('chat-viewport');
      if (viewport) {
        viewport.scrollTo({ top: viewport.scrollHeight, behavior });
      }
    }, 50);
  };

  // Sync scroll on dialogue change or streaming text update
  useEffect(() => {
    if (hasChatStarted) {
      scrollToBottom();
    }
  }, [dialogue.length, streamingText, isAiTyping]);

  // Listen to SSE events for progress updates
  useEffect(() => {
    if (!activeChatId || isFixtureMode) {
      setIsRailLoading(false);
      return;
    }

    const eventSource = new EventSource(`/chats/${activeChatId}/events`);

    eventSource.addEventListener('pipeline_status', (e: any) => {
      try {
        const data = JSON.parse(e.data);
        setIsRailLoading(data.phase === 'running');
      } catch (err) {
        console.error('Error parsing pipeline_status:', err);
      }
    });

    eventSource.addEventListener('pair_ready', async (e: any) => {
      try {
        JSON.parse(e.data);
        const res = await fetch(`/chats/${activeChatId}/bundle`);
        if (res.ok) {
          const bundleData = await res.json();
          
          useAppStore.setState((state) => {
            const wasAtLatest = !state.panelBundle || state.selectedPairIdx === state.panelBundle.pairs.length - 1;
            const newPairsLength = bundleData.panel_bundle?.pairs?.length || 0;
            const newIndex = wasAtLatest && newPairsLength > 0 ? newPairsLength - 1 : state.selectedPairIdx;
            return {
              panelBundle: bundleData.panel_bundle,
              dialogue: bundleData.dialogue,
              selectedPairIdx: newIndex
            };
          });
        }
      } catch (err) {
        console.error('Error parsing pair_ready:', err);
      }
    });

    return () => {
      eventSource.close();
    };
  }, [activeChatId, isFixtureMode, setDialogue, setPanelBundle, setSelectedPairIdx]);

  useEffect(() => {
    if (chatTitle) {
      setTempTitle(chatTitle);
    }
  }, [chatTitle]);

  const handleSaveTitle = async () => {
    if (!activeChatId || !tempTitle.trim() || tempTitle.trim() === chatTitle) {
      setIsEditingTitle(false);
      return;
    }
    if (isFixtureMode) {
      updateConversationTitle(activeChatId, tempTitle.trim());
      setIsEditingTitle(false);
      return;
    }
    try {
      const res = await fetch(`/chats/${activeChatId}/title`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: tempTitle.trim() }),
      });
      if (res.ok) {
        updateConversationTitle(activeChatId, tempTitle.trim());
        // Reload bundle to reflect updated root outcome in UI
        const bundleRes = await fetch(`/chats/${activeChatId}/bundle`);
        if (bundleRes.ok) {
          const bundleData = await bundleRes.json();
          setPanelBundle(bundleData.panel_bundle);
        }
      }
    } catch (err) {
      console.error('Error saving title:', err);
    }
    setIsEditingTitle(false);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;
    
    setIsGenerating(true);
    setIsAiTyping(true);
    setStreamingText('');
    setInputMessage('');
    
    let chatId = activeChatId;
    
    // 1. If chat hasn't started, create it first
    if (!chatId) {
      try {
        const res = await fetch('/chats', { method: 'POST' });
        if (res.ok) {
          const newChat = await res.json();
          addConversation(newChat);
          setActiveChatId(newChat.id);
          chatId = newChat.id;
        } else {
          setIsGenerating(false);
          setIsAiTyping(false);
          return;
        }
      } catch (error) {
        console.error('Failed to create new chat:', error);
        setIsGenerating(false);
        setIsAiTyping(false);
        return;
      }
    }
    
    // Determine new pair number
    let maxPair = 0;
    let lastSpeaker = null;
    for (const turn of dialogue) {
      maxPair = Math.max(maxPair, turn.pair);
      lastSpeaker = turn.speaker;
    }
    const newPair = lastSpeaker === 'ai' ? maxPair + 1 : (maxPair || 1);
    
    // 2. Append user turn locally
    const userTurn = {
      pair: newPair,
      speaker: 'user' as const,
      text: text.trim(),
      attachments: [],
      ts: new Date().toISOString()
    };
    
    setDialogue([...dialogue, userTurn]);
    scrollToBottom();
    
    // 3. Post message to streaming API
    try {
      const response = await fetch(`/chats/${chatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get stream reader');
      }
      
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last partial line in buffer
        
        for (const line of lines) {
          const cleaned = line.trim();
          if (!cleaned.startsWith('data:')) continue;
          
          const rawData = cleaned.substring(5).trim();
          if (rawData === '[DONE]') {
            break;
          }
          
          try {
            const parsed = JSON.parse(rawData);
            if (parsed.token) {
              setIsAiTyping(false); // First token clears typing indicator
              setStreamingText(prev => prev + parsed.token);
              scrollToBottom();
            } else if (parsed.error) {
              console.error('LLM generation error:', parsed.error);
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e, rawData);
          }
        }
      }
    } catch (error) {
      console.error('Error sending message stream:', error);
      setIsAiTyping(false);
    } finally {
      setIsGenerating(false);
      setStreamingText('');
      setIsAiTyping(false);
    }
  };

  const activePair = panelBundle?.pairs?.[selectedPairIdx] || null;
  const isHistoryMode = hasChatStarted && panelBundle && selectedPairIdx < panelBundle.pairs.length - 1;

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
              {isEditingTitle ? (
                <input
                  type="text"
                  value={tempTitle}
                  onChange={(e) => setTempTitle(e.target.value)}
                  onBlur={handleSaveTitle}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveTitle();
                    if (e.key === 'Escape') {
                      setTempTitle(chatTitle);
                      setIsEditingTitle(false);
                    }
                  }}
                  autoFocus
                  style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    padding: '2px 6px',
                    outline: 'none',
                    width: '300px',
                    fontFamily: 'var(--font-sans)',
                  }}
                />
              ) : (
                <span
                  onDoubleClick={() => setIsEditingTitle(true)}
                  title="Double click to edit title"
                  style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  {chatTitle}
                </span>
              )}
            </div>

            {/* Chat History Viewport */}
            <div
              id="chat-viewport"
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
                const isHighlighted = turn.pair === (selectedPairIdx + 1);
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
                        border: isUser 
                          ? (isHighlighted ? `2px solid ${getActiveAccent()}` : 'none') 
                          : (isHighlighted ? `2.5px solid ${getActiveAccent()}` : '1.5px solid var(--border)'),
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

              {/* Streaming AI typing indicator */}
              {isAiTyping && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      assistant · typing
                    </span>
                  </div>
                  <div
                    style={{
                      maxWidth: '70%',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      fontSize: '13px',
                      backgroundColor: 'var(--card-bg)',
                      color: 'var(--text-primary)',
                      border: '1.5px solid var(--border)',
                      borderBottomLeftRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <span className="typing-dot" style={{ animationDelay: '0s' }}></span>
                    <span className="typing-dot" style={{ animationDelay: '0.2s' }}></span>
                    <span className="typing-dot" style={{ animationDelay: '0.4s' }}></span>
                  </div>
                </div>
              )}

              {/* Streaming AI text */}
              {streamingText && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    gap: '4px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      assistant · streaming
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
                      backgroundColor: 'var(--card-bg)',
                      color: 'var(--text-primary)',
                      border: `1.5px solid ${getActiveAccent()}`,
                      borderBottomLeftRadius: '4px',
                    }}
                  >
                    {streamingText}
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input Bar */}
            <div
              style={{
                padding: '16px 24px 24px',
                borderTop: '1px solid var(--border)',
              }}
            >
              {isHistoryMode && (
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                  <button
                    onClick={() => {
                      if (panelBundle) {
                        setSelectedPairIdx(panelBundle.pairs.length - 1);
                        scrollToBottom();
                      }
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      backgroundColor: 'var(--card-bg)',
                      border: '1px solid var(--border)',
                      borderRadius: '16px',
                      padding: '6px 14px',
                      fontSize: '11px',
                      fontWeight: 500,
                      color: 'var(--you)',
                      cursor: 'pointer',
                      boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--you)' }} />
                    Back to latest ↓
                  </button>
                </div>
              )}
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
                  placeholder={isGenerating ? "AI is replying..." : "Message..."}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={isGenerating}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(inputMessage);
                    }
                  }}
                  style={{
                    flex: 1,
                    border: 'none',
                    outline: 'none',
                    fontSize: '13px',
                    backgroundColor: 'transparent',
                    cursor: isGenerating ? 'not-allowed' : 'text',
                  }}
                />
                <button
                  disabled={isGenerating || !inputMessage.trim()}
                  onClick={() => handleSendMessage(inputMessage)}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    color: (isGenerating || !inputMessage.trim()) ? 'var(--text-muted)' : 'var(--you)',
                    cursor: (isGenerating || !inputMessage.trim()) ? 'not-allowed' : 'pointer',
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
                    onClick={() => {
                      const templates = ["website", "trip", "fantasy"];
                      handleStartChatWithTemplate(templates[idx]);
                    }}
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
                  placeholder={isGenerating ? "AI is replying..." : "Ask me anything..."}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={isGenerating}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(inputMessage);
                    }
                  }}
                  style={{
                    flex: 1,
                    border: 'none',
                    outline: 'none',
                    fontSize: '13px',
                    backgroundColor: 'transparent',
                    cursor: isGenerating ? 'not-allowed' : 'text',
                  }}
                />
                <button
                  disabled={isGenerating || !inputMessage.trim()}
                  onClick={() => handleSendMessage(inputMessage)}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    color: (isGenerating || !inputMessage.trim()) ? 'var(--text-muted)' : 'var(--you)',
                    cursor: (isGenerating || !inputMessage.trim()) ? 'not-allowed' : 'pointer',
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
            {hasChatStarted && panelBundle && panelBundle.pairs && panelBundle.pairs.length > 0
              ? `${selectedPairIdx + 1}/${panelBundle.pairs.length}`
              : '0/0'}
          </span>
        </div>
        {isRailLoading && (
          <div
            style={{
              height: '3px',
              width: '100%',
              backgroundColor: 'rgba(0, 87, 255, 0.08)',
              position: 'relative',
              overflow: 'hidden',
              flexShrink: 0,
            }}
          >
            <div
              className="loading-bar-anim"
              style={{
                position: 'absolute',
                height: '100%',
                backgroundColor: 'var(--you)',
                width: '30%',
              }}
            />
          </div>
        )}

        {/* ═══ ZONE 1: Upper sections (natural height, never scroll) ═══ */}
        <div style={{ flexShrink: 0 }}>
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
        </div>

        {/* ═══ ZONE 2: Timeline (fills remaining space, scrolls internally) ═══ */}
        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
          <TimelineSection
            pairs={hasChatStarted && panelBundle ? panelBundle.pairs.map((p) => p.timeline) : []}
            selectedPairIdx={selectedPairIdx}
            onSelectPair={setSelectedPairIdx}
            onRerunPair={async (pairNumber) => {
              if (isFixtureMode) return;
              try {
                setIsRailLoading(true);
                const res = await fetch(`/chats/${activeChatId}/pairs/${pairNumber}/rerun`, {
                  method: 'POST'
                });
                if (!res.ok) {
                  setIsRailLoading(false);
                }
              } catch (error) {
                console.error('Error triggering rerun:', error);
                setIsRailLoading(false);
              }
            }}
          />
        </div>

        {/* ═══ ZONE 3: HOW (pinned to bottom, aligned with chat input) ═══ */}
        <div
          style={{
            flexShrink: 0,
            borderTop: '1px solid var(--border)',
          }}
        >
          <SectionHeader label="How You're Working" sectionKey="HOW" verticalAlign="top" />
          <HowSection
            howData={
              hasChatStarted && panelBundle && panelBundle.pairs[selectedPairIdx]
                ? panelBundle.pairs[selectedPairIdx].how
                : null
            }
          />
        </div>
      </section>
    </div>
  );
};

export default App;
