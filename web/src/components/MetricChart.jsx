import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip
} from "chart.js";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Legend, Tooltip);

export default function MetricChart({ data, label, color }) {
  const chartData = {
    labels: data.map((point) => new Date(point.ts).toLocaleTimeString()),
    datasets: [
      {
        label,
        data: data.map((point) => point.value),
        borderColor: color,
        backgroundColor: color + "33",
        tension: 0.3,
        fill: true,
        pointRadius: 0
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: { maxRotation: 0, autoSkip: true }
      },
      y: {
        beginAtZero: true
      }
    }
  };

  return (
    <div className="chart-card">
      <Line data={chartData} options={options} />
    </div>
  );
}

