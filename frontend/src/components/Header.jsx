import React, { useEffect, useState } from 'react';
import { Bot, LayoutDashboard, MessageSquare } from 'lucide-react';

export default function Header({ activeTab, setActiveTab }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const checkHealth = () => {
      fetch('/health')
        .then(res => res.json())
        .then(data => setHealth(data))
        .catch(() => setHealth({ status: 'degraded' }));
    };

    checkHealth();
    const interval = setInterval(checkHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="app-header">
      <div className="brand">
        <Bot className="brand-icon" size={26} />
        <span>Exaqube Analytics</span>
      </div>

      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={16} /> Agent Chat
        </button>
        <button
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={16} /> Pinned Dashboard
        </button>
      </nav>

      <div className="health-badge">
        <span className="pulse-dot" style={{ backgroundColor: health?.status === 'ok' ? '#10b981' : '#f59e0b', boxShadow: health?.status === 'ok' ? '0 0 8px #10b981' : '0 0 8px #f59e0b' }} />
        <span>{health?.status === 'ok' ? `Healthy (${health.plugins_count} plugins)` : 'Connecting...'}</span>
      </div>
    </header>
  );
}
