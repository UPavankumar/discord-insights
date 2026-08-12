import React from 'react';

export default function DataTable({ data, count }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '12px', color: '#6b7280', fontSize: '0.85rem' }}>No data returned.</div>;
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="data-table-container">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx}>
              {columns.map(col => (
                <td key={col}>{String(row[col] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {count && <div style={{ padding: '8px 12px', fontSize: '0.75rem', color: '#6b7280', backgroundColor: '#1f2937', textAlign: 'right' }}>Total rows: {count}</div>}
    </div>
  );
}
