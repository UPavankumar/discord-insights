import React, { useState, useEffect } from 'react';
import { Sliders, Database, BarChart2, FileText, Check, Cpu, CheckSquare, Square } from 'lucide-react';

const PLUGIN_ICONS = {
  query: Database,
  chart: BarChart2,
  summary: FileText,
};

const PLUGIN_DESCRIPTIONS = {
  query: 'Execute read-only SQL queries over PostgreSQL database.',
  chart: 'Format result sets into interactive visual line, bar, and pie charts.',
  summary: 'Generate structured executive summaries and key insights.',
};

export default function SidebarPlugins({ onApplyPlugins }) {
  const [availablePlugins, setAvailablePlugins] = useState(['query', 'chart', 'summary']);
  const [selectedPlugins, setSelectedPlugins] = useState(['query', 'chart', 'summary']);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => {
        if (data.plugins && Array.isArray(data.plugins)) {
          setAvailablePlugins(data.plugins);
          setSelectedPlugins(data.plugins);
        }
      })
      .catch(() => {});
  }, []);

  const togglePlugin = (name) => {
    setSelectedPlugins(prev =>
      prev.includes(name)
        ? prev.filter(p => p !== name)
        : [...prev, name]
    );
    setIsSaved(false);
  };

  const selectAll = () => {
    setSelectedPlugins(availablePlugins);
    setIsSaved(false);
  };

  const clearAll = () => {
    setSelectedPlugins([]);
    setIsSaved(false);
  };

  const handleApply = () => {
    const toApply = selectedPlugins.length > 0 ? selectedPlugins : availablePlugins;
    onApplyPlugins(toApply);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  return (
    <aside className="sidebar-plugins">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <Sliders size={18} className="sidebar-title-icon" />
          <span>Plugin Manager</span>
        </div>
        <div className="sidebar-actions">
          <button className="text-link-btn" onClick={selectAll}>All</button>
          <button className="text-link-btn" onClick={clearAll}>Reset</button>
        </div>
      </div>

      <div className="sidebar-plugin-list">
        {availablePlugins.map(name => {
          const Icon = PLUGIN_ICONS[name] || Cpu;
          const isChecked = selectedPlugins.includes(name);
          const desc = PLUGIN_DESCRIPTIONS[name] || 'Custom registered agent plugin.';

          return (
            <div
              key={name}
              className={`sidebar-plugin-card ${isChecked ? 'active' : ''}`}
              onClick={() => togglePlugin(name)}
            >
              <div className="card-top">
                <div className="card-info">
                  <Icon size={16} className="plugin-card-icon" />
                  <span className="plugin-card-name">{name}</span>
                </div>
                {isChecked ? (
                  <CheckSquare size={16} className="check-box-active" />
                ) : (
                  <Square size={16} className="check-box-empty" />
                )}
              </div>
              <p className="plugin-card-desc">{desc}</p>
            </div>
          );
        })}
      </div>

      <div className="sidebar-footer">
        <button
          className={`apply-plugins-btn ${isSaved ? 'applied' : ''}`}
          onClick={handleApply}
        >
          {isSaved ? (
            <>
              <Check size={16} /> Plugins Applied!
            </>
          ) : (
            `Apply Plugins (${selectedPlugins.length}/${availablePlugins.length})`
          )}
        </button>
      </div>
    </aside>
  );
}
