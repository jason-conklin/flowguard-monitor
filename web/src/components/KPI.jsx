export default function KPI({ label, value, unit, trend }) {
  return (
    <div className="kpi-card">
      <h3>{label}</h3>
      <div className="kpi-value">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {typeof trend === "number" && (
        <span className={`kpi-trend ${trend >= 0 ? "up" : "down"}`}>
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(2)}%
        </span>
      )}
    </div>
  );
}

