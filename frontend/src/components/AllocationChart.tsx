import { useEffect, useRef } from 'react';
import { Chart, DoughnutController, ArcElement, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
Chart.register(DoughnutController, ArcElement, Tooltip, Legend);

interface AllocationData {
  labels: string[];
  values: number[];
  colors?: string[];
}

interface AllocationChartProps {
  data: AllocationData;
  title?: string;
}

const DEFAULT_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#14B8A6', // teal
  '#F97316', // orange
  '#6366F1', // indigo
  '#84CC16', // lime
];

export default function AllocationChart({ data, title = 'Portfolio Allocation' }: AllocationChartProps) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current || !data.labels.length) return;

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const colors = data.colors || DEFAULT_COLORS.slice(0, data.labels.length);

    chartInstance.current = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [
          {
            data: data.values,
            backgroundColor: colors,
            borderColor: colors.map(() => '#ffffff'),
            borderWidth: 2,
            hoverOffset: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${context.label}: ${percentage}%`;
              },
            },
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  const total = data.values.reduce((a, b) => a + b, 0);
  const colors = data.colors || DEFAULT_COLORS.slice(0, data.labels.length);

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      
      <div className="flex items-center gap-8">
        {/* Chart */}
        <div className="relative w-48 h-48">
          <canvas ref={chartRef}></canvas>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{data.labels.length}</p>
              <p className="text-sm text-gray-500">Holdings</p>
            </div>
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex-1 space-y-2 max-h-48 overflow-y-auto">
          {data.labels.map((label, index) => {
            const percentage = ((data.values[index] / total) * 100).toFixed(1);
            return (
              <div key={label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: colors[index] }}
                  ></div>
                  <span className="text-sm text-gray-600">{label}</span>
                </div>
                <span className="text-sm font-medium text-gray-800">{percentage}%</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
