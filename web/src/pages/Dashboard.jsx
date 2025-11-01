import { useEffect, useMemo, useState } from "react";
import KPI from "../components/KPI.jsx";
import TimeRangePicker from "../components/TimeRangePicker.jsx";
import ServicePicker from "../components/ServicePicker.jsx";
import MetricChart from "../components/MetricChart.jsx";
import AlertList from "../components/AlertList.jsx";
import {
  fetchAlerts,
  fetchConfig,
  fetchKpis,
  fetchMetrics
} from "../api/client.js";

export default function Dashboard() {
  const [services, setServices] = useState([]);
  const [service, setService] = useState("");
  const [range, setRange] = useState("1h");
  const [kpis, setKpis] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState({ loading: true, error: null });

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const cfg = await fetchConfig();
        setServices(cfg.services || []);
        if (!service && (cfg.services || []).length) {
          setService(cfg.services[0]);
        }
      } catch (error) {
        setStatus({ loading: false, error: "Failed to load config" });
      }
    };
    loadConfig();
  }, []);

  useEffect(() => {
    const loadData = async () => {
      if (!service) {
        setStatus({ loading: false, error: null });
        return;
      }
      setStatus({ loading: true, error: null });
      try {
        const [kpiData, metricSeries, alertData] = await Promise.all([
          fetchKpis({ service, range }),
          fetchMetrics({ service, range }),
          fetchAlerts({ limit: 10 })
        ]);
        setKpis(kpiData.latest);
        setMetrics([
          {
            label: "Error Rate",
            color: "#ef4444",
            values: metricSeries.map((point) => ({
              ts: point.ts,
              value: point.error_rate
            }))
          },
          {
            label: "p95 Latency (ms)",
            color: "#6366f1",
            values: metricSeries.map((point) => ({
              ts: point.ts,
              value: point.p95_latency_ms
            }))
          },
          {
            label: "Throughput (TPS)",
            color: "#10b981",
            values: metricSeries.map((point) => ({
              ts: point.ts,
              value: point.tps
            }))
          }
        ]);
        setAlerts(alertData);
        setStatus({ loading: false, error: null });
      } catch (error) {
        setStatus({ loading: false, error: "Failed to load dashboard data" });
      }
    };
    loadData();
  }, [service, range]);

  const kpiCards = useMemo(() => {
    if (!kpis) {
      return [];
    }
    return [
      {
        label: "Error Rate",
        value: `${(kpis.error_rate * 100).toFixed(2)}%`
      },
      {
        label: "p95 Latency",
        value: kpis.p95_latency_ms,
        unit: "ms"
      },
      {
        label: "Throughput",
        value: kpis.tps.toFixed(2),
        unit: "req/s"
      }
    ];
  }, [kpis]);

  return (
    <section className="view">
      <div className="controls">
        <ServicePicker services={services} value={service} onChange={setService} />
        <TimeRangePicker value={range} onChange={setRange} />
      </div>

      {status.error && <div className="card error">{status.error}</div>}
      {status.loading && <div className="card muted">Loading dashboard…</div>}

      {!status.loading && !status.error && (
        <>
          <div className="kpi-grid">
            {kpiCards.map((kpi) => (
              <KPI key={kpi.label} {...kpi} />
            ))}
          </div>

          <div className="chart-grid">
            {metrics.map((metric) => (
              <MetricChart
                key={metric.label}
                data={metric.values}
                label={metric.label}
                color={metric.color}
              />
            ))}
          </div>

          <AlertList alerts={alerts} />
        </>
      )}
    </section>
  );
}
