import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { Pin } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const PALETTE = [
  '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#6366f1'
];

export default function ChartRenderer({ spec, onPin, isPinned }) {
  if (!spec || !spec.data || spec.data.length === 0) {
    return <div style={{ padding: '16px', color: '#9ca3af', fontStyle: 'italic' }}>No chart data available.</div>;
  }

  const chartType = String(spec.type || 'bar').toLowerCase();
  const isLine = chartType.includes('line');
  const isPie = chartType.includes('pie') || chartType.includes('donut');
  const isBar = !isLine && !isPie;

  const xKey = spec.x_key && spec.data[0]?.[spec.x_key] !== undefined ? spec.x_key : Object.keys(spec.data[0])[0];
  const yKeys = spec.y_keys && spec.y_keys.length > 0 ? spec.y_keys : [Object.keys(spec.data[0])[1] || Object.keys(spec.data[0])[0]];

  const labels = spec.data.map((row, idx) => String(row[xKey] ?? `Item ${idx + 1}`));

  const datasets = yKeys.map((yKey, idx) => ({
    label: yKey,
    data: spec.data.map(row => {
      const val = Number(row[yKey]);
      return isNaN(val) ? 0 : val;
    }),
    backgroundColor: isPie ? PALETTE : PALETTE[idx % PALETTE.length],

    borderColor: isPie ? '#111827' : PALETTE[idx % PALETTE.length],
    borderWidth: 2,
    tension: 0.3,
  }));

  const chartData = { labels, datasets };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#9ca3af' },
      },
      title: {
        display: !!spec.title,
        text: spec.title || 'Analytics Chart',
        color: '#f3f4f6',
        font: { size: 14, weight: '600' },
      },
    },
    scales: !isPie ? {
      x: { ticks: { color: '#9ca3af' }, grid: { color: '#1e293b' } },
      y: { ticks: { color: '#9ca3af' }, grid: { color: '#1e293b' } },
    } : undefined,
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '340px', backgroundColor: '#111827', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b', marginTop: '12px' }}>
      {onPin && (
        <button
          onClick={() => onPin(spec)}
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            zIndex: 10,
            background: isPinned ? '#3b82f6' : '#1f2937',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '6px 10px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.75rem',
          }}
        >
          <Pin size={14} />
          {isPinned ? 'Pinned' : 'Pin to Dashboard'}
        </button>
      )}

      {isLine && <Line data={chartData} options={options} />}
      {isBar && <Bar data={chartData} options={options} />}
      {isPie && <Pie data={chartData} options={options} />}
    </div>
  );
}
