import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import SidebarPlugins from './components/SidebarPlugins';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [activePlugins, setActivePlugins] = useState(['query', 'chart', 'summary']);
  const [pinnedCharts, setPinnedCharts] = useState(() => {
    const saved = localStorage.getItem('exaqube_pinned_charts');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('exaqube_pinned_charts', JSON.stringify(pinnedCharts));
  }, [pinnedCharts]);

  const handlePinChart = (chartSpec) => {
    setPinnedCharts(prev => {
      if (prev.some(c => c.title === chartSpec.title)) {
        return prev.filter(c => c.title !== chartSpec.title);
      }
      return [...prev, chartSpec];
    });
  };

  const handleUnpin = (index) => {
    setPinnedCharts(prev => prev.filter((_, idx) => idx !== index));
  };

  return (
    <div className="app-container">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="workspace-layout">
        <SidebarPlugins onApplyPlugins={setActivePlugins} />
        <main className="workspace-content">
          {activeTab === 'chat' ? (
            <ChatInterface
              onPinChart={handlePinChart}
              pinnedCharts={pinnedCharts}
              enabledPlugins={activePlugins}
            />
          ) : (
            <Dashboard pinnedCharts={pinnedCharts} onUnpin={handleUnpin} />
          )}
        </main>
      </div>
    </div>
  );
}
