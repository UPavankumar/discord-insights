import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Terminal, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import ChartRenderer from './ChartRenderer';
import DataTable from './DataTable';

export default function ChatInterface({ onPinChart, pinnedCharts, enabledPlugins }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      stages: [
        {
          stage: 'prose',
          payload: {
            text: `👋 Welcome to Exaqube Analytics!

I am your Discord Intelligence AI Assistant. Here is an overview of the dataset & platform:

📊 Dataset Scope:
• Coverage Period: December 18, 2025 – June 16, 2026
• Scale: 10 Servers, 62 Channels, 2,775 Members, 5,000 Messages
• Server Regions: US-East, US-West, Europe, Asia, Brazil

⚡ Agent Capabilities:
• Dynamic SQL Queries: Write & execute safe read-only SELECT queries over PostgreSQL.
• Visual Charting: Produce interactive Line, Bar, and Pie charts in real time.
• Pinned Dashboard: Save any chart output to your persistent dashboard.

💡 Recommended Example Prompts:
1. "Which 5 servers have the highest member counts?"
2. "Chart daily message volume for top channels in June 2026"
3. "Show me weekday vs weekend message activity as a bar chart"`
          }
        }
      ]
    }
  ]);

  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [hasShownTip, setHasShownTip] = useState(false);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Reset tip flag when enabled plugins configuration changes
  useEffect(() => {
    setHasShownTip(false);
  }, [enabledPlugins]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;

    const userMessageText = input.trim();
    setInput('');
    setIsStreaming(true);
    setTimeout(() => inputRef.current?.focus(), 50);

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `assistant_${Date.now()}`;

    setMessages(prev => [
      ...prev,
      { id: userMsgId, role: 'user', text: userMessageText },
      { id: assistantMsgId, role: 'assistant', stages: [] }
    ]);

    const activeList = enabledPlugins || ['query', 'chart', 'summary'];
    const pluginParam = activeList.length > 0 ? `&plugins=${encodeURIComponent(activeList.join(','))}` : '';
    const tipParam = `&show_tip=${!hasShownTip}`;
    
    // Mark tip as shown so subsequent messages won't repeat it
    setHasShownTip(true);

    const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(userMessageText)}${pluginParam}${tipParam}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.stage === 'prose' || data.stage === 'error') {
          setIsStreaming(false);
          setTimeout(() => inputRef.current?.focus(), 50);
        }
        setMessages(prev =>
          prev.map(msg => {
            if (msg.id === assistantMsgId) {
              return {
                ...msg,
                stages: [...msg.stages, data]
              };
            }
            return msg;
          })
        );
      } catch (err) {
        console.error("Error parsing SSE data:", err);
      }
    };

    eventSource.addEventListener('end', () => {
      eventSource.close();
      setIsStreaming(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    });

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      eventSource.close();
      setIsStreaming(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    };

  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message-bubble ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="user-text">{msg.text}</div>
            ) : (
              <div className="assistant-card">
                {msg.stages.map((st, idx) => (
                  <div key={idx} className="stage-block">
                    {st.stage === 'reasoning' && (
                      <div className="stage-badge stage-reasoning">
                        <Sparkles size={12} /> {st.payload.text}
                      </div>
                    )}

                    {st.stage === 'tool_call' && (
                      <div className="stage-badge stage-tool_call">
                        <Terminal size={12} /> Tool: {st.payload.tool}
                      </div>
                    )}

                    {st.stage === 'tool_progress' && (
                      <div className="stage-badge stage-tool_progress">
                        {st.payload.status}
                      </div>
                    )}

                    {st.stage === 'result' && st.payload.tool === 'query' && (
                      <div>
                        <div className="sql-codeblock">
                          <code>{st.payload.result.sql}</code>
                        </div>
                        <DataTable data={st.payload.result.data} count={st.payload.result.count} />
                      </div>
                    )}

                    {st.stage === 'result' && st.payload.tool === 'chart' && (
                      <div style={{ marginTop: '12px' }}>
                        <ChartRenderer
                          spec={st.payload.result}
                          onPin={onPinChart}
                          isPinned={pinnedCharts?.some(c => c.title === st.payload.result.title)}
                        />
                      </div>
                    )}

                    {st.stage === 'prose' && (
                      <div className="stage-prose">
                        {st.payload.text}
                      </div>
                    )}

                    {st.stage === 'error' && (
                      <div className="stage-badge stage-tool_call" style={{ color: '#ef4444' }}>
                        <AlertTriangle size={12} /> Error: {st.payload.message}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-bar">
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Ask a question about Discord server analytics..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={isStreaming}
          autoFocus
        />
        <button className="send-btn" onClick={handleSend} disabled={isStreaming || !input.trim()}>
          <Send size={16} /> Send
        </button>
      </div>
    </div>
  );
}
