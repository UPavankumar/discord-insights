import React from 'react';
import { Trash2, BarChart2 } from 'lucide-react';
import ChartRenderer from './ChartRenderer';

export default function Dashboard({ pinnedCharts, onUnpin }) {
  if (!pinnedCharts || pinnedCharts.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#6b7280', gap: '12px' }}>
        <BarChart2 size={48} strokeWidth={1.5} />
        <p style={{ fontSize: '1rem' }}>No pinned charts yet.</p>
        <p style={{ fontSize: '0.85rem' }}>Ask the agent for a chart in the chat and click "Pin to Dashboard".</p>
      </div>
    );
  }

  return (
    <div className="dashboard-grid">
      {pinnedCharts.map((spec, idx) => (
        <div key={idx} className="pinned-card">
          <div className="pinned-header">
            <span className="pinned-title">{spec.title}</span>
            <button className="unpin-btn" onClick={() => onUnpin(idx)}>
              <Trash2 size={16} />
            </button>
          </div>
          <ChartRenderer spec={spec} />
        </div>
      ))}
    </div>
  );
}
