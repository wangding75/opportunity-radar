import React from 'react';

// ----------------------------------------------------
// Smooth Line Chart
// ----------------------------------------------------
interface LineChartProps {
  data: Array<{ label: string; total: number; abnormal?: number }>;
  height?: number;
}

export const LineChart: React.FC<LineChartProps> = ({ data, height = 180 }) => {
  const width = 460;
  const paddingLeft = 36;
  const paddingRight = 16;
  const paddingTop = 20;
  const paddingBottom = 28;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const maxVal = 800;

  const getX = (index: number) => paddingLeft + (index / (data.length - 1)) * chartWidth;
  const getY = (val: number) => paddingTop + chartHeight - (val / maxVal) * chartHeight;

  // Build SVG path
  const totalPoints = data.map((d, i) => `${getX(i)},${getY(d.total)}`).join(' ');
  const abnormalPoints = data.map((d, i) => `${getX(i)},${getY(d.abnormal || 0)}`).join(' ');

  const totalArea = `${getX(0)},${paddingTop + chartHeight} ${totalPoints} ${getX(data.length - 1)},${paddingTop + chartHeight}`;

  return (
    <div style={{ width: '100%', overflow: 'hidden' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
        {/* Y Axis Grid lines */}
        {[0, 200, 400, 600, 800].map((val) => {
          const y = getY(val);
          return (
            <g key={val}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="var(--border-subtle)"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
              <text
                x={paddingLeft - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="var(--text-muted)"
              >
                {val}
              </text>
            </g>
          );
        })}

        {/* Area fill for Total */}
        <polygon points={totalArea} fill="rgba(37, 99, 235, 0.08)" />

        {/* Total line */}
        <polyline
          points={totalPoints}
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Total points */}
        {data.map((d, i) => (
          <circle
            key={i}
            cx={getX(i)}
            cy={getY(d.total)}
            r="3.5"
            fill="var(--color-primary)"
            stroke="#ffffff"
            strokeWidth="1.5"
          />
        ))}

        {/* Abnormal line */}
        {data[0].abnormal !== undefined && (
          <>
            <polyline
              points={abnormalPoints}
              fill="none"
              stroke="var(--color-danger)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {data.map((d, i) => (
              <circle
                key={i}
                cx={getX(i)}
                cy={getY(d.abnormal || 0)}
                r="3"
                fill="var(--color-danger)"
                stroke="#ffffff"
                strokeWidth="1.5"
              />
            ))}
          </>
        )}

        {/* X Axis labels */}
        {data.map((d, i) => (
          <text
            key={i}
            x={getX(i)}
            y={height - 8}
            textAnchor="middle"
            fontSize="12"
            fill="var(--text-muted)"
          >
            {d.label}
          </text>
        ))}
      </svg>
    </div>
  );
};

// ----------------------------------------------------
// Donut / Ring Chart
// ----------------------------------------------------
interface DonutChartProps {
  total: number;
  totalLabel?: string;
  segments: Array<{ label: string; count: number; percentage: string; color: string }>;
  size?: number;
}

export const DonutChart: React.FC<DonutChartProps> = ({
  total,
  totalLabel = '总计划数',
  segments,
  size = 140,
}) => {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const strokeWidth = 14;

  let currentOffset = 0;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg viewBox="0 0 140 140" style={{ width: size, height: size, transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth={strokeWidth}
          />
          {segments.map((seg, i) => {
            const segRatio = total > 0 ? seg.count / total : 0;
            const strokeDasharray = `${segRatio * circumference} ${circumference}`;
            const strokeDashoffset = -currentOffset;
            currentOffset += segRatio * circumference;

            return (
              <circle
                key={i}
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke={seg.color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            );
          })}
        </svg>

        {/* Center label */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
          }}
        >
          <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--text-primary)' }}>
            {total}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{totalLabel}</span>
        </div>
      </div>

      {/* Legend list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
        {segments.map((seg, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: seg.color }} />
              <span style={{ color: 'var(--text-secondary)' }}>{seg.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 500 }}>
              <span style={{ color: 'var(--text-primary)' }}>{seg.count}</span>
              <span style={{ color: 'var(--text-muted)' }}>({seg.percentage})</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ----------------------------------------------------
// Mini Sparkline
// ----------------------------------------------------
export const Sparkline: React.FC<{ points?: number[]; color?: string; width?: number; height?: number }> = ({
  points = [20, 25, 30, 28, 45, 40, 55, 65],
  color = '#2563eb',
  width = 64,
  height = 20,
}) => {
  const min = Math.min(...points);
  const max = Math.max(...points) || 1;
  const range = max - min || 1;

  const svgPoints = points
    .map((p, i) => {
      const x = (i / (points.length - 1)) * width;
      const y = height - ((p - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} style={{ display: 'inline-block', verticalAlign: 'middle' }}>
      <polyline
        points={svgPoints}
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
