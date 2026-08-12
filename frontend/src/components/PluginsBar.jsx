import React, { useState, useEffect } from 'react';
import { Sliders, Database, BarChart2, FileText, Check, Cpu } from 'lucide-react';

const PLUGIN_ICONS = {
  query: Database,
  chart: BarChart2,
  summary: FileText,
};

export default function PluginsBar({ onPluginsChange }) {
  const [availablePlugins, setAvailablePlugins] = useState(['query', 'chart', 'summary']);
  const [activePlugins, setActivePlugins] = useState(['query', 'chart', 'summary']);
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => {
        if (data.plugins && Array.isArray(data.plugins)) {
          setAvailablePlugins(data.plugins);
          setActivePlugins(data.plugins);
        }
      })
      .catch(() => {});
  }, []);

  const togglePlugin = (name) => {
    setActivePlugins(prev => {
      const next = prev.includes(name)
        ? prev.filter(p => p !== name)
        : [...prev, name];
      onPluginsChange(next);
      return next;
    });
  };

  const selectAll = () => {
    setActivePlugins(availablePlugins);
    onPluginsChange(availablePlugins);
  };

  const clearAll = () => {
    setActivePlugins([]);
    onPluginsChange([]);
  };

  return (
    <div className="plugins-bar-container">
      <div className="plugins-bar-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="plugins-title">
          <Sliders size={16} className="title-icon" />
          <span>Active Agent Plugins ({activePlugins.length}/{availablePlugins.length})</span>
        </div>
        <div className="plugins-bar-controls">
          <button className="text-action-btn" onClick={(e) => { e.stopPropagation(); selectAll(); }}>Select All</button>
          <button className="text-action-btn" onClick={(e) => { e.stopPropagation(); clearAll(); }}>Clear</button>
        </div>
      </div>

      {isOpen && (
        <div className="plugins-chips-grid">
          {availablePlugins.map(name => {
            const Icon = PLUGIN_ICONS[name] || Cpu;
            const isSelected = activePlugins.includes(name);

            return (
              <button
                key={name}
                className={`plugin-chip ${isSelected ? 'selected' : ''}`}
                onClick={() => togglePlugin(name)}
              >
                <Icon size={14} />
                <span className="chip-label">{name}</span>
                {isSelected && <Check size={12} className="check-icon" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
